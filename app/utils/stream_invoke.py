from __future__ import annotations

from collections.abc import Callable
from typing import Any, AsyncIterator, Optional

import httpx

from app.clients.vllm_client import VllmClient
from app.enums.multimodal_extraction import VllmTaskType


# -------------------------
# LangGraph custom streaming
# -------------------------

StreamWriter = Callable[[dict[str, Any]], None]


def _get_writer(writer: StreamWriter | None) -> StreamWriter:
    if writer is not None:
        return writer

    from langgraph.config import get_stream_writer

    return get_stream_writer()


def _emit(writer: StreamWriter, *, event: str, node: str, **payload: Any) -> None:
    data: dict[str, Any] = {"event": event, "node": node}
    if payload:
        data.update(payload)
    writer(data)


def emit_node_progress(
    *,
    node: str,
    message: str,
    page: int | None = None,
    writer: StreamWriter | None = None,
    **fields: Any,
) -> None:
    """Emit a standard `node_progress` event (simple public API)."""

    w = _get_writer(writer)
    payload: dict[str, Any] = {"message": message}
    if page is not None:
        payload["page"] = page
    if fields:
        payload.update(fields)
    _emit(w, event="node_progress", node=node, **payload)


# -------------------------
# LLM streaming (currently via vLLM)
# -------------------------


async def stream_llm_delta_tokens(
    *,
    system_prompt: str,
    user_prompt: str,
    task_type: VllmTaskType,
    port: str | int | None = "",
    timeout_s: float = 300.0,
    max_tokens: Optional[int] = None,
    temperature: float = 0.2,
    extra: Optional[dict[str, Any]] = None,
) -> AsyncIterator[str]:
    """Stream chat completion and yield delta content tokens.

    Notes:
    - This is provider-agnostic at the call site, but is currently implemented
      with `VllmClient`.
    - Owns http client creation and streaming iteration.
    """

    vllm_client = VllmClient(port=port, timeout_s=timeout_s)

    async with httpx.AsyncClient(timeout=timeout_s, trust_env=False) as client:
        async for chunk in vllm_client.stream_chat(
            client,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            task_type=task_type,
            max_tokens=max_tokens,
            temperature=temperature,
            extra=extra,
        ):
            try:
                delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content")
            except Exception:
                delta = None

            if not delta:
                continue

            yield str(delta)


async def stream_llm_and_collect(
    *,
    system_prompt: str,
    user_prompt: str,
    task_type: VllmTaskType,
    on_token: Callable[[str], None] | None = None,
    port: str | int | None = "",
    timeout_s: float = 300.0,
    max_tokens: Optional[int] = None,
    temperature: float = 0.2,
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Stream tokens (side-effect) and return collected result.

    - Streaming output: via `on_token(token)` callback (optional)
    - Return value: includes both `tokens` and concatenated `text`
    """

    tokens: list[str] = []

    async for token in stream_llm_delta_tokens(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        task_type=task_type,
        port=port,
        timeout_s=timeout_s,
        max_tokens=max_tokens,
        temperature=temperature,
        extra=extra,
    ):
        tokens.append(token)
        if on_token is not None:
            on_token(token)

    text = "".join(tokens)
    return {
        "tokens": tokens,
        "text": text,
        "text_length": len(text),
        "token_count": len(tokens),
    }


async def stream_node_llm_and_collect(
    *,
    node: str,
    system_prompt: str,
    user_prompt: str,
    task_type: VllmTaskType,
    page: int | None = None,
    writer: StreamWriter | None = None,
    start_message: str = "starting llm stream",
    done_message: str = "completed llm stream",
    port: str | int | None = "",
    timeout_s: float = 300.0,
    max_tokens: Optional[int] = None,
    temperature: float = 0.2,
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """One-call helper for LangGraph nodes (simple public API).

    Handles writer + progress/token events + final collected return.
    """

    w = _get_writer(writer)
    emit_node_progress(node=node, message=start_message, page=page, writer=w)

    def on_token(token: str) -> None:
        _emit(w, event="llm_token", node=node, token=token, page=page)

    result = await stream_llm_and_collect(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        task_type=task_type,
        on_token=on_token,
        port=port,
        timeout_s=timeout_s,
        max_tokens=max_tokens,
        temperature=temperature,
        extra=extra,
    )

    emit_node_progress(
        node=node,
        message=done_message,
        page=page,
        writer=w,
        text_length=int(result.get("text_length") or 0),
    )
    return result
