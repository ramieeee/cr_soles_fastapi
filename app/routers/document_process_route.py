import base64

import fitz  # PyMuPDF
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.langgraph import get_document_graph

router = APIRouter()

router_prefix = "/document"


@router.post(f"{router_prefix}/process", tags=["document"])
async def process_document(
    pdf: UploadFile = File(...),
    prompt: str = Form("Describe the document"),
):
    if not pdf.content_type or pdf.content_type not in {
        "application/pdf",
        "application/x-pdf",
        "application/acrobat",
        "applications/vnd.pdf",
        "text/pdf",
        "text/x-pdf",
    }:
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    pdf_bytes = await pdf.read()

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid PDF: {exc}") from exc

    page_images_b64: list[str] = []
    try:
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            png_bytes = pix.tobytes("png")
            page_images_b64.append(base64.b64encode(png_bytes).decode("ascii"))
    finally:
        doc.close()

    if not page_images_b64:
        raise HTTPException(status_code=400, detail="PDF has no pages.")

    graph = get_document_graph()
    state = {
        "page_images_b64": page_images_b64,
        "prompt": prompt,
        "attempts": 0,
        "max_attempts": 1,
    }

    try:
        result = await graph.ainvoke(state)
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"Ollama request failed: {exc}"
        ) from exc

    pages = result.get("ocr_pages", [])
    return {
        "pages": pages,
        "metadata": result.get("metadata", {}),
        "missing_fields": result.get("missing_fields", []),
        "page_count": len(pages),
    }
