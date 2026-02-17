from fastapi import APIRouter, Depends, HTTPException, Query

from app.services.paper_review.service import fetch_review_papers
from app.core.logger import set_log
from app.core.db import get_db
from sqlalchemy.orm import Session
from app.enums.paper_review.enums import ReviewTableType


router = APIRouter()

router_prefix = "/paper_review"


@router.get(f"{router_prefix}/fetch/papers", tags=["document"])
async def fetch_all_papers_staging(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=500),
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
