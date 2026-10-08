from fastapi import APIRouter, HTTPException

from app.schemas.youtube import (
    ChatQueryRequest,
    ChatQueryResponse,
    VideoResponse,
    YouTubeLoadRequest,
    YouTubeLoadResponse,
)
from app.services.ingestion.youtube import extract_video_id
from app.services.rag.groq_service import GroqGenerationError
from app.services.youtube_qa import YouTubeQA

router = APIRouter(prefix="/api")
_qa: YouTubeQA | None = None


def get_qa() -> YouTubeQA:
    global _qa
    if _qa is None:
        _qa = YouTubeQA()
    return _qa


@router.post("/youtube/load", response_model=YouTubeLoadResponse)
def load_youtube(request: YouTubeLoadRequest):
    url = str(request.url)
    try:
        extract_video_id(url)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    try:
        return get_qa().load(url)
    except ValueError as exc:
        raise HTTPException(422, f"Transcript unavailable: {exc}") from exc
    except Exception as exc:
        raise HTTPException(502, f"YouTube ingestion failed: {exc}") from exc


@router.get("/youtube/{video_id}", response_model=VideoResponse)
def get_youtube(video_id: str):
    video = get_qa().get_video(video_id)
    if video is None:
        raise HTTPException(404, "Video is not loaded in this session.")
    return video


@router.post("/chat/query", response_model=ChatQueryResponse)
def query_video(request: ChatQueryRequest):
    try:
        return get_qa().query(request.video_id, request.question)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except GroqGenerationError as exc:
        raise HTTPException(502, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Retrieval failed: {exc}") from exc
