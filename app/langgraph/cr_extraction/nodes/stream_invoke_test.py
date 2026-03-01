from __future__ import annotations

import time

from app.core.logger import set_log
from app.enums.multimodal_extraction import VllmTaskType
from app.langgraph.cr_extraction.state import CrExtractionState
from app.utils.stream_invoke import (
    stream_node_llm_and_collect,
)


async def stream_invoke_test1(state: CrExtractionState) -> CrExtractionState:
    page_index = int(state.get("current_page_index") or 0)
    set_log(f"cr_extraction.stream_invoke_test1: page_index={page_index}")

    pages_content = state.get("pages_content") or []
    page_text = (
        pages_content[page_index] if 0 <= page_index < len(pages_content) else ""
    )
    user_prompt = (
        state.get("stream_prompt")
        or f"Summarize the information given below\n\n{page_text[:4000]}"
    )

    result = await stream_node_llm_and_collect(
        node="stream_invoke_test1",
        page=page_index,
        system_prompt="You are a concise extraction assistant.",
        user_prompt=user_prompt,
        task_type=VllmTaskType.CR_EXTRACTION,
        port="",
        timeout_s=300.0,
        start_message="starting llm stream",
        done_message="completed llm stream",
    )

    events = list(state.get("debug_events") or [])
    events.append(
        {"node": "stream_invoke_test1", "ts": time.time(), "page": page_index}
    )
    streamed_text = str(result.get("text") or "")
    return {
        "debug_events": events,
        "last_node": "stream_invoke_test1",
        "streamed_text": streamed_text,
        "streamed_tokens": result.get("tokens", []),
    }


async def stream_invoke_test2(state: CrExtractionState) -> CrExtractionState:
    page_index = int(state.get("current_page_index") or 0)
    set_log(f"cr_extraction.stream_invoke_test2: page_index={page_index}")

    pages_content = state.get("pages_content") or []
    page_text = (
        pages_content[page_index] if 0 <= page_index < len(pages_content) else ""
    )
    user_prompt = (
        state.get("stream_prompt")
        or f"Summarize the information given below\n\n{page_text[:4000]}"
    )

    result = await stream_node_llm_and_collect(
        node="stream_invoke_test2",
        page=page_index,
        system_prompt="You are a concise extraction assistant.",
        user_prompt=user_prompt,
        task_type=VllmTaskType.CR_EXTRACTION,
        port="",
        timeout_s=300.0,
        start_message="starting llm stream",
        done_message="completed llm stream",
    )

    events = list(state.get("debug_events") or [])
    events.append(
        {"node": "stream_invoke_test2", "ts": time.time(), "page": page_index}
    )
    streamed_text = str(result.get("text") or "")
    return {
        "debug_events": events,
        "last_node": "stream_invoke_test2",
        "streamed_text": streamed_text,
        "streamed_tokens": result.get("tokens", []),
    }
