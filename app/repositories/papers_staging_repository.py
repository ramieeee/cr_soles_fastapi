from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, union_all, func
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
    latest_idx_per_paper = (
        select(
            PapersStaging.idx.label("idx"),
            func.row_number()
            .over(
                partition_by=PapersStaging.id,
                order_by=PapersStaging.idx.desc(),
            )
            .label("rn"),
        )
        .where(
            PapersStaging.is_approved.is_(False),
            PapersStaging.id.isnot(None),
        )
        .subquery()
    )

    selected_idxs = union_all(
        select(latest_idx_per_paper.c.idx).where(latest_idx_per_paper.c.rn == 1),
        select(PapersStaging.idx).where(
            PapersStaging.is_approved.is_(False),
            PapersStaging.id.is_(None),
        ),
    ).subquery()

    query = (
        select(PapersStaging)
        .join(selected_idxs, PapersStaging.idx == selected_idxs.c.idx)
        .order_by(PapersStaging.idx.desc())
        .offset(int(offset))
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
    ingestion_timestamp: datetime | None = None,
    is_approved: bool | None = None,
    approval_timestamp: Any | None = None,
) -> PapersStaging:
    paper_staging = PapersStaging(
        id=paper_id,
        title=title,
        authors=authors or [],
        journal=journal,
        year=year,
        abstract=abstract,
        pdf_url=pdf_url,
        ingestion_source=ingestion_source,
        embedding=embedding,
    )

    if ingestion_timestamp is not None:
        paper_staging.ingestion_timestamp = ingestion_timestamp
    if is_approved is not None:
        paper_staging.is_approved = is_approved
    if approval_timestamp is not None:
        paper_staging.approval_timestamp = approval_timestamp

    db.add(paper_staging)
    db.flush()
    return paper_staging


def get_papers_staging_by_idx(
    db: Session,
    *,
    idx: int,
) -> PapersStaging | None:
    return db.get(PapersStaging, idx)


def get_papers_staging_by_paper_id(
    db: Session,
    *,
    paper_id: UUID,
) -> PapersStaging | None:
    stmt = (
        select(PapersStaging)
        .where(PapersStaging.id == paper_id)
        .order_by(PapersStaging.idx.desc())
    )
    return db.execute(stmt).scalars().first()


def update_papers_staging_fields(
    db: Session,
    *,
    item: PapersStaging,
    fields: dict,
) -> PapersStaging:
    for key, value in fields.items():
        setattr(item, key, value)
    db.flush()
    return item


def _get_papers_staging(db: Session, identifier: str) -> PapersStaging | None:
    if identifier.isdigit():
        return db.get(PapersStaging, int(identifier))
    try:
        value = UUID(identifier)
    except ValueError:
        return None
    stmt = (
        select(PapersStaging)
        .where(PapersStaging.id == value)
        .order_by(PapersStaging.idx.desc())
    )
    return db.execute(stmt).scalars().first()
