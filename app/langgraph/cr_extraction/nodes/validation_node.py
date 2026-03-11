from __future__ import annotations

from typing import Any

from app.core.logger import set_log
from app.enums.multimodal_extraction import VllmTaskType
from app.langgraph.cr_extraction.state import CrExtractionState
from app.langgraph.cr_extraction.nodes.common import (
    normalize_evidence_list,
    parse_json_object,
    pick_relevant_pages,
)
from app.prompts.cr_extraction import (
    get_instrument_system_prompt,
    get_instrument_verify_prompt,
    get_population_system_prompt,
    get_population_verify_prompt,
)
from app.utils.stream_invoke import stream_node_llm_and_collect


async def validation_node(state: CrExtractionState) -> CrExtractionState:
    validation_target = state.get("validation_target")
    pages_content = state.get("pages_content") or []
    set_log(f"cr_extraction.validation_node: target={validation_target}")

    if validation_target == "population":
        population = dict(state.get("population") or {})
        relevant_pages = pick_relevant_pages(pages_content, population)
        result = await stream_node_llm_and_collect(
            node="validation_node_population",
            system_prompt=get_population_system_prompt(),
            user_prompt=get_population_verify_prompt(relevant_pages, population),
            task_type=VllmTaskType.CR_EXTRACTION,
            port="",
            timeout_s=300.0,
            start_message="re-validating population evidence",
            done_message="population re-validation completed",
        )

        verify_text = str(result.get("text") or "")
        try:
            population = parse_json_object(verify_text)
        except Exception as exc:
            set_log(f"validation population parse failed: {exc}", level="error")
            population["verify_raw_text"] = verify_text

        population["evidence"] = normalize_evidence_list(
            population.get("evidence"),
            pages_content,
        )
        if not population.get("evidence"):
            population["confidence"] = min(
                float(population.get("confidence") or 0.0),
                0.4,
            )
        population["evidence_pages"] = [
            item["page"] for item in population.get("evidence", []) if "page" in item
        ]
        return {
            "population": population,
            "last_node": "validation_node",
        }

    if validation_target == "instrument":
        cr_operationalization = dict(state.get("cr_operationalization") or {})
        relevant_pages = pick_relevant_pages(pages_content, cr_operationalization)
        result = await stream_node_llm_and_collect(
            node="validation_node_instrument",
            system_prompt=get_instrument_system_prompt(),
            user_prompt=get_instrument_verify_prompt(
                relevant_pages,
                cr_operationalization,
            ),
            task_type=VllmTaskType.CR_EXTRACTION,
            port="",
            timeout_s=300.0,
            start_message="re-validating instrument evidence",
            done_message="instrument re-validation completed",
        )

        verify_text = str(result.get("text") or "")
        try:
            cr_operationalization = parse_json_object(verify_text)
        except Exception as exc:
            set_log(f"validation instrument parse failed: {exc}", level="error")
            cr_operationalization["verify_raw_text"] = verify_text

        cr_operationalization["evidence"] = normalize_evidence_list(
            cr_operationalization.get("evidence"),
            pages_content,
        )
        if not cr_operationalization.get("evidence"):
            cr_operationalization["confidence"] = min(
                float(cr_operationalization.get("confidence") or 0.0),
                0.4,
            )
        cr_operationalization["evidence_pages"] = [
            item["page"]
            for item in cr_operationalization.get("evidence", [])
            if "page" in item
        ]
        return {
            "cr_operationalization": cr_operationalization,
            "last_node": "validation_node",
        }

    return {"last_node": "validation_node"}
