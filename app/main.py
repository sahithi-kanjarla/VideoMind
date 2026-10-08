from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.youtube import router as youtube_router
from app.api.conversations import router as conversations_router
from app.api.sources import router as sources_router
from app.api.chat import router as chat_router
from app.db.database import init_supabase
from app.services.ingestion.registry import register
from app.services.ingestion.youtube import YouTubeIngestor
from fastapi.staticfiles import StaticFiles
from pathlib import Path


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    try:
        init_supabase()
        print("Supabase initialized")
    except Exception as e:
        print(f"Supabase initialization: {e}")

    register("youtube", YouTubeIngestor())
    print(f"Registered ingestors: youtube")

    yield
    print("App shutdown")


app = FastAPI(
    title=settings.app_name,
    description="Multimodal knowledge ingestion and conversational retrieval backend",
    version="0.2.0",
    lifespan=lifespan,
)

app.include_router(sources_router)
app.include_router(chat_router)
app.include_router(conversations_router)
app.include_router(youtube_router)

frontend_path = Path(__file__).resolve().parents[2] / "frontend"


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": settings.app_name,
    }


if frontend_path.is_dir():
    app.mount(
        "/frontend",
        StaticFiles(directory=frontend_path, html=True),
        name="frontend-files",
    )
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
