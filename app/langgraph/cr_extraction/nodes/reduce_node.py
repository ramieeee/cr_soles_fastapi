from app.langgraph.cr_extraction.state import CrExtractionState


async def reduce_node(state: CrExtractionState) -> CrExtractionState:
    # TODO: merge inference_steps/evidence_store into final extracted objects.
    return {"extraction_complete": True}
