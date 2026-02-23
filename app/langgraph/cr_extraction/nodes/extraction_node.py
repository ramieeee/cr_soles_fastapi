from __future__ import annotations

from app.core.logger import set_log
from app.langgraph.cr_extraction.state import CrExtractionState


async def extraction_node(state: CrExtractionState) -> CrExtractionState:
    """Extract data for the current page.

    This node is meant to be used in a graph loop:
    extraction(page i) -> validation(page i) -> next_page -> extraction(page i+1) ...
    """

    pages = state.get("pages_text") or []
    page_index = int(state.get("current_page_index") or 0)

    set_log(
        f"cr_extraction.extraction_node: page_index={page_index} pages={len(pages)}"
    )

    if not pages:
        return {
            "missing_fields": ["pages_text"],
            "extraction_complete": False,
        }

    if page_index < 0 or page_index >= len(pages):
        return {
            "missing_fields": ["current_page_index"],
            "extraction_complete": False,
        }

    page_text = pages[page_index]
    _ = page_text

    steps = list(state.get("inference_steps") or [])
    steps.append(
        {
            "page": page_index,
            "focus": "",
            "memory": "",
            "evidence": {},
            "confidence": None,
        }
    )

    return {
        "inference_steps": steps,
    }
