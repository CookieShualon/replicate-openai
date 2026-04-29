from __future__ import annotations

# ---------------------------------------------------------------------------
# Image model registry
# ---------------------------------------------------------------------------
# Each entry: alias → (replicate_model_id, input_style)
#
# input_style:
#   "flux"   — uses aspect_ratio + num_outputs; supports go_fast / num_inference_steps
#   "sdxl"   — uses width + height + num_outputs
#   "sd3"    — uses aspect_ratio, output_format, cfg
#
IMAGE_MODEL_MAP: dict[str, tuple[str, str]] = {
    # FLUX family (Black Forest Labs)
    "flux-schnell":         ("black-forest-labs/flux-schnell",      "flux"),
    "flux-dev":             ("black-forest-labs/flux-dev",          "flux"),
    "flux-pro":             ("black-forest-labs/flux-1.1-pro",      "flux"),
    "flux-2-pro":           ("black-forest-labs/flux-2-pro",        "flux"),
    # Imagen / Google
    "imagen-3":             ("google/imagen-3",                     "flux"),
    "imagen-4":             ("google/imagen-4",                     "flux"),
    # Ideogram
    "ideogram-v3":          ("ideogram-ai/ideogram-v3-balanced",    "flux"),
    # Stable Diffusion
    "stable-diffusion-3":   ("stability-ai/stable-diffusion-3",    "sd3"),
    "sdxl":                 ("stability-ai/sdxl",                   "sdxl"),
}

DEFAULT_IMAGE_MODEL = "flux-schnell"

# ---------------------------------------------------------------------------
# Size helpers
# ---------------------------------------------------------------------------

# OpenAI size string → aspect_ratio string (for flux / sd3 style)
_SIZE_TO_ASPECT: dict[str, str] = {
    "256x256":   "1:1",
    "512x512":   "1:1",
    "1024x1024": "1:1",
    "1792x1024": "16:9",
    "1024x1792": "9:16",
}


def size_to_aspect_ratio(size: str | None) -> str:
    if size and size in _SIZE_TO_ASPECT:
        return _SIZE_TO_ASPECT[size]
    return "1:1"


def size_to_wh(size: str | None) -> tuple[int, int]:
    """Return (width, height) from an OpenAI size string."""
    if size:
        parts = size.lower().split("x")
        if len(parts) == 2:
            try:
                return int(parts[0]), int(parts[1])
            except ValueError:
                pass
    return 1024, 1024


# ---------------------------------------------------------------------------
# Input builders
# ---------------------------------------------------------------------------

def build_image_input(
    prompt: str,
    input_style: str,
    size: str | None,
    n: int,
    quality: str | None,
    style: str | None,
) -> dict:
    """Translate OpenAI image parameters into a Replicate input dict."""
    inp: dict = {"prompt": prompt}

    if input_style == "flux":
        inp["aspect_ratio"] = size_to_aspect_ratio(size)
        inp["num_outputs"] = max(1, min(n, 4))
        if quality == "hd":
            inp["num_inference_steps"] = 50
        if style:
            inp["style"] = style

    elif input_style == "sdxl":
        w, h = size_to_wh(size)
        inp["width"] = w
        inp["height"] = h
        inp["num_outputs"] = max(1, min(n, 4))

    elif input_style == "sd3":
        inp["aspect_ratio"] = size_to_aspect_ratio(size)
        inp["num_outputs"] = max(1, min(n, 4))
        if quality == "hd":
            inp["cfg"] = 7.5

    return inp
