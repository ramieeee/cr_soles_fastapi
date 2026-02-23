from app.langgraph.cr_extraction.state import CrExtractionState


async def next_page_node(state: CrExtractionState) -> CrExtractionState:
    page_index = int(state.get("current_page_index") or 0)
    return {"current_page_index": page_index + 1}
