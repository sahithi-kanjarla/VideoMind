from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.youtube import router as youtube_router
from app.api.conversations import router as conversations_router
from app.db.database import init_supabase
from fastapi.staticfiles import StaticFiles
from pathlib import Path


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    try:
        init_supabase()
        print("✓ Supabase initialized")
    except Exception as e:
        print(f"⚠ Supabase initialization: {e}")
    yield
    # Shutdown
    print("App shutdown")


app = FastAPI(
    title=settings.app_name,
    description="Multimodal knowledge ingestion and conversational retrieval backend",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(youtube_router)
app.include_router(conversations_router)
frontend_path = Path(__file__).resolve().parents[2] / "frontend"


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
