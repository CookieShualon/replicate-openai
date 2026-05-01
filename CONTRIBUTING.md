# Contributing to replicate-openai

Thanks for your interest in contributing. This document covers everything you need to get started — from setting up a local dev environment to submitting a pull request.

---

## Table of Contents

- [Project structure](#project-structure)
- [Setting up locally](#setting-up-locally)
- [Running the server](#running-the-server)
- [How to contribute](#how-to-contribute)
- [Adding a model alias](#adding-a-model-alias)
- [Code style](#code-style)
- [Submitting a pull request](#submitting-a-pull-request)
- [Reporting bugs](#reporting-bugs)

---

## Project structure

```
replicate-openai/
├── main.py                  # FastAPI app, homepage, server entry point
├── app/
│   ├── config.py            # Env vars, MODEL_MAP (chat aliases)
│   ├── routes.py            # All API endpoints (/v1/*)
│   ├── models.py            # Pydantic request/response schemas
│   ├── replicate_client.py  # Replicate API calls (predictions, model list)
│   ├── translator.py        # Prompt formatting, token counting, response shaping
│   └── image_models.py      # IMAGE_MODEL_MAP, image input builder
├── requirements.txt
├── Dockerfile
└── .env.example
```

The request lifecycle for chat completions:

```
Client → POST /v1/chat/completions
       → routes.py (auth, model resolution)
       → translator.py (messages → Replicate prompt)
       → replicate_client.py (run or stream prediction)
       → translator.py (Replicate output → OpenAI response)
       → Client
```

---

## Setting up locally

**Requirements:** Python 3.11+

```bash
git clone https://github.com/CookieShualon/replicate-openai.git
cd replicate-openai

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your REPLICATE_API_TOKEN
```

---

## Running the server

```bash
python main.py
# or with auto-reload during development:
uvicorn main:app --reload
```

The server starts at `http://localhost:8000`. Interactive API docs are at `/docs`.

---

## How to contribute

Good starting points:

- **Add a model alias** — the most common contribution (see below)
- **Improve prompt formatting** — `app/translator.py` handles Llama and Mistral templates; other model families may need their own
- **Add a new endpoint** — e.g. `/v1/embeddings`, `/v1/audio/transcriptions`
- **Fix a bug** — open an issue first if the fix is non-trivial
- **Improve error handling** — better messages for common Replicate API errors

If you're planning something large, open an issue to discuss the approach before writing code.

---

## Adding a model alias

### Chat / text model

Open `app/config.py` and add an entry to `MODEL_MAP`:

```python
MODEL_MAP = {
    # existing entries...
    "my-model-alias": "owner/model-name",
}
```

The alias will automatically appear in `GET /v1/models`.

If the model uses a non-standard prompt format (not Llama-3 or Mistral), add a formatter in `app/translator.py` and wire it up in `messages_to_prompt`.

### Image model

Open `app/image_models.py` and add an entry to `IMAGE_MODEL_MAP`:

```python
IMAGE_MODEL_MAP = {
    # existing entries...
    "my-image-alias": "owner/model-name",
}
```

If the model expects different input parameters, extend `build_image_input` to handle it.

---

## Code style

- **Python 3.11+**, no `from __future__ import annotations` hacks needed beyond what's already there
- **Pydantic v2** for all request/response models
- **Type annotations** on all function signatures
- **No comments** unless the why is non-obvious — code should be self-explanatory
- Run a quick sanity check before committing:

```bash
python -c "import main"         # import check
uvicorn main:app &              # start server
curl http://localhost:8000/     # homepage loads
curl http://localhost:8000/v1/models  # model list returns
kill %1
```

There is no enforced linter yet — consistent style with the surrounding code is enough.

---

## Submitting a pull request

1. Fork the repo and create a branch from `main`:
   ```bash
   git checkout -b feat/my-feature
   ```

2. Make your changes. Keep commits focused — one logical change per commit.

3. Test manually:
   ```bash
   python main.py &
   python test.py   # or your own smoke test
   ```

4. Push and open a PR against `main`. Include:
   - What the change does and why
   - Any Replicate model IDs or aliases affected
   - How you tested it

PRs that add model aliases don't need extensive justification — just confirm the model works end-to-end.

---

## Reporting bugs

Open a [GitHub issue](https://github.com/CookieShualon/replicate-openai/issues) with:

- What you did
- What you expected to happen
- What actually happened (include the full error / response body)
- Your Python version and OS
- Whether you're using `AUTH_MODE=true` or `false`
