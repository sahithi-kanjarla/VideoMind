from app.models.source import TranscriptSegment
from app.services.chunking.transcript import chunk_transcript
from app.services.embeddings.service import EmbeddingService
from app.services.vector_store.chroma import ChromaVectorStore


def test_chroma_retrieves_relevant_chunk(tmp_path):
    segments = [
        TranscriptSegment(
            text="Most animals spend most of their time doing absolutely nothing.",
            start=0.0,
            end=5.0,
        ),
        TranscriptSegment(
            text="Some animals have evolved to rest and conserve energy.",
            start=5.0,
            end=10.0,
        ),
        TranscriptSegment(
            text="The programme also discusses useful vocabulary.",
            start=10.0,
            end=15.0,
        ),
    ]

    chunks = chunk_transcript(
        source_id="test-video",
        segments=segments,
        target_words=10,
        overlap_segments=0,
    )

    embedding_service = EmbeddingService()

    embeddings = embedding_service.embed_documents(
        [chunk.text for chunk in chunks]
    )

    store = ChromaVectorStore(
        persist_directory=str(tmp_path / "chroma")
    )

    store.add_chunks(chunks, embeddings)

    query_embedding = embedding_service.embed_query(
        "Why do animals spend so much time doing nothing?"
    )

    results = store.search(
        query_embedding=query_embedding,
        top_k=1,
    )

    assert results["documents"]
    assert results["documents"][0]

    top_result = results["documents"][0][0]

    assert "animals" in top_result.lower()
    assert "nothing" in top_result.lower()