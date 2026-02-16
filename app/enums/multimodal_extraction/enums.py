from enum import Enum


class VllmTaskType(str, Enum):
    OCR = "ocr"
    BIBLIOGRAPHIC_INFO_EXTRACTION = "bibliographic_info_extraction"
    EMBEDDING = "embedding"
    CHAT = "chat"
