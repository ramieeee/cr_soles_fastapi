from __future__ import annotations

from typing import Any, Sequence

from sqlalchemy import select, literal
from sqlalchemy.orm import Session


from app.models.papers import Papers


def list_papers(
    db: Session,
    *,
    offset: int = 0,
    limit: int = 100,
) -> list[Papers]:
    query = select(Papers).offset(int(offset)).limit(int(limit))
    result = db.execute(query)
    return result.scalars().all()


def create_paper(
    db: Session,
    *,
    title: str,
    authors: list[str] | None = None,
    journal: str | None = None,
    year: int | None = None,
    abstract: str | None = None,
    pdf_url: str | None = None,
    ingestion_source: str | None = None,
    embedding: list[float] | None = None,
) -> Papers:
    paper = Papers(
        title=title,
        authors=authors or [],
        journal=journal,
        year=year,
        abstract=abstract,
        pdf_url=pdf_url,
        ingestion_source=ingestion_source,
        embedding=embedding,
    )
    db.add(paper)
    db.flush()
    return paper
