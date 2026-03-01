from app.langgraph.cr_extraction.state import CrExtractionState


async def reduce_node(state: CrExtractionState) -> CrExtractionState:
    population = state.get("population") or {}
    cr_operationalization = state.get("cr_operationalization") or {}

    normalized_row = {
        "paper_id": state.get("paper_id"),
        "population_summary": population.get("population_summary"),
        "target_population": population.get("target_population"),
        "age_band": population.get("age_band"),
        "clinical_condition_tags": population.get("clinical_condition_tags", []),
        "country_setting": population.get("country_setting"),
        "instrument_name": cr_operationalization.get("instrument_name"),
        "instrument_family": cr_operationalization.get(
            "instrument_family", "not_detected"
        ),
        "detected_proxy_labels": cr_operationalization.get(
            "detected_proxy_labels", []
        ),
        "scoring_method": cr_operationalization.get("scoring_method"),
        "time_administration": cr_operationalization.get("time_administration"),
        "population_confidence": population.get("confidence"),
        "instrument_confidence": cr_operationalization.get("confidence"),
    }

    return {
        "normalized_row": normalized_row,
        "extraction_complete": True,
        "last_node": "reduce_node",
    }
