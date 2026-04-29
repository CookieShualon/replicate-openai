from __future__ import annotations

import json
import logging
import time
import uuid
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

import base64

import httpx

from app.config import DEFAULT_MODEL, MODEL_MAP
from app.image_models import IMAGE_MODEL_MAP, DEFAULT_IMAGE_MODEL, build_image_input
from app.models import (
    ChatCompletionRequest,
    CompletionRequest,
    CompletionResponse,
    CompletionChoice,
    ErrorDetail,
    ErrorResponse,
    ImageData,
    ImageGenerationRequest,
    ImageGenerationResponse,
    Message,
    Model,
    ModelList,
    Usage,
)
from app.replicate_client import fetch_replicate_models, run_image_prediction, run_prediction, stream_prediction
from app.translator import (
    count_tokens,
    messages_to_prompt,
    opening_chunk,
    replicate_output_to_openai,
    stream_chunk,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_model(requested_model: str) -> tuple[str, str, str]:
    """
    Resolve an incoming model name to its Replicate counterpart.

    Lookup order:
      1. Exact match in MODEL_MAP (hardcoded aliases)
      2. Case-insensitive match in MODEL_MAP
      3. Treat the name as a raw "owner/name" Replicate model ID
      4. Fall back to DEFAULT_MODEL

    Returns:
        (canonical_name, replicate_model_id, prompt_format)
    """
    name = requested_model or DEFAULT_MODEL

    if name in MODEL_MAP:
        replicate_id, prompt_format = MODEL_MAP[name]
        return name, replicate_id, prompt_format

    # Case-insensitive alias match
    lower = name.lower()
    for key in MODEL_MAP:
        if key.lower() == lower:
            replicate_id, prompt_format = MODEL_MAP[key]
            return key, replicate_id, prompt_format

    # Treat as a raw Replicate "owner/name" or "owner/name:version" ID
    if "/" in name:
        owner = name.split("/")[0]
        model_name = name.split("/")[1].split(":")[0]
        from app.replicate_client import _detect_prompt_format
        return name, name, _detect_prompt_format(owner, model_name)

    logger.warning("Unknown model '%s', falling back to %s", name, DEFAULT_MODEL)
    replicate_id, prompt_format = MODEL_MAP[DEFAULT_MODEL]
    return DEFAULT_MODEL, replicate_id, prompt_format


def _build_replicate_input(
    request: ChatCompletionRequest,
    prompt: str,
    system_prompt: str,
) -> dict:
    """Build the input dict for the Replicate prediction."""
    inp: dict = {
        "prompt": prompt,
        "max_tokens": request.max_tokens or 512,
        "temperature": request.temperature if request.temperature is not None else 0.7,
        "top_p": request.top_p if request.top_p is not None else 0.9,
    }
    if system_prompt:
        inp["system_prompt"] = system_prompt
    if request.stop:
        inp["stop_sequences"] = (
            request.stop if isinstance(request.stop, str) else ",".join(request.stop)
        )
    return inp


def _openai_error(message: str, error_type: str, code: str, status_code: int) -> JSONResponse:
    body = ErrorResponse(error=ErrorDetail(message=message, type=error_type, code=code))
    return JSONResponse(status_code=status_code, content=body.model_dump())


# ---------------------------------------------------------------------------
# Model endpoints
# ---------------------------------------------------------------------------

@router.get("/models", response_model=ModelList)
async def list_models() -> ModelList:
    """Return all available models: hardcoded aliases + live models from Replicate collections."""
    seen: set[str] = set()
    models: list[Model] = []
    now = int(time.time())

    # Hardcoded chat aliases
    for name in MODEL_MAP:
        seen.add(name)
        models.append(Model(id=name, object="model", created=now, owned_by="replicate"))

    # Hardcoded image aliases
    for name in IMAGE_MODEL_MAP:
        seen.add(name)
        models.append(Model(id=name, object="model", created=now, owned_by="replicate"))

    # Live models from Replicate collections
    try:
        live = await fetch_replicate_models()
        for m in live:
            model_id = m["id"]
            if model_id not in seen:
                seen.add(model_id)
                models.append(Model(id=model_id, object="model", created=now, owned_by=m["owner"]))
    except Exception as exc:
        logger.warning("Could not fetch live models from Replicate: %s", exc)

    return ModelList(object="list", data=models)


@router.get("/models/{model_id:path}", response_model=Model)
async def get_model(model_id: str) -> Model:
    """Return info for a single model (alias or raw owner/name ID)."""
    now = int(time.time())
    if model_id in MODEL_MAP:
        return Model(id=model_id, object="model", created=now, owned_by="replicate")
    if model_id in IMAGE_MODEL_MAP:
        return Model(id=model_id, object="model", created=now, owned_by="replicate")
    if "/" in model_id:
        owner = model_id.split("/")[0]
        return Model(id=model_id, object="model", created=now, owned_by=owner)
    raise HTTPException(
        status_code=404,
        detail=f"Model '{model_id}' not found. Use GET /v1/models to see available models.",
    )


# ---------------------------------------------------------------------------
# Chat completions
# ---------------------------------------------------------------------------

@router.post("/chat/completions", response_model=None)
async def chat_completions(request: ChatCompletionRequest) -> JSONResponse | StreamingResponse:
    """
    OpenAI-compatible chat completions endpoint.

    Supports both streaming (stream=true) and non-streaming responses.
    """
    canonical_name, replicate_id, prompt_format = _resolve_model(request.model)

    try:
        prompt, system_prompt = messages_to_prompt(request.messages, prompt_format)
    except Exception as exc:
        return _openai_error(
            message=f"Failed to format messages: {exc}",
            error_type="invalid_request_error",
            code="invalid_messages",
            status_code=422,
        )

    replicate_input = _build_replicate_input(request, prompt, system_prompt)
    prompt_tokens = count_tokens(prompt)

    if request.stream:
        return StreamingResponse(
            _stream_chat_response(replicate_id, replicate_input, canonical_name, prompt_tokens),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    # Non-streaming
    try:
        output = await run_prediction(replicate_id, replicate_input, stream=False)
    except PermissionError as exc:
        return _openai_error(str(exc), "authentication_error", "invalid_api_key", 401)
    except TimeoutError as exc:
        return _openai_error(str(exc), "server_error", "timeout", 504)
    except RuntimeError as exc:
        return _openai_error(str(exc), "server_error", "replicate_error", 500)

    completion_tokens = count_tokens(output)
    response = replicate_output_to_openai(output, canonical_name, prompt_tokens, completion_tokens)
    return JSONResponse(content=response.model_dump())


async def _stream_chat_response(
    replicate_id: str,
    replicate_input: dict,
    model_name: str,
    prompt_tokens: int,
) -> AsyncIterator[str]:
    """Generator that yields SSE-formatted chat completion chunks."""
    chunk_id = f"chatcmpl-{uuid.uuid4().hex}"

    # Send opening chunk with role
    first = opening_chunk(model_name, chunk_id)
    yield f"data: {first.model_dump_json()}\n\n"

    try:
        async for token in stream_prediction(replicate_id, replicate_input):
            chunk = stream_chunk(token, model_name, chunk_id)
            yield f"data: {chunk.model_dump_json()}\n\n"
    except PermissionError as exc:
        error_chunk = _sse_error(str(exc), "authentication_error", "invalid_api_key")
        yield f"data: {error_chunk}\n\n"
        yield "data: [DONE]\n\n"
        return
    except (RuntimeError, TimeoutError) as exc:
        error_chunk = _sse_error(str(exc), "server_error", "replicate_error")
        yield f"data: {error_chunk}\n\n"
        yield "data: [DONE]\n\n"
        return

    # Final chunk with finish_reason
    final = stream_chunk("", model_name, chunk_id, finish_reason="stop")
    yield f"data: {final.model_dump_json()}\n\n"
    yield "data: [DONE]\n\n"
async def _stream_completion_response(
    replicate_id: str,
    replicate_input: dict,
    model_name: str,
) -> AsyncIterator[str]:
    """Generator that yields SSE-formatted legacy completion chunks."""
    chunk_id = f"cmpl-{uuid.uuid4().hex}"
    created = int(time.time())

    try:
        async for token in stream_prediction(replicate_id, replicate_input):
            chunk = {
                "id": chunk_id,
                "object": "text_completion",
                "created": created,
                "model": model_name,
                "choices": [
                    {
                        "text": token,
                        "index": 0,
                        "logprobs": None,
                        "finish_reason": None,
                    }
                ],
            }
            yield f"data: {json.dumps(chunk)}\n\n"
    except PermissionError as exc:
        error_chunk = _sse_error(str(exc), "authentication_error", "invalid_api_key")
        yield f"data: {error_chunk}\n\n"
        yield "data: [DONE]\n\n"
        return
    except (RuntimeError, TimeoutError) as exc:
        error_chunk = _sse_error(str(exc), "server_error", "replicate_error")
        yield f"data: {error_chunk}\n\n"
        yield "data: [DONE]\n\n"
        return

    final = {
        "id": chunk_id,
        "object": "text_completion",
        "created": created,
        "model": model_name,
        "choices": [
            {
                "text": "",
                "index": 0,
                "logprobs": None,
                "finish_reason": "stop",
            }
        ],
    }
    yield f"data: {json.dumps(final)}\n\n"
    yield "data: [DONE]\n\n"


def _sse_error(message: str, error_type: str, code: str) -> str:
    """Serialize an error as a JSON string suitable for embedding in an SSE data line."""
    return json.dumps({"error": {"message": message, "type": error_type, "code": code}})


# ---------------------------------------------------------------------------
# Legacy text completions
# ---------------------------------------------------------------------------

@router.post("/completions", response_model=None)
async def text_completions(request: CompletionRequest) -> JSONResponse | StreamingResponse:
    """
    Legacy /v1/completions endpoint.

    Maps the plain prompt to a single-turn chat completion internally.
    """
    canonical_name, replicate_id, prompt_format = _resolve_model(request.model)

    # Normalise prompt to a string
    raw_prompt = request.prompt if isinstance(request.prompt, str) else "\n".join(request.prompt)

    # Wrap in a user message so we can reuse the chat pipeline
    messages = [Message(role="user", content=raw_prompt)]
    chat_req = ChatCompletionRequest(
        model=request.model,
        messages=messages,
        temperature=request.temperature,
        top_p=request.top_p,
        max_tokens=request.max_tokens,
        stream=request.stream,
        stop=request.stop,
        n=request.n,
        user=request.user,
    )

    prompt, system_prompt = messages_to_prompt(messages, prompt_format)
    replicate_input = _build_replicate_input(chat_req, prompt, system_prompt)
    prompt_tokens = count_tokens(prompt)

    if request.stream:
        return StreamingResponse(
            _stream_completion_response(replicate_id, replicate_input, canonical_name),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    try:
        output = await run_prediction(replicate_id, replicate_input, stream=False)
    except PermissionError as exc:
        return _openai_error(str(exc), "authentication_error", "invalid_api_key", 401)
    except TimeoutError as exc:
        return _openai_error(str(exc), "server_error", "timeout", 504)
    except RuntimeError as exc:
        return _openai_error(str(exc), "server_error", "replicate_error", 500)

    completion_tokens = count_tokens(output)
    response = CompletionResponse(
        model=canonical_name,
        choices=[
            CompletionChoice(text=output, index=0, finish_reason="stop")
        ],
        usage=Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        ),
    )
    return JSONResponse(content=response.model_dump())


# ---------------------------------------------------------------------------
# Image generation
# ---------------------------------------------------------------------------

@router.post("/images/generations", response_model=None)
async def image_generations(request: ImageGenerationRequest) -> JSONResponse:
    """
    OpenAI-compatible image generation endpoint.

    Maps to Replicate image models. Supports response_format=url (default)
    and response_format=b64_json.
    """
    model_name = request.model or DEFAULT_IMAGE_MODEL

    # Resolve model: check alias map first, then treat as raw owner/name
    if model_name in IMAGE_MODEL_MAP:
        replicate_id, input_style = IMAGE_MODEL_MAP[model_name]
    elif "/" in model_name:
        replicate_id = model_name
        # Detect style from name heuristic
        slug = model_name.lower()
        input_style = "sdxl" if ("sdxl" in slug or "stable-diffusion" in slug) else "flux"
    else:
        return _openai_error(
            f"Unknown image model '{model_name}'. Use one of: {', '.join(IMAGE_MODEL_MAP)}",
            "invalid_request_error",
            "model_not_found",
            400,
        )

    replicate_input = build_image_input(
        prompt=request.prompt,
        input_style=input_style,
        size=request.size,
        n=request.n or 1,
        quality=request.quality,
        style=request.style,
    )

    try:
        urls = await run_image_prediction(replicate_id, replicate_input)
    except PermissionError as exc:
        return _openai_error(str(exc), "authentication_error", "invalid_api_key", 401)
    except TimeoutError as exc:
        return _openai_error(str(exc), "server_error", "timeout", 504)
    except RuntimeError as exc:
        return _openai_error(str(exc), "server_error", "replicate_error", 500)

    if not urls:
        return _openai_error("Replicate returned no images", "server_error", "no_output", 500)

    if request.response_format == "b64_json":
        data = await _urls_to_b64(urls)
    else:
        data = [ImageData(url=u) for u in urls]

    response = ImageGenerationResponse(data=data)
    return JSONResponse(content=response.model_dump())


async def _urls_to_b64(urls: list[str]) -> list[ImageData]:
    """Download image URLs and return them as base64-encoded ImageData objects."""
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        result: list[ImageData] = []
        for url in urls:
            resp = await client.get(url)
            resp.raise_for_status()
            b64 = base64.b64encode(resp.content).decode("utf-8")
            result.append(ImageData(b64_json=b64))
        return result

