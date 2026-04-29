from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, AsyncIterator

import httpx

from app.config import REPLICATE_API_BASE, REPLICATE_API_TOKEN

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dynamic model listing
# ---------------------------------------------------------------------------

# Collections to fetch; Replicate paginates — we follow next_cursor links
_COLLECTIONS = ["language-models", "instruct-tuned-llms"]

# Simple in-process cache: (timestamp, list_of_model_dicts)
_models_cache: tuple[float, list[dict]] | None = None
_CACHE_TTL = 300  # seconds


def _detect_prompt_format(owner: str, name: str) -> str:
    slug = f"{owner}/{name}".lower()
    if "mistral" in slug or "mixtral" in slug:
        return "mistral"
    return "llama3"


async def fetch_replicate_models() -> list[dict]:
    """
    Return a list of dicts with keys: id, owner, name, description, prompt_format.
    Results are cached for _CACHE_TTL seconds to avoid hammering the API.
    """
    global _models_cache
    now = time.monotonic()
    if _models_cache and (now - _models_cache[0]) < _CACHE_TTL:
        return _models_cache[1]

    if not REPLICATE_API_TOKEN:
        return []

    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    seen: set[str] = set()
    results: list[dict] = []

    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
        for collection_slug in _COLLECTIONS:
            url: str | None = f"{REPLICATE_API_BASE}/collections/{collection_slug}"
            while url:
                try:
                    resp = await client.get(url, headers=headers)
                    if resp.status_code != 200:
                        logger.warning("Could not fetch collection %s: %s", collection_slug, resp.status_code)
                        break
                    data = resp.json()
                except Exception as exc:
                    logger.warning("Error fetching collection %s: %s", collection_slug, exc)
                    break

                for m in data.get("models", []) or []:
                    owner = m.get("owner", "")
                    name = m.get("name", "")
                    model_id = f"{owner}/{name}"
                    if model_id in seen:
                        continue
                    seen.add(model_id)
                    results.append({
                        "id": model_id,
                        "owner": owner,
                        "name": name,
                        "description": m.get("description", ""),
                        "prompt_format": _detect_prompt_format(owner, name),
                        "run_count": m.get("run_count", 0),
                    })

                url = data.get("next")  # follow pagination

    results.sort(key=lambda m: m.get("run_count", 0), reverse=True)
    _models_cache = (now, results)
    return results

# Maximum time to wait for a prediction to complete (seconds)
POLL_TIMEOUT = 300
POLL_INTERVAL = 0.75  # seconds between status polls

# Maximum time to wait for the stream URL to become available
STREAM_URL_TIMEOUT = 60


def _auth_headers() -> dict[str, str]:
    if not REPLICATE_API_TOKEN:
        raise ValueError("REPLICATE_API_TOKEN is not set")
    return {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }


async def _create_prediction(
    client: httpx.AsyncClient,
    model_version: str,
    input_dict: dict[str, Any],
    stream: bool = False,
) -> dict[str, Any]:
    """
    POST to Replicate's predictions endpoint.

    Replicate supports two addressing styles:
      - Versioned:   {"version": "<sha>", "input": {...}}
      - Model-level: POST /v1/models/{owner}/{name}/predictions  (no version key)

    We use the model-level endpoint when model_version looks like "owner/name"
    (no colon), and the versioned endpoint when it's "owner/name:version".
    """
    payload: dict[str, Any] = {"input": input_dict}
    if stream:
        payload["stream"] = True

    if ":" in model_version:
        # Versioned deployment
        payload["version"] = model_version
        url = f"{REPLICATE_API_BASE}/predictions"
    else:
        # Model-level deployment (uses the model's default version)
        url = f"{REPLICATE_API_BASE}/models/{model_version}/predictions"

    response = await client.post(url, json=payload, headers=_auth_headers())

    if response.status_code == 401:
        raise PermissionError("Invalid or missing REPLICATE_API_TOKEN")

    if response.status_code not in (200, 201):
        detail = response.text
        raise RuntimeError(
            f"Replicate prediction creation failed [{response.status_code}]: {detail}"
        )

    return response.json()


async def _poll_prediction(
    client: httpx.AsyncClient,
    prediction_id: str,
) -> dict[str, Any]:
    """Poll a prediction until it reaches a terminal state."""
    url = f"{REPLICATE_API_BASE}/predictions/{prediction_id}"
    elapsed = 0.0

    while elapsed < POLL_TIMEOUT:
        await asyncio.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL

        resp = await client.get(url, headers=_auth_headers())
        if resp.status_code != 200:
            raise RuntimeError(
                f"Replicate poll failed [{resp.status_code}]: {resp.text}"
            )

        data = resp.json()
        status = data.get("status")

        if status == "succeeded":
            return data
        if status in ("failed", "canceled"):
            error_msg = data.get("error") or "Prediction failed with no error message"
            raise RuntimeError(f"Replicate prediction {status}: {error_msg}")

        # Still processing — continue polling
        logger.debug("Prediction %s status: %s (elapsed %.1fs)", prediction_id, status, elapsed)

    raise TimeoutError(f"Replicate prediction timed out after {POLL_TIMEOUT}s")


