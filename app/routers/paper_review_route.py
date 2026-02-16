from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Depends

from app.services.multimodal_extraction.service import run_service
from app.core.logger import set_log
from app.core.db import get_db
from sqlalchemy.orm import Session


router = APIRouter()

router_prefix = "/paper_review"


@router.post(f"{router_prefix}/fetch/staging_papers", tags=["document"])
async def fetch_all_papers_staging(
    offset: int = Form(0),
    limit: int = Form(10),
    db: Session = Depends(get_db),
):
    set_log("fetch_all_papers_staging")
    try:
        set_log("Multimodal_extraction done", level="info")
        return result
    except ValueError as exc:
        set_log(f"ValueError in fetch_all_papers_staging: {exc}", level="error")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        set_log(f"Exception in fetch_all_papers_staging: {exc}", level="error")
        raise HTTPException(
            status_code=502, detail=f"VLLM request failed: {exc}"
        ) from exc
