# replicate-openai

An OpenAI-compatible API gateway that routes requests to [Replicate](https://replicate.com)-hosted models. Drop it in front of any OpenAI SDK client by changing one line of code.

## What it does

- Exposes the OpenAI REST API surface (`/v1/chat/completions`, `/v1/completions`, `/v1/models`)
- Translates each request into a Replicate prediction, streams or collects the output, then returns an OpenAI-shaped response
- Handles Llama-3 and Mistral prompt formatting automatically
- Supports both streaming (`stream: true`) and non-streaming responses

## Quickstart

### 1. Set your Replicate token

```bash
cp .env.example .env
# Edit .env and paste your token from https://replicate.com/account/api-tokens
```

### 2. Install dependencies and run

```bash
pip install -r requirements.txt
python main.py
# or: uvicorn main:app --reload
```

The server starts on `http://localhost:8000`. Interactive API docs are at `http://localhost:8000/docs`.

### 3. Point your OpenAI client at it

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-used",          # any non-empty string works
)

response = client.chat.completions.create(
    model="llama-3-8b-instruct",
    messages=[{"role": "user", "content": "Hello! Who are you?"}],
)
print(response.choices[0].message.content)
```

Streaming works identically:

```python
with client.chat.completions.stream(
    model="llama-3-70b-instruct",
    messages=[{"role": "user", "content": "Write a haiku about servers."}],
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

### 4. Run with Docker

```bash
docker build -t replicate-openai .
docker run -p 8000:8000 --env-file .env replicate-openai
```

## Available models

`GET /v1/models` returns the full live list fetched from Replicate's model collections, refreshed every 5 minutes. You can use any model from that list, or pass an `owner/name` Replicate model ID directly — no configuration needed.

### Shorthand aliases

A set of commonly used models are pre-configured with short names:

**Chat:**

| Alias | Replicate model |
|-------|----------------|
| `llama-3-8b-instruct` | meta/meta-llama-3-8b-instruct |
| `llama-3-70b-instruct` | meta/meta-llama-3-70b-instruct |
| `llama-3.1-8b-instruct` | meta/meta-llama-3.1-8b-instruct |
| `llama-3.1-70b-instruct` | meta/meta-llama-3.1-70b-instruct |
| `llama-3.1-405b-instruct` | meta/meta-llama-3.1-405b-instruct |
| `mistral-7b-instruct` | mistralai/mistral-7b-instruct-v0.2 |
| `mixtral-8x7b-instruct` | mistralai/mixtral-8x7b-instruct-v0.1 |
| `deepseek-r1` | deepseek-ai/deepseek-r1 |
| `qwen2.5-72b-instruct` | qwen/qwen2.5-72b-instruct |

**Image:**

| Alias | Replicate model |
|-------|----------------|
| `flux-schnell` | black-forest-labs/flux-schnell |
| `flux-dev` | black-forest-labs/flux-dev |
| `flux-pro` | black-forest-labs/flux-1.1-pro |
| `flux-2-pro` | black-forest-labs/flux-2-pro |
| `imagen-3` | google/imagen-3 |
| `imagen-4` | google/imagen-4 |
| `ideogram-v3` | ideogram-ai/ideogram-v3-balanced |
| `stable-diffusion-3` | stability-ai/stable-diffusion-3 |
| `sdxl` | stability-ai/sdxl |

### Using any Replicate model

Pass the `owner/name` (or `owner/name:version`) directly as the `model` parameter:

```python
# Any language model on Replicate
client.chat.completions.create(model="mistralai/mistral-7b-instruct-v0.2", ...)

# Any image model on Replicate
client.images.generate(model="black-forest-labs/flux-dev", ...)
```

### Adding a permanent alias

To give a model a short name, add it to `MODEL_MAP` in `app/config.py` (chat) or `IMAGE_MODEL_MAP` in `app/image_models.py` (images). It will appear in `GET /v1/models` automatically.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REPLICATE_API_TOKEN` | *(required)* | Your Replicate API token |
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8000` | Listen port |
