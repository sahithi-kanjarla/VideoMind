"""Service for managing sources."""
import uuid
from datetime import datetime
from typing import Optional
from app.db.database import get_db


class SourceService:
    """Handle source CRUD operations."""

    @staticmethod
    def create(name: str, source_type: str, uri: Optional[str] = None, metadata: dict = None) -> dict:
        """Create a new source."""
        if metadata is None:
            metadata = {}

        db = get_db()
        source_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        response = db.table("sources").insert({
            "id": source_id,
            "name": name,
            "source_type": source_type,
            "uri": uri,
            "status": "processing",
            "metadata": metadata,
            "created_at": now,
            "updated_at": now,
        }).execute()

        if response.data:
            return response.data[0]
        raise Exception("Failed to create source")

    @staticmethod
    def get(source_id: str) -> Optional[dict]:
        """Get source by ID."""
        db = get_db()
        response = db.table("sources").select("*").eq("id", source_id).execute()
        return response.data[0] if response.data else None

    @staticmethod
    def update_status(source_id: str, status: str, metadata: dict = None) -> Optional[dict]:
        """Update source status and metadata."""
        if status not in ("processing", "ready", "error"):
            raise ValueError("Status must be 'processing', 'ready', or 'error'")

        db = get_db()
        now = datetime.utcnow().isoformat()

        update_data = {
            "status": status,
            "updated_at": now,
        }

        if metadata:
            update_data["metadata"] = metadata

        response = db.table("sources").update(update_data).eq("id", source_id).execute()
        return response.data[0] if response.data else None

    @staticmethod
    def link_to_conversation(conversation_id: str, source_id: str, order_index: int = 0) -> dict:
        """Link a source to a conversation."""
        db = get_db()
        link_id = str(uuid.uuid4())

        response = db.table("conversation_sources").insert({
            "id": link_id,
            "conversation_id": conversation_id,
            "source_id": source_id,
            "order_index": order_index,
        }).execute()

        if response.data:
            return response.data[0]
        raise Exception("Failed to link source to conversation")

    @staticmethod
    def get_conversation_sources(conversation_id: str) -> list[dict]:
        """Get all sources for a conversation."""
        db = get_db()
        response = db.table("conversation_sources").select("*, sources(*)").eq("conversation_id", conversation_id).order("order_index").execute()
        return [item["sources"] for item in (response.data or [])]

    @staticmethod
    def delete(source_id: str) -> bool:
        """Delete a source (cascades to chunks and links)."""
        db = get_db()
        response = db.table("sources").delete().eq("id", source_id).execute()
        return len(response.data) > 0 if response.data else False
