from enum import Enum


class ReviewTableType(str, Enum):
    PAPERS_STAGING = "papers_staging"
    PAPERS = "papers"
