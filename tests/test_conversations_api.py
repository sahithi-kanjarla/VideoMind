"""Tests for Conversations API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app


client = TestClient(app)


@patch('app.api.conversations.ConversationService.create')
def test_create_conversation_endpoint(mock_create, sample_conversation):
    """Test POST /api/conversations endpoint."""
    mock_create.return_value = sample_conversation

    response = client.post(
        "/api/conversations",
        json={"title": "Test Conversation"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "conv-123"
    assert data["title"] == "Test Conversation"


@patch('app.api.conversations.ConversationService.list')
def test_list_conversations_endpoint(mock_list, sample_conversation):
    """Test GET /api/conversations endpoint."""
    mock_list.return_value = [sample_conversation]

    response = client.get("/api/conversations")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "conv-123"


@patch('app.api.conversations.ConversationService.get_with_messages')
def test_get_conversation_endpoint(mock_get, sample_conversation, sample_message):
    """Test GET /api/conversations/{id} endpoint."""
    conv_with_messages = sample_conversation.copy()
    conv_with_messages["messages"] = [sample_message]
    conv_with_messages["sources"] = []

    mock_get.return_value = conv_with_messages

    response = client.get("/api/conversations/conv-123")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "conv-123"
    assert len(data["messages"]) == 1


@patch('app.api.conversations.ConversationService.get_with_messages')
def test_get_conversation_not_found(mock_get):
    """Test GET /api/conversations/{id} when not found."""
    mock_get.return_value = None

    response = client.get("/api/conversations/nonexistent")

    assert response.status_code == 404


@patch('app.api.conversations.ConversationService.update')
@patch('app.api.conversations.ConversationService.get')
def test_update_conversation_endpoint(mock_get, mock_update, sample_conversation):
    """Test PATCH /api/conversations/{id} endpoint."""
    mock_get.return_value = sample_conversation

    updated = sample_conversation.copy()
    updated["title"] = "Updated Title"
    mock_update.return_value = updated

    response = client.patch(
        "/api/conversations/conv-123",
        json={"title": "Updated Title"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"


@patch('app.api.conversations.ConversationService.delete')
def test_delete_conversation_endpoint(mock_delete):
    """Test DELETE /api/conversations/{id} endpoint."""
    mock_delete.return_value = True

    response = client.delete("/api/conversations/conv-123")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "deleted"


@patch('app.api.conversations.MessageService.append')
@patch('app.api.conversations.ConversationService.get')
def test_append_message_endpoint(mock_get_conv, mock_append, sample_conversation, sample_message):
    """Test POST /api/conversations/{id}/messages endpoint."""
    mock_get_conv.return_value = sample_conversation
    mock_append.return_value = sample_message

    response = client.post(
        "/api/conversations/conv-123/messages",
        json={
            "role": "user",
            "content": "What is this about?",
            "citations": []
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "user"
    assert data["content"] == "What is this about?"


@patch('app.api.conversations.MessageService.get_history')
@patch('app.api.conversations.ConversationService.get')
def test_get_messages_endpoint(mock_get_conv, mock_get_history, sample_conversation, sample_message):
    """Test GET /api/conversations/{id}/messages endpoint."""
    mock_get_conv.return_value = sample_conversation
    mock_get_history.return_value = [sample_message]

    response = client.get("/api/conversations/conv-123/messages")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["role"] == "user"
