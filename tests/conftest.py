"""Pytest configuration and fixtures."""
import pytest
from unittest.mock import MagicMock, patch
from app.db.database import get_db


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    with patch('app.db.database.get_db') as mock_db:
        # Create a mock Supabase client
        mock_client = MagicMock()
        mock_db.return_value = mock_client

        # Setup table mocks
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table

        yield mock_client


@pytest.fixture
def sample_conversation():
    """Sample conversation data."""
    return {
        "id": "conv-123",
        "title": "Test Conversation",
        "created_at": "2026-10-07T00:00:00Z",
        "updated_at": "2026-10-07T00:00:00Z",
    }


@pytest.fixture
def sample_message():
    """Sample message data."""
    return {
        "id": "msg-123",
        "conversation_id": "conv-123",
        "role": "user",
        "content": "What is this about?",
        "citations": [],
        "created_at": "2026-10-07T00:00:00Z",
    }


@pytest.fixture
def sample_source():
    """Sample source data."""
    return {
        "id": "src-123",
        "name": "Test Video",
        "source_type": "youtube",
        "uri": "https://youtube.com/watch?v=123",
        "status": "ready",
        "metadata": {"duration": 3600},
        "created_at": "2026-10-07T00:00:00Z",
        "updated_at": "2026-10-07T00:00:00Z",
    }
