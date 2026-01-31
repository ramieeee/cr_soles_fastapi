from typing import TypedDict


class DocumentState(TypedDict, total=False):
    page_images_b64: list[str]
    prompt: str
    ocr_pages: list[dict]
    bibliographic_info: dict
    bibliographic_info_raw: str
    missing_fields: list[str]
    retry_focus: list[str]
    attempts: int
    max_attempts: int
    bibliographic_info_complete: bool
    embedding: list[float]
