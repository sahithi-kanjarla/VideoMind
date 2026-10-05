from fastapi import FastAPI

from app.core.config import settings
from app.api.youtube import router as youtube_router
from fastapi.staticfiles import StaticFiles
from pathlib import Path


app = FastAPI(
    title=settings.app_name,
    description="Multimodal knowledge ingestion and conversational retrieval backend",
    version="0.1.0",
)

app.include_router(youtube_router)
frontend_path = Path(__file__).resolve().parents[1] / "frontend"


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": settings.app_name,
    }


if frontend_path.is_dir():
    # Support both the application root and the path users commonly open
    # while working from the repository layout.
    app.mount(
        "/frontend",
        StaticFiles(directory=frontend_path, html=True),
        name="frontend-files",
    )
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
