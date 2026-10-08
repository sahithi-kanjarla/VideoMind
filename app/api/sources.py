"""API endpoints for source management."""
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from app.schemas.sources import (
    AddYouTubeSourceRequest,
    SourceResponse,
    SourceStatusResponse,
    UPLOAD_EXTENSIONS,
)
from app.services.conversation_service import ConversationService
from app.services.ingestion.registry import registered_types
from app.services.rag.groq_service import GroqGenerationError
from app.services.source_service import SourceService

router = APIRouter(prefix="/api", tags=["sources"])

_pipeline = None


def get_pipeline():
    global _pipeline
    if _pipeline is None:
        from app.services.query_pipeline import QueryPipeline
        _pipeline = QueryPipeline()
    return _pipeline


@router.post(
    "/conversations/{conversation_id}/sources",
    response_model=dict,
)
def add_source(conversation_id: str, request: AddYouTubeSourceRequest):
    """Add a URL-based source (YouTube) to a conversation."""
    conversation = ConversationService.get(conversation_id)
    if conversation is None:
        raise HTTPException(404, "Conversation not found")

    if request.source_type not in registered_types():
        raise HTTPException(
            422, f"Unsupported source type: {request.source_type}. "
            f"Supported: {registered_types()}"
        )

    try:
        result = get_pipeline().ingest_source(
            conversation_id=conversation_id,
            source_type=request.source_type,
            input_value=request.url,
        )
        return result
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except GroqGenerationError as exc:
        raise HTTPException(502, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Source ingestion failed: {exc}") from exc


@router.post(
    "/conversations/{conversation_id}/sources/upload",
    response_model=dict,
)
def upload_source(conversation_id: str, file: UploadFile):
    """Upload a file (PDF, DOCX, TXT, Markdown) as a source."""
    conversation = ConversationService.get(conversation_id)
    if conversation is None:
        raise HTTPException(404, "Conversation not found")

    suffix = Path(file.filename or "").suffix.lower()

    # Determine source type from file extension
    source_type = None
    for stype, extensions in UPLOAD_EXTENSIONS.items():
        if suffix in extensions:
            source_type = stype
            break

    if source_type is None:
        allowed = [ext for exts in UPLOAD_EXTENSIONS.values() for ext in exts]
        raise HTTPException(
            422, f"Unsupported file type: {suffix}. Allowed: {', '.join(allowed)}"
        )

    if source_type not in registered_types():
        raise HTTPException(422, f"Ingestor not available for: {source_type}")

    # Save upload to a temp file and ingest
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = file.file.read()
            tmp.write(content)
            tmp_path = Path(tmp.name)

        result = get_pipeline().ingest_source(
            conversation_id=conversation_id,
            source_type=source_type,
            input_value=tmp_path,
            title=Path(file.filename or "upload").stem,
        )
        return result
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except GroqGenerationError as exc:
        raise HTTPException(502, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"File ingestion failed: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)


@router.get(
    "/conversations/{conversation_id}/sources",
    response_model=list[SourceResponse],
)
def list_sources(conversation_id: str):
    """List sources for a conversation."""
    conversation = ConversationService.get(conversation_id)
    if conversation is None:
        raise HTTPException(404, "Conversation not found")

    sources = SourceService.get_conversation_sources(conversation_id)
    return sources


@router.get("/sources/{source_id}/status", response_model=SourceStatusResponse)
def get_source_status(source_id: str):
    """Poll source processing status."""
    source = SourceService.get(source_id)
    if source is None:
        raise HTTPException(404, "Source not found")
    return {
        "id": source["id"],
        "status": source["status"],
        "metadata": source.get("metadata", {}),
    }


@router.delete("/sources/{source_id}")
def delete_source(source_id: str):
    """Remove a source and its chunks."""
    success = SourceService.delete(source_id)
    if not success:
        raise HTTPException(404, "Source not found")
    return {"status": "deleted", "id": source_id}
