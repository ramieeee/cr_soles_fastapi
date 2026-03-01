from __future__ import annotations

import time

from app.core.logger import set_log
from app.enums.multimodal_extraction import VllmTaskType
from app.langgraph.cr_extraction.state import CrExtractionState
from app.langgraph.cr_extraction.nodes.common import parse_json_object
from app.prompts.cr_extraction import (
    get_instrument_system_prompt,
    get_instrument_user_prompt,
)
from app.utils.stream_invoke import stream_node_llm_and_collect


async def instrument_node(state: CrExtractionState) -> CrExtractionState:
    set_log("cr_extraction.instrument_node")

    pages_content = state.get("pages_content") or []
    population = state.get("population") or {}
    stream_prompt = state.get("stream_prompt")
    result = await stream_node_llm_and_collect(
        node="instrument_node",
        system_prompt=get_instrument_system_prompt(),
        user_prompt=get_instrument_user_prompt(
            pages_content,
            population,
            stream_prompt,
        ),
        task_type=VllmTaskType.CR_EXTRACTION,
        port="",
        timeout_s=300.0,
        start_message="extracting instrument",
        done_message="instrument extraction completed",
    )

    raw_text = str(result.get("text") or "")
    try:
        cr_operationalization = parse_json_object(raw_text)
    except Exception as exc:
        set_log(f"instrument_node parse failed: {exc}", level="error")
        cr_operationalization = {
            "instrument_name": None,
            "instrument_family": "not_detected",
            "detected_proxy_labels": [],
            "scoring_method": None,
            "time_administration": None,
            "evidence": [],
            "confidence": 0.0,
            "raw_text": raw_text,
        }

    events = list(state.get("debug_events") or [])
    events.append({"node": "instrument_node", "ts": time.time()})

    detected_name = cr_operationalization.get("instrument_name")
    return {
        "cr_operationalization": cr_operationalization,
        "detected_instruments": [detected_name] if detected_name else [],
        "validation_target": "instrument",
        "debug_events": events,
        "last_node": "instrument_node",
    }
