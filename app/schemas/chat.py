from pydantic import BaseModel, Field


class Citation(BaseModel):
    source_id: str
    source_type: str
    label: str
    start: float | None = None
    page: int | None = None
    section: str | None = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = []
    answerable: bool = True
