from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.prompts import get_metadata_extraction_prompt
from app.langgraph.multimodal_extraction.state import DocumentState
from app.clients.ollama_client import OllamaClient


REQUIRED_FIELDS = ("title", "authors", "journal", "year", "abstract")


def _extract_json(text: str) -> dict[str, Any] | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    snippet = text[start : end + 1]
    try:
        return json.loads(snippet)
    except json.JSONDecodeError:
        return None


def _normalize_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    title = metadata.get("title") or ""
    journal = metadata.get("journal") or ""
    abstract = metadata.get("abstract") or ""

    authors = metadata.get("authors") or []
    if isinstance(authors, str):
        authors = [author.strip() for author in authors.split(",") if author.strip()]
    if not isinstance(authors, list):
        authors = []

    year = metadata.get("year")
    if isinstance(year, str):
        year = year.strip()
        if year.isdigit():
            year = int(year)
    if not isinstance(year, int):
        year = None

    normalized["title"] = str(title).strip()
    normalized["authors"] = authors
    normalized["journal"] = str(journal).strip()
    normalized["year"] = year
    normalized["abstract"] = str(abstract).strip()

    return normalized


def _find_missing_fields(metadata: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    if not metadata.get("title"):
        missing.append("title")
    if not metadata.get("authors"):
        missing.append("authors")
    if not metadata.get("journal"):
        missing.append("journal")
    if not isinstance(metadata.get("year"), int):
        missing.append("year")
    if not metadata.get("abstract"):
        missing.append("abstract")
    return missing


async def extract_metadata(state: DocumentState) -> DocumentState:
    ocr_text = state.get("ocr_text") or ""
    retry_focus = state.get("retry_focus") or []
    prompt = get_metadata_extraction_prompt(ocr_text, retry_focus)

    ollama_client = OllamaClient()
    async with httpx.AsyncClient(timeout=300.0, trust_env=False) as client:
        response_payload = await ollama_client.generate_text(client, f"{prompt}")

    raw_text = str(response_payload.get("response", "")).strip()
    metadata_json = _extract_json(raw_text) or {}
    metadata = _normalize_metadata(metadata_json)
    missing_fields = _find_missing_fields(metadata)

    return {
        "metadata": metadata,
        "metadata_raw": raw_text,
        "missing_fields": missing_fields,
    }


def prepare_retry(state: DocumentState) -> DocumentState:
    attempts = int(state.get("attempts") or 0) + 1
    retry_focus = list(state.get("missing_fields") or [])
    return {"attempts": attempts, "retry_focus": retry_focus}


def should_retry(state: DocumentState) -> str:
    missing_fields = state.get("missing_fields") or []
    attempts = int(state.get("attempts") or 0)
    max_attempts = int(state.get("max_attempts") or 1)
    if missing_fields and attempts < max_attempts:
        return "retry"
    return "end"
