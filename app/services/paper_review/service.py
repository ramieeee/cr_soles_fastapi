from __future__ import annotations

import json
from uuid import UUID
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
    update_papers_staging_fields,
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
                cleaned[key] = [str(item).strip() for item in value if str(item).strip()]
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


def update_staging_paper(
    db: Session,
    *,
    identifier: str,
    payload: str | dict,
) -> PapersStaging:
    item = _get_papers_staging(db, identifier)
    if item is None:
        raise ValueError("Staging paper not found.")

    cleaned = _normalize_edit_payload(_parse_payload(payload))
    if not cleaned:
        raise ValueError("No editable fields provided.")

    return update_papers_staging_fields(db, item=item, fields=cleaned)


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
