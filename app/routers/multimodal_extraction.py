from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services.multimodal_extraction.service import process_document_bytes

router = APIRouter()

router_prefix = "/multimodal_extraction"


@router.post(f"{router_prefix}/process", tags=["document"])
async def process_document(
    pdf: UploadFile = File(...),
    prompt: str = Form("Describe the document"),
):
    pdf_bytes = await pdf.read()

    try:
        return await process_document_bytes(pdf_bytes, pdf.content_type, prompt)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Ollama request failed: {exc}") from exc
