from __future__ import annotations

import time
import uuid
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared primitives
# ---------------------------------------------------------------------------

class Message(BaseModel):
    role: Literal["system", "user", "assistant", "function", "tool"]
    content: str
    name: Optional[str] = None


# ---------------------------------------------------------------------------
# /v1/chat/completions — request
# ---------------------------------------------------------------------------

class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[Message]
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    max_tokens: Optional[int] = 512
    stream: Optional[bool] = False
    stop: Optional[Union[str, list[str]]] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    n: Optional[int] = 1
    user: Optional[str] = None
    # Extra pass-through fields that some clients send
    logit_bias: Optional[dict[str, float]] = None
    logprobs: Optional[bool] = None
    top_logprobs: Optional[int] = None
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# /v1/chat/completions — non-streaming response
# ---------------------------------------------------------------------------

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class Choice(BaseModel):
    index: int
    message: Message
    finish_reason: Optional[str] = "stop"
    logprobs: Optional[Any] = None


class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: list[Choice]
    usage: Usage


# ---------------------------------------------------------------------------
# /v1/chat/completions — streaming response (SSE chunks)
# ---------------------------------------------------------------------------

class Delta(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None


class StreamChoice(BaseModel):
    index: int
    delta: Delta
    finish_reason: Optional[str] = None
    logprobs: Optional[Any] = None


class ChatCompletionChunk(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex}")
    object: str = "chat.completion.chunk"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: list[StreamChoice]


# ---------------------------------------------------------------------------
# /v1/completions — legacy text completions
# ---------------------------------------------------------------------------

class CompletionRequest(BaseModel):
    model: str
    prompt: Union[str, list[str]]
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    max_tokens: Optional[int] = 512
    stream: Optional[bool] = False
    stop: Optional[Union[str, list[str]]] = None
    n: Optional[int] = 1
    user: Optional[str] = None
    echo: Optional[bool] = False
    best_of: Optional[int] = None
    logit_bias: Optional[dict[str, float]] = None
    logprobs: Optional[int] = None
    suffix: Optional[str] = None
    seed: Optional[int] = None


class CompletionChoice(BaseModel):
    text: str
    index: int
    logprobs: Optional[Any] = None
    finish_reason: Optional[str] = "stop"


class CompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"cmpl-{uuid.uuid4().hex}")
    object: str = "text_completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: list[CompletionChoice]
    usage: Usage


# ---------------------------------------------------------------------------
# /v1/models
# ---------------------------------------------------------------------------

class Model(BaseModel):
    id: str
    object: str = "model"
    created: int = Field(default_factory=lambda: int(time.time()))
    owned_by: str = "replicate"


class ModelList(BaseModel):
    object: str = "list"
    data: list[Model]


# ---------------------------------------------------------------------------
# /v1/images/generations
# ---------------------------------------------------------------------------

class ImageGenerationRequest(BaseModel):
    prompt: str
    model: str = "flux-schnell"
    n: Optional[int] = 1
    size: Optional[str] = "1024x1024"          # e.g. "1024x1024", "1792x1024"
    quality: Optional[str] = "standard"        # "standard" | "hd"
    response_format: Optional[str] = "url"     # "url" | "b64_json"
    style: Optional[str] = None                # passed through if model supports it
    user: Optional[str] = None


class ImageData(BaseModel):
    url: Optional[str] = None
    b64_json: Optional[str] = None
    revised_prompt: Optional[str] = None


class ImageGenerationResponse(BaseModel):
    created: int = Field(default_factory=lambda: int(time.time()))
    data: list[ImageData]


# ---------------------------------------------------------------------------
# Error format (mirrors OpenAI)
# ---------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    message: str
    type: str
    param: Optional[str] = None
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
