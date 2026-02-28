from __future__ import annotations

import asyncio
import time

import httpx
from langgraph.config import get_stream_writer

from app.clients.vllm_client import VllmClient
from app.core.logger import set_log
from app.enums.multimodal_extraction import VllmTaskType
from app.langgraph.cr_extraction.state import CrExtractionState


async def stream_invoke_test1(state: CrExtractionState) -> CrExtractionState:
    writer = get_stream_writer()
    page_index = int(state.get("current_page_index") or 0)
    set_log(f"cr_extraction.stream_invoke_test1: page_index={page_index}")
    writer(
        {
            "event": "node_progress",
            "node": "stream_invoke_test1",
            "message": "entered first test node",
            "page": page_index,
        }
    )
    await asyncio.sleep(0.1)
    events = list(state.get("debug_events") or [])
    events.append(
        {"node": "stream_invoke_test1", "ts": time.time(), "page": page_index}
    )
    writer(
        {
            "event": "node_progress",
            "node": "stream_invoke_test1",
            "message": "leaving first test node",
            "page": page_index,
        }
    )
    return {"debug_events": events, "last_node": "stream_invoke_test1"}


async def stream_invoke_test2(state: CrExtractionState) -> CrExtractionState:
    writer = get_stream_writer()
    page_index = int(state.get("current_page_index") or 0)
    set_log(f"cr_extraction.stream_invoke_test2: page_index={page_index}")
    writer(
        {
            "event": "node_progress",
            "node": "stream_invoke_test2",
            "message": "starting vllm stream",
            "page": page_index,
        }
    )

    pages = state.get("pages_text") or []
    page_text = pages[page_index] if 0 <= page_index < len(pages) else ""
    user_prompt = (
        state.get("stream_test_prompt")
        or f"Summarize this page in one sentence.\n\n{page_text[:4000]}"
        or "Return a short sentence for stream testing."
    )

    collected_tokens: list[str] = []
    vllm_client = VllmClient(port="", timeout_s=300.0)
    async with httpx.AsyncClient(timeout=300.0, trust_env=False) as client:
        async for chunk in vllm_client.stream_chat(
            client,
            system_prompt="You are a concise extraction assistant.",
            user_prompt=user_prompt,
            task_type=VllmTaskType.CR_EXTRACTION,
            max_tokens=128,
        ):
            delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content")
            if not delta:
                continue

            collected_tokens.append(delta)
            writer(
                {
                    "event": "llm_token",
                    "node": "stream_invoke_test2",
                    "token": delta,
                    "page": page_index,
                }
            )

    events = list(state.get("debug_events") or [])
    events.append(
        {"node": "stream_invoke_test2", "ts": time.time(), "page": page_index}
    )
    streamed_text = "".join(collected_tokens)
    writer(
        {
            "event": "node_progress",
            "node": "stream_invoke_test2",
            "message": "completed vllm stream",
            "page": page_index,
            "text_length": len(streamed_text),
        }
    )
    return {
        "debug_events": events,
        "last_node": "stream_invoke_test2",
        "streamed_text": streamed_text,
    }
