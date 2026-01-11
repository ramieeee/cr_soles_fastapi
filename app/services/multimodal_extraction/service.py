from __future__ import annotations

import base64

import fitz  # PyMuPDF

from app.langgraph.multimodal_extraction import get_document_graph


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


async def process_document_bytes(
    pdf_bytes: bytes,
    content_type: str | None,
    prompt: str,
) -> dict:
    _ensure_supported_pdf(content_type)

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

    result = await graph.ainvoke(state)
    pages = result.get("ocr_pages", [])
    return {
        "pages": pages,
        "metadata": result.get("metadata", {}),
        "missing_fields": result.get("missing_fields", []),
        "page_count": len(pages),
    }
