# Agent Instructions

## Project Overview

`replicate-openai` is a FastAPI gateway that exposes an OpenAI-compatible API and routes requests to Replicate-hosted models. Keep changes focused on preserving OpenAI SDK compatibility while translating requests and responses to Replicate cleanly.

## Repository Layout

- `main.py` defines the FastAPI app, CORS setup, homepage, and server entry point.
- `app/routes.py` owns the `/v1/*` API endpoints, auth handling, and model resolution.
- `app/models.py` contains Pydantic request and response schemas.
- `app/translator.py` formats chat/completion prompts and converts Replicate outputs into OpenAI-shaped responses.
- `app/replicate_client.py` contains Replicate API calls, prediction handling, streaming, and model list fetching.
- `app/config.py` contains environment configuration and chat model aliases in `MODEL_MAP`.
- `app/image_models.py` contains image model aliases in `IMAGE_MODEL_MAP` and image input shaping.
- `test.py` is a smoke test suite that expects a running server and may call paid Replicate models.

## Local Setup

Use Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `REPLICATE_API_TOKEN` in `.env` for server mode unless using BYOK auth.

## Running

```bash
python main.py
```

or:

```bash
uvicorn main:app --reload
```

The service runs at `http://localhost:8000`; OpenAI-compatible endpoints are under `http://localhost:8000/v1`.

## Testing

Quick import check:

```bash
python -c "import main"
```

Smoke tests:

```bash
python main.py
python test.py
```

`test.py` makes real API calls through Replicate, including image generation, so run it only when credentials and cost are acceptable.

## Coding Guidelines

- Match the existing simple FastAPI/Pydantic style.
- Use type annotations on public functions and new helper functions.
- Keep OpenAI response shapes stable; client SDK compatibility is the main contract.
- Prefer small, explicit helpers over broad abstractions.
- Avoid comments unless the reason for the code is not obvious.
- Do not add new dependencies unless the benefit is clear and documented.

## Common Changes

To add a chat/text alias, update `MODEL_MAP` in `app/config.py`.

To add an image alias, update `IMAGE_MODEL_MAP` in `app/image_models.py`.

If a model requires special prompt formatting, add the formatter in `app/translator.py` and route to it from the existing prompt conversion path.

If a model requires special image inputs, extend `build_image_input` in `app/image_models.py`.

## Safety Notes

- Keep secrets out of the repository. Use `.env` for `REPLICATE_API_TOKEN`.
- Preserve `AUTH_MODE=true` behavior: clients supply their own Replicate token via `Authorization: Bearer ...`.
- Be careful with live model list behavior; `/v1/models` combines configured aliases with Replicate-fetched models.
