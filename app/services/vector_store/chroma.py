import chromadb

from app.models.chunk import ContentChunk


class ChromaVectorStore:
    COLLECTION_NAME = "videomind_chunks"

    def __init__(
        self,
        persist_directory: str = "chroma",
        client=None,
    ):
        if client is not None:
            self.client = client
        else:
            self.client = chromadb.PersistentClient(
                path=persist_directory
            )

        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(
        self,
        chunks: list[ContentChunk],
        embeddings: list[list[float]],
    ) -> None:
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
                    **chunk.metadata,
                    "start": chunk.start,
                    "end": chunk.end,
                }
                for chunk in chunks
            ],
        )

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        source_ids: list[str] | None = None,
    ) -> dict:
        options = {}
        if source_ids:
            if len(source_ids) == 1:
                options["where"] = {"source_id": source_ids[0]}
            else:
                options["where"] = {"source_id": {"$in": source_ids}}
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            **options,
        )
