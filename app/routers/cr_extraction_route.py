from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.responses import StreamingResponse

from app.services.cr_extraction import run_service, run_stream_service
from app.core.logger import set_log
from app.core.db import get_db
from sqlalchemy.orm import Session
from app.schemas.cr_extraction import CRExtractionRequest
from app.schemas.common import CommonResponse


router = APIRouter()

router_prefix = "/cr_extraction"


@router.post(f"{router_prefix}/extract", tags=["document"])
async def extract_document(
    payload: CRExtractionRequest = Body(...),
    db: Session = Depends(get_db),
) -> CommonResponse:
    set_log("cr_extraction endpoint called")
    try:
        result = await run_service(payload, db)
        set_log("CR extraction done")
        return CommonResponse(
            success=True,
            status_code=200,
            message="CR extraction completed successfully",
            data=result,
        )
    except ValueError as exc:
        set_log(f"ValueError in extract_document: {exc}", level="error")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        set_log(f"Exception in extract_document: {exc}", level="error")
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {exc}"
        ) from exc


@router.post(f"{router_prefix}/extract/stream", tags=["document"])
async def extract_document_stream(
    payload: CRExtractionRequest = Body(...),
    db: Session = Depends(get_db),
):
    set_log("cr_extraction stream endpoint called")
    try:
        stream = await run_stream_service(payload, db)
        return StreamingResponse(
            stream,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except ValueError as exc:
        set_log(f"ValueError in extract_document_stream: {exc}", level="error")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        set_log(f"Exception in extract_document_stream: {exc}", level="error")
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {exc}"
        ) from exc
