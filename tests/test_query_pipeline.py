import pytest
from unittest.mock import MagicMock, patch

from app.services.query_pipeline import QueryPipeline


@pytest.fixture
def mock_services():
    embeddings = MagicMock()
    store = MagicMock()
    retriever = MagicMock()
    generator = MagicMock()
    return embeddings, store, retriever, generator


@pytest.fixture
def pipeline(mock_services):
    return QueryPipeline(services=mock_services)


@patch("app.services.query_pipeline.ConversationService")
@patch("app.services.query_pipeline.SourceService")
@patch("app.services.query_pipeline.MessageService")
def test_query_no_sources(mock_msg, mock_src, mock_conv, pipeline):
    mock_conv.get.return_value = {"id": "conv-1", "title": "Test"}
    mock_src.get_conversation_sources.return_value = []

    result = pipeline.query("conv-1", "What is RAG?")

    assert result["answerable"] is False
    assert "No sources" in result["answer"]


@patch("app.services.query_pipeline.ConversationService")
@patch("app.services.query_pipeline.SourceService")
@patch("app.services.query_pipeline.MessageService")
def test_query_no_relevant_results(mock_msg, mock_src, mock_conv, pipeline, mock_services):
    mock_conv.get.return_value = {"id": "conv-1", "title": "Test"}
    mock_src.get_conversation_sources.return_value = [
        {"id": "s1", "source_type": "youtube", "metadata": {"source_id": "abc12345678"}}
    ]
    _, _, retriever, _ = mock_services
    retriever.retrieve.return_value = []

    result = pipeline.query("conv-1", "What is quantum computing?")

    assert result["answerable"] is False
    assert "couldn't find" in result["answer"]


@patch("app.services.query_pipeline.ConversationService")
@patch("app.services.query_pipeline.SourceService")
@patch("app.services.query_pipeline.MessageService")
def test_query_with_results(mock_msg, mock_src, mock_conv, pipeline, mock_services):
    mock_conv.get.return_value = {"id": "conv-1", "title": "Test"}
    mock_src.get_conversation_sources.return_value = [
        {"id": "s1", "source_type": "youtube", "metadata": {"source_id": "vid123"}}
    ]
    _, _, retriever, generator = mock_services
    retriever.retrieve.return_value = [
        {"text": "RAG is retrieval augmented generation", "metadata": {"source_id": "vid123", "start": 42.0}},
    ]
    generator.answer.return_value = "RAG stands for retrieval augmented generation."
    mock_msg.append.return_value = {"id": "m1"}

    result = pipeline.query("conv-1", "What is RAG?")

    assert result["answerable"] is True
    assert "RAG" in result["answer"]
    assert len(result["citations"]) >= 1


def test_query_empty_question(pipeline):
    with pytest.raises(ValueError, match="empty"):
        pipeline.query("conv-1", "   ")


@patch("app.services.query_pipeline.ConversationService")
def test_query_conversation_not_found(mock_conv, pipeline):
    mock_conv.get.return_value = None
    with pytest.raises(LookupError, match="not found"):
        pipeline.query("nonexistent", "What?")
