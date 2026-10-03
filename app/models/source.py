from pydantic import BaseModel, Field
from typing import Literal


SourceType = Literal[
    "youtube",
    "video",
    "audio",
    "pdf",
    "document",
    "web",
    "meeting",
]


class TranscriptSegment(BaseModel):
    text: str
    start: float | None = None
    end: float | None = None
    speaker: str | None = None


class NormalizedSource(BaseModel):
    source_id: str
    source_type: SourceType
    title: str | None = None
    uri: str | None = None
    language: str | None = None
    segments: list[TranscriptSegment] = Field(default_factory=list)