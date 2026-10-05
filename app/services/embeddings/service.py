from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Generate embeddings for documents and queries."""

    MODEL_NAME = "intfloat/multilingual-e5-small"

    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for document chunks."""
        passages = [f"passage: {text}" for text in texts]

        embeddings = self.model.encode(
            passages,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        """Generate an embedding for a user query."""
        embedding = self.model.encode(
            f"query: {query}",
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return embedding.tolist()