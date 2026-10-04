from app.services.embeddings.service import EmbeddingService
from app.services.retrieval.reranker import Reranker
from app.services.vector_store.chroma import ChromaVectorStore


class Retriever:
    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: ChromaVectorStore,
        reranker: Reranker | None = None,
        candidate_k: int = 20,
        max_results: int = 8,
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.reranker = reranker

        # Candidate pool is intentionally larger than the final context.
        self.candidate_k = candidate_k

        # Safety limit so one query cannot flood the LLM context.
        self.max_results = max_results

    def retrieve(self, query: str, source_id: str | None = None) -> list[dict]:
        query_embedding = self.embedding_service.embed_query(query)

        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=self.candidate_k,
            source_id=source_id,
        )

        candidate_ids = results["ids"][0]
        candidate_documents = results["documents"][0]
        candidate_metadatas = results["metadatas"][0]

        if not candidate_documents:
            return []

        candidates = [
            {
                "chunk_id": chunk_id,
                "text": document,
                "metadata": metadata,
            }
            for chunk_id, document, metadata in zip(
                candidate_ids,
                candidate_documents,
                candidate_metadatas,
            )
        ]

        # If no reranker is configured, return the semantic results.
        if self.reranker is None:
            return candidates[: self.max_results]

        reranked = self.reranker.rerank(
            query=query,
            documents=[candidate["text"] for candidate in candidates],
            top_k=len(candidates),
        )

        document_lookup = {
            candidate["text"]: candidate
            for candidate in candidates
        }

        reranked_candidates = []

        for result in reranked:
            document = result["text"]
            original = document_lookup.get(document)

            if original is None:
                continue

            reranked_candidates.append(
                {
                    "chunk_id": original["chunk_id"],
                    "text": document,
                    "score": result["score"],
                    "metadata": original["metadata"],
                }
            )

        return self._select_relevant(
            reranked_candidates
        )

    def _select_relevant(
        self,
        results: list[dict],
    ) -> list[dict]:
        """
        Dynamically select relevant chunks from reranked results.

        The selector does not use a fixed score threshold.
        Instead, it looks for a meaningful score drop between
        consecutive candidates.

        A maximum result limit is still kept as a safety guard.
        """

        if not results:
            return []

        if len(results) == 1:
            return results

        # Reranker results are already sorted highest → lowest.
        scores = [float(result["score"]) for result in results]

        # Calculate drops between consecutive scores.
        gaps = [
            scores[i] - scores[i + 1]
            for i in range(len(scores) - 1)
        ]

        # Find the largest drop.
        largest_gap_index = max(
            range(len(gaps)),
            key=lambda index: gaps[index],
        )

        largest_gap = gaps[largest_gap_index]

        # Conservative initial rule.
        #
        # We only cut when there is a meaningful score cliff.
        # Otherwise keep the strongest results up to max_results.
        #
        # This value is intentionally isolated here so it can
        # be replaced later after evaluation.
        GAP_THRESHOLD = 3.0

        if largest_gap >= GAP_THRESHOLD:
            cutoff = largest_gap_index + 1
            selected = results[:cutoff]
        else:
            selected = results[: self.max_results]

        return selected[: self.max_results]
