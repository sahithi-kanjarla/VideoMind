from pydantic import BaseModel, Field


class AddYouTubeSourceRequest(BaseModel):
    source_type: str = "youtube"
    url: str = Field(min_length=1)


class SourceResponse(BaseModel):
    id: str
    name: str
    source_type: str
    uri: str | None = None
    status: str
    metadata: dict = {}
    created_at: str
    updated_at: str


class SourceStatusResponse(BaseModel):
    id: str
    status: str
    metadata: dict = {}
