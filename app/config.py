import os
from dotenv import load_dotenv

load_dotenv()

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")
AUTH_MODE: bool = os.getenv("AUTH_MODE", "false").lower() == "true"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Maps OpenAI-style model names to (replicate_model_id, prompt_format)
# prompt_format is either "llama3" or "mistral"
MODEL_MAP: dict[str, tuple[str, str]] = {
    # Llama 3
    "llama-3-8b-instruct":       ("meta/meta-llama-3-8b-instruct",        "llama3"),
    "llama-3-70b-instruct":      ("meta/meta-llama-3-70b-instruct",       "llama3"),
    "llama-3.1-8b-instruct":     ("meta/meta-llama-3.1-8b-instruct",      "llama3"),
    "llama-3.1-70b-instruct":    ("meta/meta-llama-3.1-70b-instruct",     "llama3"),
    "llama-3.1-405b-instruct":   ("meta/meta-llama-3.1-405b-instruct",    "llama3"),
    # Mistral
    "mistral-7b-instruct":       ("mistralai/mistral-7b-instruct-v0.2",   "mistral"),
    "mixtral-8x7b-instruct":     ("mistralai/mixtral-8x7b-instruct-v0.1", "mistral"),
    # Deepseek
    "deepseek-r1":               ("deepseek-ai/deepseek-r1",              "llama3"),
    # Qwen
    "qwen2.5-72b-instruct":      ("qwen/qwen2.5-72b-instruct",            "llama3"),
}

DEFAULT_MODEL = "llama-3-8b-instruct"

REPLICATE_API_BASE = "https://api.replicate.com/v1"
