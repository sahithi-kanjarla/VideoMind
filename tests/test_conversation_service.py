"""Tests for ConversationService."""
import pytest
from unittest.mock import MagicMock, patch
from app.services.conversation_service import ConversationService


@patch('app.services.conversation_service.get_db')
def test_create_conversation(mock_get_db, sample_conversation):
    """Test creating a conversation."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    # Mock response
    mock_response = MagicMock()
    mock_response.data = [sample_conversation]
    mock_db.table.return_value.insert.return_value.execute.return_value = mock_response

    # Test
    result = ConversationService.create("Test Conversation")

    assert result["id"] == "conv-123"
    assert result["title"] == "Test Conversation"
    mock_db.table.assert_called_with("conversations")


@patch('app.services.conversation_service.get_db')
def test_get_conversation(mock_get_db, sample_conversation):
    """Test getting a conversation."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    # Mock response
    mock_response = MagicMock()
    mock_response.data = [sample_conversation]
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

    # Test
    result = ConversationService.get("conv-123")

    assert result["id"] == "conv-123"
    assert result["title"] == "Test Conversation"


@patch('app.services.conversation_service.get_db')
def test_get_conversation_not_found(mock_get_db):
    """Test getting a non-existent conversation."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    # Mock empty response
    mock_response = MagicMock()
    mock_response.data = []
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

    # Test
    result = ConversationService.get("nonexistent")

    assert result is None


@patch('app.services.conversation_service.get_db')
def test_list_conversations(mock_get_db, sample_conversation):
    """Test listing conversations."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    # Mock response
    mock_response = MagicMock()
    mock_response.data = [sample_conversation]
    mock_db.table.return_value.select.return_value.order.return_value.range.return_value.execute.return_value = mock_response

    # Test
    result = ConversationService.list(limit=50, offset=0)

    assert len(result) == 1
    assert result[0]["id"] == "conv-123"


@patch('app.services.conversation_service.get_db')
def test_update_conversation(mock_get_db, sample_conversation):
    """Test updating a conversation."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    updated = sample_conversation.copy()
    updated["title"] = "Updated Title"

    # Mock response
    mock_response = MagicMock()
    mock_response.data = [updated]
    mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response

    # Test
    result = ConversationService.update("conv-123", title="Updated Title")

    assert result["title"] == "Updated Title"


@patch('app.services.conversation_service.get_db')
def test_delete_conversation(mock_get_db):
    """Test deleting a conversation."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    # Mock response
    mock_response = MagicMock()
    mock_response.data = [{"id": "conv-123"}]
    mock_db.table.return_value.delete.return_value.eq.return_value.execute.return_value = mock_response

    # Test
    result = ConversationService.delete("conv-123")

    assert result is True


@patch('app.services.conversation_service.get_db')
def test_get_with_messages(mock_get_db, sample_conversation, sample_message):
    """Test getting conversation with messages."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    # Mock conversation response
    conv_response = MagicMock()
    conv_response.data = [sample_conversation]

    # Mock messages response
    msg_response = MagicMock()
    msg_response.data = [sample_message]

    # Mock sources response
    src_response = MagicMock()
    src_response.data = []

    # Setup side effects
    select_mock = MagicMock()
    eq_mock = MagicMock()

    # First call for conversation
    def table_side_effect(table_name):
        mock_table = MagicMock()
        if table_name == "conversations":
            mock_table.select.return_value.eq.return_value.execute.return_value = conv_response
        elif table_name == "messages":
            mock_table.select.return_value.eq.return_value.order.return_value.execute.return_value = msg_response
        elif table_name == "conversation_sources":
            mock_table.select.return_value.eq.return_value.order.return_value.execute.return_value = src_response
        return mock_table

    mock_db.table.side_effect = table_side_effect

    # Test
    result = ConversationService.get_with_messages("conv-123")

    assert result["id"] == "conv-123"
    assert len(result["messages"]) == 1
