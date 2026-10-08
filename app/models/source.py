from pydantic import BaseModel, Field
from typing import Literal


SourceType = Literal[
    "youtube",
    "video",
    "audio",
    "pdf",
    "docx",
    "text",
    "markdown",
    "paste",
]


class ContentSegment(BaseModel):
    text: str
    start: float | None = None
    end: float | None = None
    speaker: str | None = None
    page: int | None = None
    section: str | None = None
    paragraph_index: int | None = None


TranscriptSegment = ContentSegment


class NormalizedSource(BaseModel):
    source_id: str
    source_type: SourceType
    title: str | None = None
    uri: str | None = None
    language: str | None = None
    segments: list[ContentSegment] = Field(default_factory=list)
