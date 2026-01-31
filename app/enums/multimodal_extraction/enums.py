from enum import Enum


class VllmTaskType(str, Enum):
    OCR = "ocr"
    bibliographic_info_EXTRACTION = "bibliographic_info_extraction"
    EMBEDDING = "embedding"
    CHAT = "chat"
