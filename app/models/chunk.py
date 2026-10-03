from pydantic import BaseModel, Field


class TranscriptChunk(BaseModel):
    chunk_id: str
    source_id: str
    text: str

    start: float | None = None
    end: float | None = None

    metadata: dict = Field(default_factory=dict)