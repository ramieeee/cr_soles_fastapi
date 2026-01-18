vlm_ocr_system_prompt = """
    Extract the visible content from the document image.

    Output MUST be valid JSON with exactly these keys:
    - "text"
    - "tables"
    - "images"

    Rules:
    - Do NOT explain or analyse.
    - Do NOT add extra keys.
    - Always include all three keys.
    - Return JSON only. Do not use markdown code fences (no ```).


    "text":
    - A single string of all visible text in reading order.
    - Keep line breaks.

    "tables":
    - A list of tables.
    - Each table:
    { "headers": [...], "rows": [...] }
    - If no tables, output [].

    "images":
    - A list of short descriptions of figures, charts, or diagrams.
    - If none, output [].
"""


def get_vlm_ocr_system_prompt() -> str:
    return vlm_ocr_system_prompt


metadata_extraction_system_prompt = """
    Extract bibliographic metadata from the OCR text.
    Return ONLY valid JSON with keys: title, authors, journal, year, abstract.
    Use empty string for missing text fields, empty array for authors, and null for year.
"""


def get_metadata_extraction_prompt(ocr_text: str, retry_focus: list[str] | None) -> str:
    focus = ""
    if retry_focus:
        focus = f"Focus on missing fields: {', '.join(retry_focus)}.\n"
    return (
        f"{metadata_extraction_system_prompt}\n"
        f"{focus}"
        "OCR TEXT:\n"
        f"{ocr_text}\n"
    )
