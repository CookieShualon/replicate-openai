# replicate-openai

An OpenAI-compatible API gateway that routes requests to [Replicate](https://replicate.com)-hosted models. Drop it in front of any OpenAI SDK client by changing one line of code.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
![GitHub Stars](https://img.shields.io/github/stars/cookieshualon/replicate-openai?style=flat&color=yellow)
[<img src="https://railway.com/button.svg" height="20">](https://railway.com/deploy/replicate-openai?referralCode=UJ-ev5&utm_medium=integration&utm_source=template&utm_campaign=generic)

## Table of Contents

- [Features](#features)
- [Use cases](#use-cases)
- [What it does](#what-it-does)
- [Quickstart](#quickstart)
- [Available models](#available-models)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Features

- OpenAI-compatible API surface (`/v1/chat/completions`, `/v1/completions`, `/v1/models`, `/v1/images/generate`)
- Automatic prompt formatting for Llama-3 and Mistral models
- Streaming and non-streaming response support
- Chat and image model support
- Pre-configured model aliases for popular models
- Live model list fetched from Replicate's collections
- BYOK (Bring Your Own Key) authentication mode
- Docker support

## Use cases

**Switch from OpenAI to open-source models without touching your code**
Your app already uses the OpenAI SDK. Change `base_url` to point here, pick a model like `llama-3-70b-instruct`, and everything — streaming, tool calls, message history — works as before. No SDK swap, no refactor.

**Cut costs on LLM-heavy workloads**
Replicate's per-second billing and open-weight models are often significantly cheaper than OpenAI for high-volume inference. Drop this gateway in and benchmark models side by side without rewriting any client code.

**Access 1000+ models through one API**
Replicate hosts thousands of community and official models across text, image, audio, and video. This gateway exposes all of them through the OpenAI interface — pass any `owner/model` ID as the `model` parameter and it just works.

**Build a multi-user AI service with BYOK**
Enable `AUTH_MODE=true` and each user can supply their own Replicate API token as a Bearer header. You don't hold anyone's credentials, and billing goes directly to each user's Replicate account.

**Add image generation to an OpenAI-based app**
Any app using `client.images.generate(...)` can use FLUX, Stable Diffusion, Imagen 4, or Ideogram via this gateway — no new SDK or client needed.

**Self-host for privacy or compliance**
Run the gateway on your own infrastructure. Requests go from your server to Replicate's API — no data passes through OpenAI.

**Use Replicate models inside AI coding tools**
Cursor, Kilo Code, Continue, and similar tools let you configure a custom OpenAI base URL. Point them at this gateway and use any Replicate model — Llama 3, DeepSeek R1, Qwen, or any other — directly inside your editor, with no OpenAI account required.

**Prototype with different models fast**
Swap `model="llama-3-70b-instruct"` for `model="deepseek-r1"` or any Replicate model ID. No config changes, no redeployment — just change the model name in your request.

## What it does

- Exposes the OpenAI REST API surface
- Translates each request into a Replicate prediction
- Streams or collects the output, then returns an OpenAI-shaped response
- Handles prompt formatting automatically for supported model families

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

**Chat completions (non-streaming):**

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

**Chat completions (streaming):**

```python
with client.chat.completions.stream(
    model="llama-3-70b-instruct",
    messages=[{"role": "user", "content": "Write a haiku about servers."}],
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

**Image generation:**

```python
response = client.images.generate(
    model="flux-schnell",
    prompt="A beautiful sunset over mountains",
    size="1024x1024",
    n=1,
)
image_url = response.data[0].url
print(image_url)
```

### 4. Run with Docker

Pull the pre-built image:

```bash
docker pull cookieshualon/replicate-openai
docker run -p 8000:8000 --env-file .env cookieshualon/replicate-openai
```

Or build it yourself:

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

## Configuration

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REPLICATE_API_TOKEN` | *(required in server mode)* | Your Replicate API token. Required when `AUTH_MODE=false`. |
| `AUTH_MODE` | `false` | Authentication mode: `false`=server uses `REPLICATE_API_TOKEN` for all requests; `true`=clients must provide their own token via `Authorization: Bearer <token>` (BYOK - Bring Your Own Key). |
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8000` | Listen port |

## Troubleshooting

**401 Unauthorized**: Check that `REPLICATE_API_TOKEN` is valid when using `AUTH_MODE=false`. If using `AUTH_MODE=true`, ensure your client passes a valid Replicate token in the `Authorization` header.

**404 Model not found**: Use `GET /v1/models` to see the full list of available models. You can use any model ID from that list, or pass a full `owner/name` Replicate model identifier directly.

**Streaming issues**: Ensure your OpenAI client supports Server-Sent Events (SSE). The gateway streams Replicate's output directly to maintain low latency.

**Connection errors**: Verify the server is running and accessible at the configured `HOST` and `PORT`. Check your firewall settings if running in a cloud environment.

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide — local setup, code style, how to add a model alias, and how to submit a PR.

Quick start:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
