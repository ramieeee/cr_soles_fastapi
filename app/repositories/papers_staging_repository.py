from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy import literal
from typing import Sequence, Any

from app.models.papers_staging import PapersStaging


def find_similar_papers(
    db: Session,
    *,
    embedding: Sequence[float],
    limit: int = 10,
    min_similarity: float | None = None,
) -> list[dict[str, Any]]:
    # 핵심: embedding을 문자열로 만들지 말고, "그대로" 바인딩
    embedding_vector = list(map(float, embedding))
    distance = PapersStaging.embedding.cosine_distance(embedding_vector)
    similarity = (literal(1.0) - distance).label("similarity")

    query = (
        select(
            PapersStaging.id,
            PapersStaging.title,
            PapersStaging.authors,
            PapersStaging.journal,
            PapersStaging.year,
            PapersStaging.abstract,
            PapersStaging.pdf_url,
            PapersStaging.ingestion_source,
            PapersStaging.ingestion_timestamp,
            similarity,
        )
        .where(PapersStaging.embedding.isnot(None))
        .order_by(distance)
        .limit(int(limit))
    )

    if min_similarity is not None:
        query = query.where(similarity >= float(min_similarity))

    result = db.execute(query)
    return [dict(row) for row in result.mappings().all()]


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
