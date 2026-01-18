from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.prompts import (
    get_metadata_determine_completion_prompt,
    get_metadata_extraction_prompt,
)
from app.langgraph.multimodal_extraction.state import DocumentState
from app.clients.vllm_client import VllmClient

from app.core.logger import set_log


REQUIRED_FIELDS = ("title", "authors", "journal", "year", "abstract")


def _extract_json(text: str) -> dict[str, Any] | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    snippet = text[start : end + 1]
    try:
        set_log(f"Extracting JSON snippet: {snippet}")
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


def _merge_metadata(
    base: dict[str, Any] | None,
    incoming: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(base or {})
    for key in ("title", "journal"):
        value = incoming.get(key)
        if value:
            merged[key] = value

    if incoming.get("authors"):
        merged["authors"] = incoming["authors"]

    if isinstance(incoming.get("year"), int):
        merged["year"] = incoming["year"]

    incoming_abstract = incoming.get("abstract") or ""
    current_abstract = merged.get("abstract") or ""
    if incoming_abstract and len(incoming_abstract) >= len(current_abstract):
        merged["abstract"] = incoming_abstract

    return _normalize_metadata(merged)


def _collect_ocr_text(ocr_pages: list[dict], max_pages: int) -> str:
    snippets: list[str] = []
    for page in ocr_pages[:max_pages]:
        text = page.get("text")
        if isinstance(text, str) and text.strip():
            snippets.append(text.strip())
    return "\n\n".join(snippets)


def _is_complete_response(text: str) -> bool:
    normalized = text.strip().lower()
    return normalized.startswith("complete")


async def extract_metadata(state: DocumentState) -> DocumentState:
    set_log("Extract_metadata node")
    ocr_pages = state.get("ocr_pages") or []
    retry_focus = state.get("retry_focus") or []

    # Same rationale as OCR node: VllmClient.chat() uses its own timeout.
    vllm_client = VllmClient(port="", timeout_s=300.0)
    metadata: dict[str, Any] = _normalize_metadata(state.get("metadata") or {})
    raw_text = ""
    metadata_complete = False

    async with httpx.AsyncClient(timeout=300.0, trust_env=False) as client:
        for page_count in range(1, len(ocr_pages) + 1):
            ocr_text = _collect_ocr_text(ocr_pages, page_count)
            if not ocr_text:
                continue

            prompt = get_metadata_extraction_prompt(ocr_text, retry_focus)
            response_payload = await vllm_client.chat(
                client=client,
                system_prompt=prompt,
                user_prompt="Extract the bibliographic metadata",
            )

            raw_text = (
                response_payload.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            raw_text = str(raw_text).strip()
            metadata_json = _extract_json(raw_text) or {}
            metadata = _merge_metadata(metadata, _normalize_metadata(metadata_json))

            completion_prompt = get_metadata_determine_completion_prompt()
            completion_payload = await vllm_client.chat(
                client=client,
                system_prompt=str(completion_prompt),
                user_prompt=(
                    "OCR TEXT:\n"
                    f"{ocr_text}\n\n"
                    "METADATA JSON:\n"
                    f"{json.dumps(metadata, ensure_ascii=True)}"
                ),
            )
            completion_text = (
                completion_payload.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            metadata_complete = _is_complete_response(str(completion_text))
            if metadata_complete:
                break

    missing_fields = _find_missing_fields(metadata)
    if not metadata_complete and not missing_fields:
        missing_fields = ["incomplete"]

    return {
        "metadata": metadata,
        "metadata_raw": raw_text,
        "missing_fields": missing_fields,
        "metadata_complete": metadata_complete,
    }


def prepare_retry(state: DocumentState) -> DocumentState:
    attempts = int(state.get("attempts") or 0) + 1
    retry_focus = list(state.get("missing_fields") or [])
    return {"attempts": attempts, "retry_focus": retry_focus}


def should_retry(state: DocumentState) -> str:
    metadata_complete = bool(state.get("metadata_complete"))
    attempts = int(state.get("attempts") or 0)
    max_attempts = int(state.get("max_attempts") or 1)
    if not metadata_complete and attempts < max_attempts:
        set_log("Metadata incomplete, will retry.")
        return "retry"
    set_log("Metadata extraction complete or max attempts reached, ending.")
    return "end"
