from pydantic import AliasChoices, BaseModel, Field


class CRExtractionRequest(BaseModel):
    paper_id: str = Field(validation_alias=AliasChoices("paper_id", "id"))
    stream_prompt: str | None = None
