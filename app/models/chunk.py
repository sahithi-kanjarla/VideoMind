from pydantic import BaseModel, Field


class ContentChunk(BaseModel):
    chunk_id: str
    source_id: str
    text: str

    start: float | None = None
    end: float | None = None

    page: int | None = None
    section: str | None = None
    paragraph_index: int | None = None

    metadata: dict = Field(default_factory=dict)


TranscriptChunk = ContentChunk
