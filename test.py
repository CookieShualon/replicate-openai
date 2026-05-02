"""
Cost-efficient smoke tests for the replicate-openai gateway.
Requires the server to be running (python main.py) and REPLICATE_API_TOKEN set.

Usage:
    python test.py [--base-url http://localhost:8000]
"""

import argparse
import os
import sys
import httpx
from openai import OpenAI

# Cheapest models: fast inference, low cost
CHAT_MODEL  = "llama-3-8b-instruct"
IMAGE_MODEL = "flux-schnell"

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"


def check(name: str, fn):
    try:
        fn()
        print(f"  {PASS}  {name}")
        return True
    except Exception as e:
        print(f"  {FAIL}  {name}")
        print(f"         {e}")
        return False


def run_tests(base_url: str) -> int:
    # Detect auth mode and pick the right api_key for the OpenAI client
    try:
        r = httpx.get(f"{base_url}/v1/auth-mode", timeout=5)
        auth_mode: bool = r.json().get("auth_mode", False)
    except Exception:
        auth_mode = False

    if auth_mode:
        token = os.environ.get("REPLICATE_API_TOKEN")
        if not token:
            print("AUTH_MODE is on but REPLICATE_API_TOKEN is not set in env — cannot run tests.")
            return 1
        api_key = token
    else:
        api_key = "test"

    client = OpenAI(base_url=f"{base_url}/v1", api_key=api_key)
    failures = 0

    # -------------------------------------------------------------------------
    print("\n── Health ──────────────────────────────────────────")

    def test_health():
        r = httpx.get(base_url, timeout=5)
        assert r.status_code == 200

    if not check("GET / returns 200", test_health):
        failures += 1

    def test_auth_mode_endpoint():
        r = httpx.get(f"{base_url}/v1/auth-mode", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert "auth_mode" in data
        assert isinstance(data["auth_mode"], bool)

    if not check("GET /auth-mode returns auth_mode bool", test_auth_mode_endpoint):
        failures += 1

    # -------------------------------------------------------------------------
    print("\n── Models ──────────────────────────────────────────")

    def test_list_models():
        models = client.models.list()
        ids = [m.id for m in models.data]
        assert CHAT_MODEL  in ids, f"{CHAT_MODEL} not in model list"
        assert IMAGE_MODEL in ids, f"{IMAGE_MODEL} not in model list"
        assert len(ids) > 9, "expected more than the hardcoded models"

    def test_get_model():
        m = client.models.retrieve(CHAT_MODEL)
        assert m.id == CHAT_MODEL
    def test_get_image_model():
        m = client.models.retrieve(IMAGE_MODEL)
        assert m.id == IMAGE_MODEL

    if not check("GET /v1/models lists chat + image models", test_list_models):
        failures += 1
    if not check(f"GET /v1/models/{CHAT_MODEL}", test_get_model):
        failures += 1
    if not check(f"GET /v1/models/{IMAGE_MODEL}", test_get_image_model):
        failures += 1

    # -------------------------------------------------------------------------
    print("\n── Chat completions ────────────────────────────────")

    def test_chat():
        resp = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{"role": "user", "content": "Reply with one word: hello"}],
            max_tokens=10,
        )
        text = resp.choices[0].message.content
        assert text and len(text) > 0
        assert resp.usage.total_tokens > 0

    def test_chat_system():
        resp = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": "You are a pirate. Always say 'Arrr'."},
                {"role": "user", "content": "Say hi"},
            ],
            max_tokens=15,
        )
        assert resp.choices[0].message.content

    def test_chat_stream():
        chunks = list(client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{"role": "user", "content": "Count: 1"}],
            max_tokens=10,
            stream=True,
        ))
        assert len(chunks) > 0
        last = chunks[-1]
        assert last.choices[0].finish_reason == "stop"

    def test_chat_unknown_model_fallback():
        resp = client.chat.completions.create(
            model="nonexistent-model-xyz",
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=5,
        )
        assert resp.choices[0].message.content is not None

    if not check("POST /v1/chat/completions (non-streaming)", test_chat):
        failures += 1
    if not check("POST /v1/chat/completions (system prompt)", test_chat_system):
        failures += 1
    if not check("POST /v1/chat/completions (streaming)", test_chat_stream):
        failures += 1
    if not check("Unknown model falls back gracefully", test_chat_unknown_model_fallback):
        failures += 1

    # -------------------------------------------------------------------------
    print("\n── Legacy completions ──────────────────────────────")

    def test_completion():
        resp = client.completions.create(
            model=CHAT_MODEL,
            prompt="The capital of France is",
            max_tokens=5,
        )
        assert resp.choices[0].text
    def test_completion_stream():
        chunks = list(client.completions.create(
            model=CHAT_MODEL,
            prompt="Reply with one word: hi",
            max_tokens=5,
            stream=True,
        ))
        assert len(chunks) > 0
        assert chunks[-1].choices[0].finish_reason == "stop"

    if not check("POST /v1/completions", test_completion):
        failures += 1
    if not check("POST /v1/completions (streaming)", test_completion_stream):
        failures += 1

    # -------------------------------------------------------------------------
    print("\n── Image generation ────────────────────────────────")

    def test_image_url():
        resp = client.images.generate(
            model=IMAGE_MODEL,
            prompt="a red circle on a white background",
            size="512x512",
            n=1,
        )
        url = resp.data[0].url
        assert url and url.startswith("https://"), f"bad URL: {url}"
        r = httpx.head(url, timeout=10, follow_redirects=True)
        assert r.status_code == 200

    def test_image_b64():
        resp = client.images.generate(
            model=IMAGE_MODEL,
            prompt="a blue square",
            size="512x512",
            n=1,
            response_format="b64_json",
        )
        b64 = resp.data[0].b64_json
        assert b64 and len(b64) > 100

    if not check("POST /v1/images/generations (url)", test_image_url):
        failures += 1
    if not check("POST /v1/images/generations (b64_json)", test_image_b64):
        failures += 1

    # -------------------------------------------------------------------------
    print()
    total = 13
    passed = total - failures
    status = PASS if failures == 0 else FAIL
    print(f"Results: {status}  {passed}/{total} passed\n")
    return failures


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()

    sys.exit(run_tests(args.base_url))
