from __future__ import annotations

import math
import time
import uuid
from typing import Optional

from app.models import (
    ChatCompletionChunk,
    ChatCompletionResponse,
    Choice,
    Delta,
    Message,
    StreamChoice,
    Usage,
)


# ---------------------------------------------------------------------------
# Token counting (rough estimate)
# ---------------------------------------------------------------------------

def count_tokens(text: str) -> int:
    """Rough token estimate: word count * 1.3, minimum 1."""
    if not text:
        return 0
    return max(1, math.ceil(len(text.split()) * 1.3))


# ---------------------------------------------------------------------------
# Prompt formatting
# ---------------------------------------------------------------------------

def _format_llama3(messages: list[Message], system_prompt: str) -> str:
    """
    Format messages using the Llama-3 instruct template.

    Structure:
        <|begin_of_text|>
        <|start_header_id|>system<|end_header_id|>
        {system}
        <|eot_id|>
        <|start_header_id|>user<|end_header_id|>
        {user}
        <|eot_id|>
        <|start_header_id|>assistant<|end_header_id|>
    """
    parts: list[str] = ["<|begin_of_text|>"]

    if system_prompt:
        parts.append(
            f"<|start_header_id|>system<|end_header_id|>\n{system_prompt}\n<|eot_id|>"
        )

    for msg in messages:
        if msg.role == "system":
            # Already handled above; skip repeated system messages in the loop.
            continue
        role_tag = msg.role  # "user" or "assistant"
        parts.append(
            f"<|start_header_id|>{role_tag}<|end_header_id|>\n{msg.content}\n<|eot_id|>"
        )

    # Open the assistant turn for generation
    parts.append("<|start_header_id|>assistant<|end_header_id|>")
    return "\n".join(parts)


def _format_mistral(messages: list[Message], system_prompt: str) -> str:
    """
    Format messages using the Mistral instruct template.

    Structure: [INST] {optional system prefix}{user} [/INST] {assistant} [INST] ...
    """
    parts: list[str] = []
    system_prefix = f"{system_prompt}\n\n" if system_prompt else ""
    first_user = True

    i = 0
    non_system = [m for m in messages if m.role != "system"]

    while i < len(non_system):
        msg = non_system[i]
        if msg.role == "user":
            prefix = system_prefix if first_user else ""
            first_user = False
            parts.append(f"[INST] {prefix}{msg.content} [/INST]")
        elif msg.role == "assistant":
            parts.append(f" {msg.content} ")
        i += 1

    return "".join(parts)


def messages_to_prompt(messages: list[Message], model_name: str) -> tuple[str, str]:
    """
    Convert an OpenAI messages array to a (prompt, system_prompt) tuple.

    Returns:
        prompt        - full formatted prompt string
        system_prompt - extracted system content (may be empty)
    """
    # Extract system prompt from the first system message
    system_prompt = ""
    for msg in messages:
        if msg.role == "system":
            system_prompt = msg.content
            break

    # Choose format based on model name suffix passed from config
    if model_name == "llama3":
        prompt = _format_llama3(messages, system_prompt)
    else:
        # mistral and generic fallback
        prompt = _format_mistral(messages, system_prompt)

    return prompt, system_prompt


# ---------------------------------------------------------------------------
# Response builders
# ---------------------------------------------------------------------------

def replicate_output_to_openai(
    output: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> ChatCompletionResponse:
    """Wrap a completed Replicate output string in an OpenAI ChatCompletionResponse."""
    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex}",
        object="chat.completion",
        created=int(time.time()),
        model=model,
        choices=[
            Choice(
                index=0,
                message=Message(role="assistant", content=output),
                finish_reason="stop",
            )
        ],
        usage=Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        ),
    )


def stream_chunk(
    delta_text: str,
    model: str,
    chunk_id: str,
    finish_reason: Optional[str] = None,
) -> ChatCompletionChunk:
    """Build a single SSE ChatCompletionChunk for streaming responses."""
    return ChatCompletionChunk(
        id=chunk_id,
        object="chat.completion.chunk",
        created=int(time.time()),
        model=model,
        choices=[
            StreamChoice(
                index=0,
                delta=Delta(content=delta_text) if delta_text else Delta(),
                finish_reason=finish_reason,
            )
        ],
    )


def opening_chunk(model: str, chunk_id: str) -> ChatCompletionChunk:
    """First chunk in a stream — carries role only, no content."""
    return ChatCompletionChunk(
        id=chunk_id,
        object="chat.completion.chunk",
        created=int(time.time()),
        model=model,
        choices=[
            StreamChoice(
                index=0,
                delta=Delta(role="assistant"),
                finish_reason=None,
            )
        ],
    )
