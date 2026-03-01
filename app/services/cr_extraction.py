from __future__ import annotations

import json
from typing import Any, AsyncIterator

from app.core.logger import set_log
from sqlalchemy.orm import Session
from app.langgraph.cr_extraction import get_cr_extraction_graph
from app.repositories.papers_repository import (
    get_paper_by_id,
)
from app.schemas.cr_extraction import CRExtractionRequest


def _normalize_pages_content(contents: Any) -> list[dict[str, Any]]:
    if not isinstance(contents, list):
        return []

    pages: list[dict[str, Any]] = []
    for item in contents:
        if isinstance(item, dict):
            pages.append(item)
            continue

        pages.append({"page": None, "text": str(item), "tables": [], "images": []})

    return pages


def _build_initial_state(
    payload: CRExtractionRequest, pages_content: list[dict[str, Any]]
) -> dict:
    return {
        "paper_id": payload.paper_id,
        "pages_content": pages_content,
        "current_page_index": 0,
        "debug_events": [],
        "stream_prompt": payload.stream_prompt,
    }


def _format_sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _resolve_pages_content(
    payload: CRExtractionRequest,
    db: Session,
) -> tuple[str | None, list[dict[str, Any]]]:
    if payload.pages_content:
        return payload.paper_id, _normalize_pages_content(payload.pages_content)

    if not payload.paper_id:
        raise ValueError("Either paper_id or pages_content must be provided.")

    paper = get_paper_by_id(db, paper_id=payload.paper_id)
    if paper is None:
        raise ValueError(f"Paper not found: {payload.paper_id}")

    return str(payload.paper_id), _normalize_pages_content(paper.pages_content)


# async def run_service(
#     payload: CRExtractionRequest,
#     db: Session,
# ) -> dict:
#     paper_id = payload.paper_id
#     set_log("Processing extraction service")

#     paper = get_paper_by_id(db, paper_id=paper_id)
#     if paper is None:
#         raise ValueError(f"Paper not found: {paper_id}")

#     pages_text = _normalize_pages_text(paper.pages_content)

#     graph = get_cr_extraction_graph()
#     state = _build_initial_state(payload, pages_text)

#     set_log("Invoking document graph")
#     result = await graph.ainvoke(state)

#     return {
#         "paper_id": paper_id,
#         "page_count": len(pages_text),
#         "last_node": result.get("last_node"),
#         "debug_events": result.get("debug_events", []),
#         "streamed_text": result.get("streamed_text", ""),
#     }


async def run_stream_service(
    payload: CRExtractionRequest,
    db: Session,
) -> AsyncIterator[str]:
    paper_id, pages_content = _resolve_pages_content(payload, db)
    graph = get_cr_extraction_graph()
    state = _build_initial_state(payload, pages_content)

    async def event_generator() -> AsyncIterator[str]:
        final_result: dict[str, Any] = {}

        yield _format_sse(
            "status",
            {
                "message": "cr extraction stream started",
                "paper_id": paper_id,
                "page_count": len(pages_content),
            },
        )

        try:
            async for item in graph.astream(
                state,
                stream_mode=["updates", "custom"],
            ):
                if isinstance(item, tuple) and len(item) == 2:
                    mode, chunk = item
                else:
                    mode, chunk = "updates", item

                if mode == "custom" and isinstance(chunk, dict):
                    event_name = chunk.get("event", "custom")
                    yield _format_sse(event_name, chunk)
                    continue

                if isinstance(chunk, dict):
                    for value in chunk.values():
                        if isinstance(value, dict):
                            final_result.update(value)

                yield _format_sse(
                    "graph_update",
                    {
                        "mode": mode,
                        "chunk": chunk,
                    },
                )

            yield _format_sse(
                "done",
                {
                    "message": "cr extraction stream completed",
                    "paper_id": paper_id,
                    "page_count": len(pages_content),
                    "result": {
                        "population": final_result.get("population"),
                        "cr_operationalization": final_result.get(
                            "cr_operationalization"
                        ),
                        "normalized_row": final_result.get("normalized_row"),
                    },
                },
            )
        except Exception as exc:
            set_log(f"Exception in run_stream_service: {exc}", level="error")
            yield _format_sse(
                "error",
                {
                    "message": str(exc),
                    "paper_id": paper_id,
                },
            )

    return event_generator()
