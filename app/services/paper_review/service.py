from __future__ import annotations

import json
from uuid import UUID
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.logger import set_log
from app.enums.paper_review.enums import ReviewTableType
from app.models.papers import Papers
from app.models.papers_staging import PapersStaging
from app.repositories.papers_repository import (
    list_papers,
    get_paper_by_id,
    update_paper_fields,
)
from app.repositories.papers_staging_repository import (
    list_papers_staging,
    get_papers_staging_by_idx,
    get_papers_staging_by_paper_id,
    create_papers_staging,
    update_papers_staging_fields,
)
from app.repositories.papers_repository import (
    create_paper,
)

ALLOWED_EDIT_KEYS = (
    "title",
    "authors",
    "journal",
    "year",
    "abstract",
    "pdf_url",
    "ingestion_source",
)


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


def _normalize_edit_payload(payload: dict) -> dict:
    cleaned: dict = {}
    for key in ALLOWED_EDIT_KEYS:
        if key not in payload:
            continue
        value = payload.get(key)
        if key == "authors":
            if value is None:
                cleaned[key] = []
            elif isinstance(value, str):
                cleaned[key] = [item.strip() for item in value.split(",") if item]
            elif isinstance(value, list):
                cleaned[key] = [
                    str(item).strip() for item in value if str(item).strip()
                ]
        elif key == "year":
            if value is None or value == "":
                cleaned[key] = None
            elif isinstance(value, int):
                cleaned[key] = value
            elif isinstance(value, str) and value.strip().isdigit():
                cleaned[key] = int(value.strip())
            else:
                raise ValueError("Invalid year value.")
        else:
            cleaned[key] = value
    return cleaned


def _parse_payload(payload: str | dict) -> dict:
    if isinstance(payload, dict):
        return payload
    if not payload:
        return {}
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError("payload must be valid JSON.") from exc


def _get_papers_staging(db: Session, identifier: str) -> PapersStaging | None:
    if identifier.isdigit():
        return get_papers_staging_by_idx(db, idx=int(identifier))
    try:
        value = UUID(identifier)
    except ValueError:
        return None
    return get_papers_staging_by_paper_id(db, paper_id=value)


def approve_paper_staging(db: Session, idx: int) -> PapersStaging:
    with db.begin_nested():
        item = get_papers_staging_by_idx(db, idx=idx)
        if item is None:
            raise ValueError("Staging paper not found.")
        if item.is_approved:
            raise ValueError("Staging paper is already approved.")

        paper_fields = {
            "title": item.title,
            "authors": item.authors,
            "journal": item.journal,
            "year": item.year,
            "abstract": item.abstract,
            "pdf_url": item.pdf_url,
            "ingestion_source": item.ingestion_source,
        }

        if item.id is None:
            paper = create_paper(db, **paper_fields)
            paper_id = paper.id
        else:
            paper = get_paper_by_id(db, paper_id=item.id)
            if paper is None:
                raise ValueError("Referenced paper not found.")
            paper = update_paper_fields(db, item=paper, fields=paper_fields)
            paper_id = paper.id

        staging_fields = {
            "is_approved": True,
            "approval_timestamp": func.now(),
        }
        if item.id is None:
            staging_fields["id"] = paper_id

        return update_papers_staging_fields(
            db,
            item=item,
            fields=staging_fields,
        )


def edit_paper_staging(db: Session, idx: int, fields: dict) -> PapersStaging:
    item = get_papers_staging_by_idx(db, idx=idx)
    if item is None:
        raise ValueError("Staging paper not found.")
    if item.is_approved:
        raise ValueError("Cannot edit an approved staging paper.")
    return update_papers_staging_fields(db, item=item, fields=fields)


def update_paper_staging(
    db: Session,
    *,
    identifier: str,
    payload: str | dict,
) -> PapersStaging:
    original = _get_papers_staging(db, identifier)
    if original is None:
        raise ValueError("Staging paper not found.")
    if original.is_approved:
        raise ValueError("Cannot edit an approved staging paper.")

    cleaned = _normalize_edit_payload(_parse_payload(payload))
    if not cleaned:
        raise ValueError("No editable fields provided.")

    with db.begin_nested():
        # 1) 원본 + 수정 payload를 합친 "수정본"으로 papers 생성/업데이트
        edited_fields = {
            "title": cleaned.get("title", original.title),
            "authors": cleaned.get("authors", original.authors),
            "journal": cleaned.get("journal", original.journal),
            "year": cleaned.get("year", original.year),
            "abstract": cleaned.get("abstract", original.abstract),
            "pdf_url": cleaned.get("pdf_url", original.pdf_url),
            "ingestion_source": cleaned.get(
                "ingestion_source", original.ingestion_source
            ),
            "embedding": original.embedding,
        }

        if original.id is None:
            paper = create_paper(db, **edited_fields)
        else:
            paper = get_paper_by_id(db, paper_id=original.id)
            if paper is None:
                raise ValueError("Referenced paper not found.")
            paper = update_paper_fields(db, item=paper, fields=edited_fields)

        # 2) papers_id를 가진 papers_staging row 생성 (로깅 목적)
        log_row = create_papers_staging(
            db,
            paper_id=paper.id,
            title=edited_fields["title"],
            authors=edited_fields["authors"],
            journal=edited_fields["journal"],
            year=edited_fields["year"],
            abstract=edited_fields["abstract"],
            pdf_url=edited_fields["pdf_url"],
            ingestion_source=edited_fields["ingestion_source"],
            embedding=edited_fields["embedding"],
        )
        update_papers_staging_fields(
            db,
            item=log_row,
            fields={
                "is_approved": True,
                "approval_timestamp": func.now(),
            },
        )

        # 3) 기존 원본 idx row도 승인 처리해서 fetch 대상에서 제외
        return update_papers_staging_fields(
            db,
            item=original,
            fields={
                "id": paper.id,
                "is_approved": True,
                "approval_timestamp": func.now(),
            },
        )


def update_paper(
    db: Session,
    *,
    identifier: str,
    payload: str | dict,
) -> Papers:
    try:
        paper_id = UUID(identifier)
    except ValueError as exc:
        raise ValueError("Paper id must be a UUID.") from exc

    item = get_paper_by_id(db, paper_id=paper_id)
    if item is None:
        raise ValueError("Paper not found.")

    cleaned = _normalize_edit_payload(_parse_payload(payload))
    if not cleaned:
        raise ValueError("No editable fields provided.")

    return update_paper_fields(db, item=item, fields=cleaned)
