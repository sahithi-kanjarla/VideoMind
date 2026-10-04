from app.services.embeddings.service import EmbeddingService


def test_document_embedding():
    service = EmbeddingService()

    embeddings = service.embed_documents(
        [
            "Most animals spend most of their time doing nothing.",
            "Lions can sleep for many hours every day.",
        ]
    )

    assert len(embeddings) == 2
    assert len(embeddings[0]) == 384
    assert len(embeddings[1]) == 384


def test_query_embedding():
    service = EmbeddingService()

    embedding = service.embed_query(
        "Why do animals spend so much time doing nothing?"
    )

    assert len(embedding) == 384