from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services.multimodal_extraction.service import run_service
from app.core.logger import set_log

router = APIRouter()

router_prefix = "/multimodal_extraction"


@router.post(f"{router_prefix}/process", tags=["document"])
async def process_document(
    pdf: UploadFile = File(...),
    prompt: str = Form("Describe the document"),
):
    set_log("multimodal_extraction")
    pdf_bytes = await pdf.read()

    try:
        result = await run_service(pdf_bytes, pdf.content_type, prompt)

        set_log("Multimodal_extraction done", level="info")
        return result
    except ValueError as exc:
        set_log(f"ValueError in process_document: {exc}", level="error")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        set_log(f"Exception in process_document: {exc}", level="error")
        raise HTTPException(
            status_code=502, detail=f"VLLM request failed: {exc}"
        ) from exc
