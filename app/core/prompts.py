vlm_ocr_system_prompt = """
    # Task:
    Extract the visible content from the document image.

    # Output Format:
    Output MUST be valid JSON with exactly these keys:
    - "text"
    - "tables"
    - "images"

    # Rules:
    - Do NOT explain or analyse.
    - Do NOT add extra keys.
    - Always include all three keys.
    - Return JSON only. Do not use markdown code fences (no ```).

    # Key Descriptions:
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
    
    # Example Output:
    {
        "text": "Full text content here...",
        "tables": [
            {
                "headers": ["Header1", "Header2"],
                "rows": [["Row1Col1", "Row1Col2"], ["Row2Col1", "Row2Col2"]]
            }
        ],
        "images": ["Description of image 1", "Description of image 2"]
    }
"""


def get_vlm_ocr_system_prompt() -> str:
    return vlm_ocr_system_prompt


bibliographic_info_extraction_system_prompt = """
    Extract bibliographic information from the OCR text.
    Return ONLY valid JSON with keys: title, authors, journal, year, abstract, pdf_url.
    Use empty string for missing text fields, empty array for authors, and null for year.
"""


def get_bibliographic_info_extraction_prompt(
    ocr_text: str, retry_focus: list[str] | None
) -> str:
    focus = ""
    if retry_focus:
        focus = f"Focus on missing fields: {', '.join(retry_focus)}.\n"
    return (
        f"{bibliographic_info_extraction_system_prompt}\n"
        f"{focus}"
        "OCR TEXT:\n"
        f"{ocr_text}\n"
    )


bibliographic_info_determine_completion_prompt = """
    # Task:
    Determine if the extracted bibliographic information is complete.
    
    # Focus:
    Pay special attention to commonly missed or incomplete fields.
    
    # Criteria for Completeness:
    - "title" is non-empty.
    - "authors" has at least one author.
    - "journal" is non-empty.
    - "year" is correct according to the document.
    - "abstract" is not cut or incomplete.
    - "pdf_url" is present if it can be extracted from the OCR text.
    
    # Output:
    Return ONLY "complete" or "incomplete".
"""


def get_bibliographic_info_determine_completion_prompt() -> str:
    return bibliographic_info_determine_completion_prompt
