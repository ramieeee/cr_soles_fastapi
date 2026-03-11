from __future__ import annotations

import json
from typing import Any


def parse_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in streamed response.")
    return json.loads(cleaned[start : end + 1])


def get_page_text(page_item: dict[str, Any]) -> str:
    return str(page_item.get("text") or "")


def normalize_evidence_list(
    evidence: list[dict[str, Any]] | None,
    pages_content: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not evidence:
        return []

    normalized: list[dict[str, Any]] = []
    page_lookup: dict[int, str] = {}
    for item in pages_content:
        page = item.get("page")
        if isinstance(page, int):
            page_lookup[page] = get_page_text(item)

    for item in evidence:
        if not isinstance(item, dict):
            continue

        page = item.get("page")
        quote = str(item.get("quote") or "").strip()
        if not isinstance(page, int) or not quote:
            continue

        page_text = page_lookup.get(page) or ""
        if quote not in page_text:
            continue

        normalized.append(
            {
                "page": page,
                "quote": quote,
            }
        )

    return normalized


def pick_relevant_pages(
    pages_content: list[dict[str, Any]],
    candidate: dict[str, Any],
    fallback_count: int = 3,
) -> list[dict[str, Any]]:

    keywords = []

    for key in (
        "target_population",
        "country_setting",
        "instrument_name",
        "scoring_method",
        "time_administration",
    ):
        value = candidate.get(key)
        if isinstance(value, str) and value and value != "not_detected":
            keywords.append(value.lower())

    for key in (
        "clinical_condition_tags",
        "detected_proxy_labels",
    ):
        value = candidate.get(key) or []
        if isinstance(value, list):
            keywords.extend(str(item).lower() for item in value if item)

    instrument_family = candidate.get("instrument_family")
    if isinstance(instrument_family, str):
        if instrument_family and instrument_family != "not_detected":
            keywords.append(instrument_family.lower())
    elif isinstance(instrument_family, list):
        keywords.extend(
            str(item).lower()
            for item in instrument_family
            if item and item != "not_detected"
        )

    scored_pages: list[tuple[int, dict[str, Any]]] = []
    for item in pages_content:
        text = get_page_text(item).lower()
        score = sum(1 for keyword in keywords if keyword and keyword in text)
        if score > 0:
            scored_pages.append((score, item))

    scored_pages.sort(key=lambda x: x[0], reverse=True)
    selected = [item for _, item in scored_pages[:fallback_count]]

    if selected:
        return selected
    return pages_content[:fallback_count]
