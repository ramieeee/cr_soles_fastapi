vlm_ocr_system_prompt = """
    Extract all texts, tables, and images from the document clearly.
    Your output should be structured in JSON format with the following keys: 'text', 'tables', and 'images'.
    Do not include any analysis or reasoning steps.
    
    # Example output:
    {
        "text": "Extracted text content here.",
        "tables": [
            {
                "headers": ["Header1", "Header2"],
                "rows": [
                    ["Row1Col1", "Row1Col2"],
                    ["Row2Col1", "Row2Col2"]
                ]
            }
        ],
        "images": [
            "image description in summary"
        ]
    }
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
