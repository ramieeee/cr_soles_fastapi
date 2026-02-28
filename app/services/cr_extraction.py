from __future__ import annotations

from app.core.logger import set_log
from sqlalchemy.orm import Session
from app.langgraph.cr_extraction import get_cr_extraction_graph
from app.repositories.papers_repository import (
    get_paper_by_id,
)
from app.schemas.cr_extraction import CRExtractionRequest


async def run_service(
    payload: CRExtractionRequest,
    db: Session,
) -> dict:
    paper_id = payload.paper_id
    set_log("Processing extraction service")

    # Fetch paper details from DB
    paper = get_paper_by_id(db, paper_id=paper_id)
    contents = paper.pages_content or []

    try:
        print("frame")
    finally:
        print("finally")

    graph = get_cr_extraction_graph()

    state = {
        "payload": paper_id,
        "pages_content": contents,
    }

    set_log("Invoking document graph")
    # invoke the graph
    result = await graph.ainvoke(state)

    # returning results postprocessing
    # bibliographic_info = result.get("bibliographic_info") or {}
    # missing_fields = result.get("missing_fields", [])

    # DB operations here
    # ...

    return {
        # "pages": pages,
        # "bibliographic_info": bibliographic_info,
        # "page_count": len(pages),
    }
