"""Service for managing messages."""
import uuid
from datetime import datetime
from typing import Optional
from app.db.database import get_db


class MessageService:
    """Handle message CRUD operations."""

    @staticmethod
    def append(conversation_id: str, role: str, content: str, citations: list = None) -> dict:
        """Append a message to a conversation."""
        if citations is None:
            citations = []

        if role not in ("user", "assistant"):
            raise ValueError("Role must be 'user' or 'assistant'")

        db = get_db()
        message_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        response = db.table("messages").insert({
            "id": message_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "citations": citations,
            "created_at": now,
        }).execute()

        if response.data:
            return response.data[0]
        raise Exception("Failed to append message")

    @staticmethod
    def get_history(conversation_id: str, limit: int = 100) -> list[dict]:
        """Get message history for a conversation."""
        db = get_db()
        response = db.table("messages").select("*").eq("conversation_id", conversation_id).order("created_at", desc=False).limit(limit).execute()
        return response.data or []

    @staticmethod
    def get_recent(conversation_id: str, count: int = 10) -> list[dict]:
        """Get most recent messages for context."""
        db = get_db()
        response = db.table("messages").select("*").eq("conversation_id", conversation_id).order("created_at", desc=False).limit(count).execute()
        return response.data or []

    @staticmethod
    def delete_message(message_id: str) -> bool:
        """Delete a message."""
        db = get_db()
        response = db.table("messages").delete().eq("id", message_id).execute()
        return len(response.data) > 0 if response.data else False
