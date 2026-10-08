"""API endpoints for conversation management."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from app.services.conversation_service import ConversationService
from app.services.message_service import MessageService

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


# Pydantic models
class ConversationCreate(BaseModel):
    title: str


class ConversationUpdate(BaseModel):
    title: str


class MessageCreate(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    citations: list = []


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    role: str
    content: str
    citations: list
    created_at: str


# Endpoints
@router.post("", response_model=ConversationResponse)
def create_conversation(data: ConversationCreate):
    """Create a new conversation."""
    try:
        conversation = ConversationService.create(title=data.title)
        return conversation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[ConversationResponse])
def list_conversations(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0)):
    """List all conversations with pagination."""
    try:
        conversations = ConversationService.list(limit=limit, offset=offset)
        return conversations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}", response_model=dict)
def get_conversation(conversation_id: str):
    """Get conversation with messages and sources."""
    try:
        conversation = ConversationService.get_with_messages(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{conversation_id}", response_model=ConversationResponse)
def update_conversation(conversation_id: str, data: ConversationUpdate):
    """Update conversation title."""
    try:
        conversation = ConversationService.update(conversation_id, title=data.title)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: str):
    """Delete a conversation and all related data."""
    try:
        success = ConversationService.delete(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"status": "deleted", "id": conversation_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
def append_message(conversation_id: str, data: MessageCreate):
    """Append a message to a conversation."""
    try:
        # Verify conversation exists
        conversation = ConversationService.get(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Append message
        message = MessageService.append(
            conversation_id=conversation_id,
            role=data.role,
            content=data.content,
            citations=data.citations
        )
        return message
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
def get_messages(conversation_id: str, limit: int = Query(100, ge=1, le=500)):
    """Get message history for a conversation."""
    try:
        # Verify conversation exists
        conversation = ConversationService.get(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        messages = MessageService.get_history(conversation_id, limit=limit)
        return messages
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
