from __future__ import annotations

from app.core.logger import set_log
from app.langgraph.cr_extraction.state import CrExtractionState


async def validation_node(state: CrExtractionState) -> CrExtractionState:
    """Validate the latest per-page extraction.

    Scaffold:
    - Later you can add schema validation, confidence checks, retry_focus selection, etc.
    """

    page_index = int(state.get("current_page_index") or 0)
    steps = state.get("inference_steps") or []
    set_log(
        f"cr_extraction.validation_node: page_index={page_index} steps={len(steps)}"
    )

    # No-op validation for now.
    return {}
