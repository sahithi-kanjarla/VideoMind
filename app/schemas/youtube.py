from pydantic import BaseModel, Field, HttpUrl


class YouTubeLoadRequest(BaseModel):
    url: HttpUrl


class YouTubeLoadResponse(BaseModel):
    video_id: str
    url: str
    title: str
    status: str
    chunks: int


class VideoResponse(BaseModel):
    video_id: str
    url: str
    title: str
    status: str
    chunks: int


class ChatQueryRequest(BaseModel):
    video_id: str = Field(min_length=11, max_length=11)
    question: str = Field(min_length=1, max_length=2000)


class SourceTimestamp(BaseModel):
    start: float
    label: str


class ChatQueryResponse(BaseModel):
    answer: str
    sources: list[SourceTimestamp]
