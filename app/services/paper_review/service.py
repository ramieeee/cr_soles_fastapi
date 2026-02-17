from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.logger import set_log
from app.enums.paper_review.enums import ReviewTableType
from app.models.papers import Papers
from app.models.papers_staging import PapersStaging
from app.repositories.papers_repository import list_papers
from app.repositories.papers_staging_repository import list_papers_staging


def _serialize_papers_staging(item: PapersStaging) -> dict:
    return {
        "idx": item.idx,
        "paper_id": item.id,
        "is_approved": item.is_approved,
        "approval_timestamp": item.approval_timestamp,
        "title": item.title,
        "authors": item.authors,
        "journal": item.journal,
        "year": item.year,
        "abstract": item.abstract,
        "pdf_url": item.pdf_url,
        "ingestion_source": item.ingestion_source,
        "ingestion_timestamp": item.ingestion_timestamp,
    }


def _serialize_papers(item: Papers) -> dict:
    return {
        "id": item.id,
        "title": item.title,
        "authors": item.authors,
        "journal": item.journal,
        "year": item.year,
        "abstract": item.abstract,
        "pdf_url": item.pdf_url,
        "ingestion_source": item.ingestion_source,
        "ingestion_timestamp": item.ingestion_timestamp,
    }


def fetch_review_papers(
    db: Session,
    *,
    offset: int,
    limit: int,
    table_type: ReviewTableType,
) -> dict:
    set_log(
        f"fetch_review_papers: table_type={table_type} offset={offset} limit={limit}"
    )

    if table_type == ReviewTableType.PAPERS_STAGING:
        items = list_papers_staging(db, offset=offset, limit=limit)
        payload = [_serialize_papers_staging(item) for item in items]
    elif table_type == ReviewTableType.PAPERS:
        items = list_papers(db, offset=offset, limit=limit)
        payload = [_serialize_papers(item) for item in items]
    else:
        raise ValueError(f"Unsupported table_type: {table_type}")

    return {
        "table_type": table_type,
        "offset": offset,
        "limit": limit,
        "items": payload,
    }
