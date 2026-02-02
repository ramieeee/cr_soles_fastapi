from __future__ import annotations

import base64

import fitz  # PyMuPDF

from app.langgraph.multimodal_extraction import get_document_graph
from app.core.logger import set_log
from app.repositories.papers_repository import (
    find_similar_papers,
    create_paper,
    create_extraction,
)
from sqlalchemy.orm import Session


SUPPORTED_PDF_TYPES = {
    "application/pdf",
    "application/x-pdf",
    "application/acrobat",
    "applications/vnd.pdf",
    "text/pdf",
    "text/x-pdf",
}


def _ensure_supported_pdf(content_type: str | None) -> None:
    if not content_type or content_type not in SUPPORTED_PDF_TYPES:
        raise ValueError("Only PDF files are supported.")


async def run_service(
    pdf_bytes: bytes,
    ingestion_source: str,
    content_type: str | None,
    prompt: str,
    db: Session,
) -> dict:
    _ensure_supported_pdf(content_type)

    set_log("Processing document bytes")

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise ValueError(f"Invalid PDF: {exc}") from exc

    page_images_b64: list[str] = []
    try:
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            png_bytes = pix.tobytes("png")
            page_images_b64.append(base64.b64encode(png_bytes).decode("ascii"))
    finally:
        doc.close()

    if not page_images_b64:
        raise ValueError("PDF has no pages.")

    graph = get_document_graph()

    state = {
        "page_images_b64": page_images_b64,
        "prompt": prompt,
        "attempts": 0,
        "max_attempts": 1,
    }

    set_log("Invoking document graph")
    result = await graph.ainvoke(state)
    pages = result.get("ocr_pages", [])
    embedding = result.get("embedding")
    similar_doc = []
    if embedding:
        similar_doc = find_similar_papers(
            db,
            embedding=embedding,
            limit=1,
            min_similarity=0.90,
        )

    # Similar to DB session management in routers
    if similar_doc:

        result["similar_documents"] = [
            {
                "id": doc.get("id"),
                "title": doc.get("title"),
                "similarity": doc.get("similarity"),
            }
            for doc in similar_doc
        ]
        set_log(
            f"Similar documents found: {similar_doc} with similarity {similar_doc[0]['similarity'] if similar_doc else 'N/A'}"
        )
    else:
        set_log("No similar documents found in the database.")
        result["similar_documents"] = []

    bibliographic_info = result.get("bibliographic_info") or {}
    missing_fields = result.get("missing_fields", [])

    title = bibliographic_info.get("title") or "Unknown title"
    authors = bibliographic_info.get("authors") or []
    journal = bibliographic_info.get("journal") or None
    year = bibliographic_info.get("year")
    abstract = bibliographic_info.get("abstract") or None

    paper = create_paper(
        db,
        title=title,
        authors=authors,
        journal=journal,
        year=year,
        abstract=abstract,
        pdf_url=None,
        ingestion_source=ingestion_source,
        embedding=embedding if embedding else None,
    )

    return {
        "pages": pages,
        "bibliographic_info": bibliographic_info,
        "missing_fields": missing_fields,
        "page_count": len(pages),
    }
