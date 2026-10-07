"""Service for managing conversations."""
import uuid
from datetime import datetime
from typing import Optional
from app.db.database import get_db


class ConversationService:
    """Handle conversation CRUD operations."""

    @staticmethod
    def create(title: str) -> dict:
        """Create a new conversation."""
        db = get_db()
        conversation_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        response = db.table("conversations").insert({
            "id": conversation_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
        }).execute()

        if response.data:
            return response.data[0]
        raise Exception("Failed to create conversation")

    @staticmethod
    def get(conversation_id: str) -> Optional[dict]:
        """Get conversation by ID."""
        db = get_db()
        response = db.table("conversations").select("*").eq("id", conversation_id).execute()
        return response.data[0] if response.data else None

    @staticmethod
    def list(limit: int = 50, offset: int = 0) -> list[dict]:
        """List conversations with pagination."""
        db = get_db()
        response = db.table("conversations").select("*").order("updated_at", desc=True).range(offset, offset + limit - 1).execute()
        return response.data or []

    @staticmethod
    def update(conversation_id: str, title: Optional[str] = None) -> Optional[dict]:
        """Update conversation title."""
        if not title:
            return None

        db = get_db()
        now = datetime.utcnow().isoformat()

        response = db.table("conversations").update({
            "title": title,
            "updated_at": now,
        }).eq("id", conversation_id).execute()

        return response.data[0] if response.data else None

    @staticmethod
    def delete(conversation_id: str) -> bool:
        """Delete conversation and all related data."""
        db = get_db()
        response = db.table("conversations").delete().eq("id", conversation_id).execute()
        return len(response.data) > 0 if response.data else False

    @staticmethod
    def get_with_messages(conversation_id: str) -> Optional[dict]:
        """Get conversation with all messages and sources."""
        db = get_db()

        # Get conversation
        conv_response = db.table("conversations").select("*").eq("id", conversation_id).execute()
        if not conv_response.data:
            return None

        conversation = conv_response.data[0]

        # Get messages
        msg_response = db.table("messages").select("*").eq("conversation_id", conversation_id).order("created_at", desc=False).execute()
        conversation["messages"] = msg_response.data or []

        # Get sources
        src_response = db.table("conversation_sources").select("*, sources(*)").eq("conversation_id", conversation_id).order("order_index").execute()
        conversation["sources"] = [item["sources"] for item in (src_response.data or [])]

        return conversation
