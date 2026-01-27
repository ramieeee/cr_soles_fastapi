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
    pdf_bytes: bytes, content_type: str | None, prompt: str, db: Session
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
    embedding = result.get("embeddings")
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
        set_log(f"Found {len(similar_doc)} similar documents in the database.")
        result["similar_documents"] = [
            {
                "id": doc.id,
                "title": doc.title,
                "similarity": doc.similarity,
            }
            for doc in similar_doc
        ]
    else:
        set_log("No similar documents found in the database.")
        result["similar_documents"] = []

    metadata = result.get("metadata") or {}
    missing_fields = result.get("missing_fields", [])

    title = metadata.get("title") or "Unknown title"
    authors = metadata.get("authors") or []
    journal = metadata.get("journal") or None
    year = metadata.get("year")
    abstract = metadata.get("abstract") or None

    paper = create_paper(
        db,
        title=title,
        authors=authors,
        journal=journal,
        year=year,
        abstract=abstract,
        pdf_url=None,
        ingestion_source="multimodal_extraction",
        embedding=embedding if embedding else None,
    )
    create_extraction(
        db,
        paper_id=paper.id,
        extraction_version="v1",
        metadata_jsonb=metadata or None,
        status="success" if not missing_fields else "partial",
    )

    return {
        "pages": pages,
        "metadata": metadata,
        "missing_fields": missing_fields,
        "page_count": len(pages),
    }
