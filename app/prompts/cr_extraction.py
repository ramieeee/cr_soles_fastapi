from __future__ import annotations

import json
from typing import Any


def _build_pages_context(pages_content: list[dict[str, Any]], max_pages: int = 8) -> str:
    parts: list[str] = []
    for item in pages_content[:max_pages]:
        page = item.get("page")
        text = str(item.get("text") or "").strip()
        tables = item.get("tables") or []

        part = f"[PAGE {page}]"
        if text:
            part += f"\nTEXT:\n{text[:3000]}"
        if tables:
            part += f"\nTABLES:\n{json.dumps(tables, ensure_ascii=False)[:2000]}"
        parts.append(part)

    return "\n\n".join(parts)


def get_population_system_prompt() -> str:
    return """
You extract study population metadata for cognitive reserve papers.
Return JSON only. No markdown. No explanation.

Output schema:
{
  "population_summary": string,
  "target_population": string | null,
  "age_band": "young" | "middle" | "older" | "mixed" | null,
  "clinical_condition_tags": [string],
  "country_setting": string | null,
  "evidence": [string],
  "confidence": float
}

Rules:
- Use short, normalized values.
- If not found, use null or [].
- confidence must be between 0 and 1.
- evidence should contain short direct snippets or short table phrases.
""".strip()


def get_population_user_prompt(
    pages_content: list[dict[str, Any]],
    extra_instruction: str | None = None,
) -> str:
    context = _build_pages_context(pages_content)
    instruction = f"Additional instruction: {extra_instruction}\n\n" if extra_instruction else ""
    return (
        "Extract the study population information from the pages below.\n"
        "Prioritize Methods, Participants, Sample, and Table 1 style content.\n\n"
        f"{instruction}"
        f"{context}\n"
    )


def get_instrument_system_prompt() -> str:
    return """
You extract one primary cognitive reserve instrument or proxy set.
Return JSON only. No markdown. No explanation.

Output schema:
{
  "instrument_name": string | null,
  "instrument_family": "CRIq" | "CRQ" | "LEQ" | "NART" | "MWT-B" | "mCRS" | "CRASH" | "CR-interview" | "multi_proxy_custom" | "not_detected",
  "detected_proxy_labels": [string],
  "scoring_method": string | null,
  "time_administration": string | null,
  "evidence": [string],
  "confidence": float
}

Rules:
- Pick only one instrument family.
- If several are mentioned, choose the most clearly used cognitive reserve measure.
- If no named instrument exists but CR proxies are listed, use instrument_family="multi_proxy_custom".
- Use normalized proxy labels such as education, occupation, leisure, social, multilingualism, music, physical_activity, iq_proxy.
- confidence must be between 0 and 1.
""".strip()


def get_instrument_user_prompt(
    pages_content: list[dict[str, Any]],
    population: dict[str, Any] | None = None,
    extra_instruction: str | None = None,
) -> str:
    context = _build_pages_context(pages_content)
    population_text = json.dumps(population or {}, ensure_ascii=False)
    instruction = f"Additional instruction: {extra_instruction}\n" if extra_instruction else ""
    return (
        "Extract one primary cognitive reserve instrument or proxy set from the pages below.\n"
        "Prioritize questionnaire names, assessed CR proxies, cognitive scales, and scoring/time fields.\n"
        f"{instruction}"
        f"Population context: {population_text}\n\n"
        f"{context}\n"
    )
