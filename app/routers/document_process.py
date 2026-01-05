import base64

import fitz  # PyMuPDF
import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.config import settings
from app.core.prompts import get_vlm_ocr_system_prompt

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

    system_prompt = (
        "Summarize the document clearly. " "Do not include analysis or reasoning steps."
    )

    try:
        page_images_b64 = page_images_b64[:10]
        async with httpx.AsyncClient(timeout=300.0, trust_env=False) as client:
            chat_url = f"{settings.ollama_base_url}/api/chat"
            generate_url = f"{settings.ollama_base_url}/api/generate"

            print(settings.ollama_model)

            page_results: list[dict] = []

            for page_index, image_b64 in enumerate(page_images_b64, start=1):
                payload = {
                    "model": settings.ollama_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": f"Page {page_index}: {prompt}",
                            "images": [image_b64],
                        },
                    ],
                    "stream": False,
                }

                response = await client.post(chat_url, json=payload)

                if response.status_code == 404:
                    generate_payload = {
                        "model": settings.ollama_model,
                        "options": {"reasoning": False},
                        "prompt": f"{system_prompt} Page {page_index}: {prompt}",
                        "images": [image_b64],
                        "stream": False,
                    }
                    response = await client.post(generate_url, json=generate_payload)

                response.raise_for_status()
                page_results.append(
                    {
                        "page": page_index,
                        "ollama": response.json(),
                    }
                )
    except httpx.HTTPStatusError as exc:
        detail = f"Ollama request failed: {exc}"
        if exc.response is not None:
            detail = f"{detail} | response: {exc.response.text}"
        raise HTTPException(status_code=502, detail=detail) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502, detail=f"Ollama request failed: {exc}"
        ) from exc

    return {"pages": page_results, "page_count": len(page_results)}