async def run_prediction(
    model_version: str,
    input_dict: dict[str, Any],
    stream: bool = False,
) -> str:
    """
    Run a Replicate prediction and return the full text output.

    For non-streaming predictions the output may be a list of strings or a
    single string; we always join and return a plain str.
    """
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, read=300.0)) as client:
        prediction = await _create_prediction(client, model_version, input_dict, stream=False)
        prediction_id = prediction["id"]
        logger.info("Created prediction %s for model %s", prediction_id, model_version)

        result = await _poll_prediction(client, prediction_id)
        output = result.get("output")

        if output is None:
            return ""
        if isinstance(output, list):
            return "".join(str(token) for token in output)
        return str(output)


async def stream_prediction(
    model_version: str,
    input_dict: dict[str, Any],
) -> AsyncIterator[str]:
    """
    Run a Replicate prediction in streaming mode.

    Yields individual text tokens as they arrive via Server-Sent Events.
    The caller is responsible for wrapping each token in the OpenAI chunk format.
    """
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, read=300.0)) as client:
        prediction = await _create_prediction(client, model_version, input_dict, stream=True)
        prediction_id = prediction["id"]
        logger.info("Created streaming prediction %s for model %s", prediction_id, model_version)

        # Wait for Replicate to provide the stream URL
        stream_url = prediction.get("urls", {}).get("stream")
        if not stream_url:
            stream_url = await _wait_for_stream_url(client, prediction_id)

        # Stream SSE tokens
        async for token in _read_sse_stream(client, stream_url):
            yield token


async def _wait_for_stream_url(
    client: httpx.AsyncClient,
    prediction_id: str,
) -> str:
    """Poll the prediction until the stream URL is available."""
    url = f"{REPLICATE_API_BASE}/predictions/{prediction_id}"
    elapsed = 0.0

    while elapsed < STREAM_URL_TIMEOUT:
        await asyncio.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL

        resp = await client.get(url, headers=_auth_headers())
        if resp.status_code != 200:
            raise RuntimeError(f"Replicate poll failed [{resp.status_code}]: {resp.text}")

        data = resp.json()
        status = data.get("status")

        if status in ("failed", "canceled"):
            error_msg = data.get("error") or "Prediction failed"
            raise RuntimeError(f"Replicate prediction {status}: {error_msg}")

        stream_url = data.get("urls", {}).get("stream")
        if stream_url:
            return stream_url

    raise TimeoutError("Stream URL did not become available in time")


async def _read_sse_stream(
    client: httpx.AsyncClient,
    stream_url: str,
) -> AsyncIterator[str]:
    """
    Read a Replicate SSE stream and yield token strings.

    Replicate's SSE format:
        event: output
        data: <token>

        event: done
        data: {}
    """
    headers = {**_auth_headers(), "Accept": "text/event-stream"}

    async with client.stream("GET", stream_url, headers=headers, timeout=None) as response:
        if response.status_code != 200:
            body = await response.aread()
            raise RuntimeError(
                f"Replicate stream endpoint returned [{response.status_code}]: {body.decode()}"
            )

        event_type: str = ""
        async for raw_line in response.aiter_lines():
            line = raw_line.strip()

            if line.startswith("event:"):
                event_type = line[len("event:"):].strip()
            elif line.startswith("data:"):
                data = line[len("data:"):].strip()

                if event_type == "done" or data in ("{}", ""):
                    # End of stream
                    return

                if event_type == "output":
                    yield data
                # Ignore other event types (e.g. "error", "logs")

            elif line == "":
                # Blank line resets the event type for the next event
                event_type = ""


# ---------------------------------------------------------------------------
# Image generation
# ---------------------------------------------------------------------------

async def run_image_prediction(
    model_version: str,
    input_dict: dict[str, Any],
) -> list[str]:
    """
    Run a Replicate image generation prediction and return a list of output URLs.

    Image models return either a single URL string or a list of URL strings.
    """
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=300.0)) as client:
        prediction = await _create_prediction(client, model_version, input_dict, stream=False)
        prediction_id = prediction["id"]
        logger.info("Created image prediction %s for model %s", prediction_id, model_version)

        result = await _poll_prediction(client, prediction_id)
        output = result.get("output")

        if output is None:
            return []
        if isinstance(output, list):
            return [str(u) for u in output]
        return [str(output)]
