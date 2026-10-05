import json
from pathlib import Path

import chromadb

from app.models.source import TranscriptSegment
from app.services.chunking.transcript import chunk_transcript
from app.services.embeddings.service import EmbeddingService
from app.services.ingestion.youtube import fetch_transcript
from app.services.vector_store.chroma import ChromaVectorStore


VIDEO_URL = "https://www.youtube.com/watch?v=Y681hXWwhQY"
VIDEO_ID = "Y681hXWwhQY"


def load_questions():
    path = Path(__file__).parent / "retrieval_questions.json"

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def build_chunks():
    raw_segments = fetch_transcript(VIDEO_URL)

    segments = [
        TranscriptSegment(
            text=item["text"],
            start=item["start"],
            end=item["start"] + item["duration"],
        )
        for item in raw_segments
    ]

    return chunk_transcript(
        source_id=VIDEO_ID,
        segments=segments,
        target_words=100,
        overlap_segments=1,
    )


def calculate_reciprocal_rank(
    retrieved_ids: list[str],
    relevant_ids: set[str],
) -> float:
    """Return reciprocal rank of the first relevant result."""

    for rank, chunk_id in enumerate(retrieved_ids, start=1):
        if chunk_id in relevant_ids:
            return 1 / rank

    return 0.0


def calculate_recall_at_k(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    k: int,
) -> float:
    """
    Calculate true Recall@K.

    Recall@K = relevant chunks retrieved in top K
               ---------------------------------
               total relevant chunks
    """

    if not relevant_ids:
        return 0.0

    retrieved_at_k = set(retrieved_ids[:k])

    relevant_retrieved = retrieved_at_k & relevant_ids

    return len(relevant_retrieved) / len(relevant_ids)


def calculate_hit_at_k(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    k: int,
) -> bool:
    """
    Hit@K is True when at least one relevant chunk
    appears in the top K results.
    """

    return bool(set(retrieved_ids[:k]) & relevant_ids)


def main():
    questions = load_questions()

    print("Building transcript chunks...")
    chunks = build_chunks()

    print(f"Chunks: {len(chunks)}")

    print("Loading embedding model...")
    embedding_service = EmbeddingService()

    print("Creating in-memory Chroma database...")

    # EphemeralClient keeps Chroma in memory.
    # This avoids Windows file-locking problems caused by
    # deleting PersistentClient files immediately after evaluation.
    chroma_client = chromadb.EphemeralClient()

    store = ChromaVectorStore(
        client=chroma_client
    )

    print("Generating document embeddings...")

    embeddings = embedding_service.embed_documents(
        [chunk.text for chunk in chunks]
    )

    store.add_chunks(chunks, embeddings)

    hit_at_1_count = 0
    hit_at_3_count = 0
    hit_at_5_count = 0

    recall_at_1_scores = []
    recall_at_3_scores = []
    recall_at_5_scores = []

    reciprocal_ranks = []

    print("\nRunning retrieval evaluation...\n")

    for index, item in enumerate(questions, start=1):
        question = item["question"]
        relevant_ids = set(item["relevant_chunks"])

        query_embedding = embedding_service.embed_query(
            question
        )

        results = store.search(
            query_embedding=query_embedding,
            top_k=5,
        )

        retrieved_ids = results["ids"][0]

        # -------------------------
        # Hit@K
        # -------------------------

        hit_at_1 = calculate_hit_at_k(
            retrieved_ids,
            relevant_ids,
            1,
        )

        hit_at_3 = calculate_hit_at_k(
            retrieved_ids,
            relevant_ids,
            3,
        )

        hit_at_5 = calculate_hit_at_k(
            retrieved_ids,
            relevant_ids,
            5,
        )

        if hit_at_1:
            hit_at_1_count += 1

        if hit_at_3:
            hit_at_3_count += 1

        if hit_at_5:
            hit_at_5_count += 1

        # -------------------------
        # True Recall@K
        # -------------------------

        recall_1 = calculate_recall_at_k(
            retrieved_ids,
            relevant_ids,
            1,
        )

        recall_3 = calculate_recall_at_k(
            retrieved_ids,
            relevant_ids,
            3,
        )

        recall_5 = calculate_recall_at_k(
            retrieved_ids,
            relevant_ids,
            5,
        )

        recall_at_1_scores.append(recall_1)
        recall_at_3_scores.append(recall_3)
        recall_at_5_scores.append(recall_5)

        # -------------------------
        # MRR
        # -------------------------

        reciprocal_rank = calculate_reciprocal_rank(
            retrieved_ids,
            relevant_ids,
        )

        reciprocal_ranks.append(reciprocal_rank)

        # -------------------------
        # Per-question output
        # -------------------------

        print(f"{index:02d}. {question}")
        print(f"    Expected:  {sorted(relevant_ids)}")
        print(f"    Retrieved: {retrieved_ids}")

        print(
            f"    Hit@1={hit_at_1} "
            f"Hit@3={hit_at_3} "
            f"Hit@5={hit_at_5}"
        )

        print(
            f"    Recall@1={recall_1:.2f} "
            f"Recall@3={recall_3:.2f} "
            f"Recall@5={recall_5:.2f}"
        )

        print()

    # -------------------------
    # Final metrics
    # -------------------------

    total = len(questions)

    hit_1 = hit_at_1_count / total
    hit_3 = hit_at_3_count / total
    hit_5 = hit_at_5_count / total

    recall_1 = sum(recall_at_1_scores) / total
    recall_3 = sum(recall_at_3_scores) / total
    recall_5 = sum(recall_at_5_scores) / total

    mrr = sum(reciprocal_ranks) / total

    print("=" * 60)
    print("RETRIEVAL EVALUATION")
    print("=" * 60)

    print(f"Questions: {total}")

    print("\nHit Rate")
    print(f"Hit@1:     {hit_1:.2%}")
    print(f"Hit@3:     {hit_3:.2%}")
    print(f"Hit@5:     {hit_5:.2%}")

    print("\nRecall")
    print(f"Recall@1:  {recall_1:.2%}")
    print(f"Recall@3:  {recall_3:.2%}")
    print(f"Recall@5:  {recall_5:.2%}")

    print(f"\nMRR:       {mrr:.3f}")

    print("=" * 60)


if __name__ == "__main__":
    main()