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
