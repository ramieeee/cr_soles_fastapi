from __future__ import annotations

import json
import time
from typing import Any

from app.core.logger import set_log
from app.enums.multimodal_extraction import VllmTaskType
from app.langgraph.cr_extraction.state import CrExtractionState
from app.prompts.cr_extraction import (
    get_population_system_prompt,
    get_population_user_prompt,
)
from app.utils.stream_invoke import stream_node_llm_and_collect


def _parse_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in streamed response.")
    return json.loads(cleaned[start : end + 1])


async def population_node(state: CrExtractionState) -> CrExtractionState:
    set_log("cr_extraction.population_node")

    pages_content = state.get("pages_content") or []
    stream_prompt = state.get("stream_prompt")
    result = await stream_node_llm_and_collect(
        node="population_node",
        system_prompt=get_population_system_prompt(),
        user_prompt=get_population_user_prompt(pages_content, stream_prompt),
        task_type=VllmTaskType.CR_EXTRACTION,
        port="",
        timeout_s=300.0,
        start_message="extracting population",
        done_message="population extraction completed",
    )

    raw_text = str(result.get("text") or "")
    try:
        population = _parse_json_object(raw_text)
    except Exception as exc:
        set_log(f"population_node parse failed: {exc}", level="error")
        population = {
            "population_summary": None,
            "target_population": None,
            "age_band": None,
            "clinical_condition_tags": [],
            "country_setting": None,
            "evidence": [],
            "confidence": 0.0,
            "raw_text": raw_text,
        }

    events = list(state.get("debug_events") or [])
    events.append({"node": "population_node", "ts": time.time()})

    return {
        "population": population,
        "debug_events": events,
        "last_node": "population_node",
    }
