"""API endpoints for conversation-aware chat."""
from fastapi import APIRouter, HTTPException

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.conversation_service import ConversationService
from app.services.rag.groq_service import GroqGenerationError

router = APIRouter(prefix="/api", tags=["chat"])

_pipeline = None


def get_pipeline():
    global _pipeline
    if _pipeline is None:
        from app.services.query_pipeline import QueryPipeline
        _pipeline = QueryPipeline()
    return _pipeline


@router.post(
    "/conversations/{conversation_id}/chat",
    response_model=ChatResponse,
)
def chat(conversation_id: str, request: ChatRequest):
    """Send a message and get an answer from the conversation's sources."""
    conversation = ConversationService.get(conversation_id)
    if conversation is None:
        raise HTTPException(404, "Conversation not found")

    try:
        result = get_pipeline().query(conversation_id, request.message)
        return result
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except GroqGenerationError as exc:
        raise HTTPException(502, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Query failed: {exc}") from exc
