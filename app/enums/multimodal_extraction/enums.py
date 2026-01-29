from enum import Enum


class VllmTaskType(str, Enum):
    OCR = "ocr"
    BIBLIOGRAPHIC_INFORMATION_EXTRACTION = "bibliographic_information_extraction"
    EMBEDDING = "embedding"
    CHAT = "chat"
