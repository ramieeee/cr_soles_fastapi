from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.papers_staging import PapersStaging


def list_papers_staging(
    db: Session,
    *,
    offset: int = 0,
    limit: int = 100,
) -> list[PapersStaging]:
    query = (
        select(PapersStaging)
        .offset(int(offset))
        .where(PapersStaging.is_approved.is_(False))
        .limit(int(limit))
    )
    result = db.execute(query)
    return result.scalars().all()


def create_papers_staging(
    db: Session,
    *,
    paper_id: UUID | None = None,
    title: str,
    authors: list[str] | None = None,
    journal: str | None = None,
    year: int | None = None,
    abstract: str | None = None,
    pdf_url: str | None = None,
    ingestion_source: str | None = None,
    embedding: list[float] | None = None,
) -> PapersStaging:
    paper_staging = PapersStaging(
        title=title,
        authors=authors or [],
        journal=journal,
        year=year,
        abstract=abstract,
        pdf_url=pdf_url,
        ingestion_source=ingestion_source,
        embedding=embedding,
    )
    if paper_id is not None:
        paper_staging.id = paper_id
    db.add(paper_staging)
    db.flush()
    return paper_staging
