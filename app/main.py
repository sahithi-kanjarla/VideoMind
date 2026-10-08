from fastapi import FastAPI
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.youtube import router as youtube_router
from app.api.conversations import router as conversations_router
from app.api.sources import router as sources_router
from app.api.chat import router as chat_router
from app.db.database import init_supabase
from app.services.ingestion.registry import register
from app.services.ingestion.youtube import YouTubeIngestor
from app.services.ingestion.pdf import PDFIngestor
from app.services.ingestion.docx_ingestor import DocxIngestor
from app.services.ingestion.text import TextIngestor
from app.services.ingestion.markdown import MarkdownIngestor
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
    register("pdf", PDFIngestor())
    register("docx", DocxIngestor())
    register("text", TextIngestor())
    register("markdown", MarkdownIngestor())
    print("Registered ingestors: youtube, pdf, docx, text, markdown")

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

frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": settings.app_name,
    }


# Static assets (JS, CSS, images) served at /assets/
if frontend_dist.is_dir():
    assets_dir = frontend_dist / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="static-assets")

    # SPA fallback — serve index.html for all non-API, non-asset routes
    @app.get("/{path:path}")
    def spa_fallback(path: str):
        file_path = frontend_dist / path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")
