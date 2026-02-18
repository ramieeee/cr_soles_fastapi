from fastapi import APIRouter, Depends, HTTPException, Query

from app.services.paper_review.service import (
    fetch_review_papers,
    update_staging_paper as update_staging_paper_service,
    update_paper,
)
from app.core.logger import set_log
from app.core.db import get_db
from sqlalchemy.orm import Session
from app.enums.paper_review.enums import ReviewTableType


router = APIRouter()

router_prefix = "/paper_review"


@router.get(f"{router_prefix}/fetch/papers", tags=["document"])
async def fetch_all_papers_staging(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=1000),
    table_type: ReviewTableType = Query(ReviewTableType.PAPERS_STAGING),
    db: Session = Depends(get_db),
):
    set_log("fetch_all_papers_staging")
    try:
        return fetch_review_papers(
            db,
            offset=offset,
            limit=limit,
            table_type=table_type,
        )
    except ValueError as exc:
        set_log(f"ValueError in fetch_all_papers_staging: {exc}", level="error")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        set_log(f"Exception in fetch_all_papers_staging: {exc}", level="error")
        raise HTTPException(
            status_code=502, detail=f"Paper review fetch failed: {exc}"
        ) from exc


@router.post(f"{router_prefix}/update/staging_paper", tags=["document"])
async def update_staging_paper(
    id: str = Query(...),
    payload: str = Query(...),
    db: Session = Depends(get_db),
):
    set_log("update_staging_paper")
    try:
        updated = update_staging_paper_service(db, identifier=id, payload=payload)
        return {"id": updated.idx}
    except ValueError as exc:
        set_log(f"ValueError in update_staging_paper: {exc}", level="error")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        set_log(f"Exception in update_staging_paper: {exc}", level="error")
        raise HTTPException(
            status_code=502, detail=f"Paper review update failed: {exc}"
        ) from exc


@router.post(f"{router_prefix}/update/paper", tags=["document"])
async def update_paper_route(
    id: str = Query(...),
    payload: str = Query(...),
    db: Session = Depends(get_db),
):
    set_log("update_paper")
    try:
        updated = update_paper(db, identifier=id, payload=payload)
        return {"id": str(updated.id)}
    except ValueError as exc:
        set_log(f"ValueError in update_paper: {exc}", level="error")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        set_log(f"Exception in update_paper: {exc}", level="error")
        raise HTTPException(
            status_code=502, detail=f"Paper review update failed: {exc}"
        ) from exc
