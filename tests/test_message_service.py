"""Tests for MessageService."""
import pytest
from unittest.mock import MagicMock, patch
from app.services.message_service import MessageService


@patch('app.services.message_service.get_db')
def test_append_message(mock_get_db, sample_message):
    """Test appending a message."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    # Mock response
    mock_response = MagicMock()
    mock_response.data = [sample_message]
    mock_db.table.return_value.insert.return_value.execute.return_value = mock_response

    # Test
    result = MessageService.append(
        conversation_id="conv-123",
        role="user",
        content="What is this about?",
        citations=[]
    )

    assert result["id"] == "msg-123"
    assert result["role"] == "user"
    assert result["content"] == "What is this about?"


@patch('app.services.message_service.get_db')
def test_append_message_invalid_role(mock_get_db):
    """Test appending a message with invalid role."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    # Test
    with pytest.raises(ValueError):
        MessageService.append(
            conversation_id="conv-123",
            role="invalid",
            content="Test",
        )


@patch('app.services.message_service.get_db')
def test_get_history(mock_get_db, sample_message):
    """Test getting message history."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    # Mock response
    mock_response = MagicMock()
    mock_response.data = [sample_message]
    mock_db.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_response

    # Test
    result = MessageService.get_history("conv-123", limit=100)

    assert len(result) == 1
    assert result[0]["role"] == "user"


@patch('app.services.message_service.get_db')
def test_get_recent(mock_get_db, sample_message):
    """Test getting recent messages."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    # Mock response
    mock_response = MagicMock()
    mock_response.data = [sample_message]
    mock_db.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_response

    # Test
    result = MessageService.get_recent("conv-123", count=10)

    assert len(result) == 1


@patch('app.services.message_service.get_db')
def test_delete_message(mock_get_db):
    """Test deleting a message."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    # Mock response
    mock_response = MagicMock()
    mock_response.data = [{"id": "msg-123"}]
    mock_db.table.return_value.delete.return_value.eq.return_value.execute.return_value = mock_response

    # Test
    result = MessageService.delete_message("msg-123")

    assert result is True
