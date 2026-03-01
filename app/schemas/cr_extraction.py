from typing import Any

from pydantic import AliasChoices, BaseModel, Field, model_validator


class CRExtractionRequest(BaseModel):
    paper_id: str | None = Field(
        default=None, validation_alias=AliasChoices("paper_id", "id")
    )
    pages_content: list[dict[str, Any]] | None = None
    stream_prompt: str | None = None

    @model_validator(mode="after")
    def validate_source(self) -> "CRExtractionRequest":
        if self.paper_id or self.pages_content:
            return self
        raise ValueError("Either paper_id or pages_content must be provided.")
