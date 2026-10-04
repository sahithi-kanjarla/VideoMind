import chromadb

from app.models.chunk import TranscriptChunk


class ChromaVectorStore:
    """Store and retrieve VideoMind transcript chunks using Chroma."""

    COLLECTION_NAME = "videomind_chunks"

    def __init__(self, persist_directory: str = "chroma"):
        self.client = chromadb.PersistentClient(
            path=persist_directory
        )

        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(
        self,
        chunks: list[TranscriptChunk],
        embeddings: list[list[float]],
    ) -> None:
        """Store transcript chunks and their embeddings."""

        if len(chunks) != len(embeddings):
            raise ValueError(
                "Number of chunks must match number of embeddings"
            )

        self.collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            embeddings=embeddings,
            documents=[chunk.text for chunk in chunks],
            metadatas=[
                {
                    "source_id": chunk.source_id,
                    "start": chunk.start,
                    "end": chunk.end,
                    **chunk.metadata,
                }
                for chunk in chunks
            ],
        )

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> dict:
        """Search for the most similar chunks."""

        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )