import json
from pathlib import Path

import chromadb

from app.models.source import TranscriptSegment
from app.services.chunking.transcript import chunk_transcript
from app.services.embeddings.service import EmbeddingService
from app.services.ingestion.youtube import fetch_transcript
from app.services.retrieval.reranker import Reranker
from app.services.vector_store.chroma import ChromaVectorStore


VIDEO_URL = "https://www.youtube.com/watch?v=Y681hXWwhQY"
VIDEO_ID = "Y681hXWwhQY"

# We deliberately retrieve broadly.
# This is a candidate-pool experiment, NOT the final context size.
CANDIDATE_K_VALUES = [5, 10, 20, 30]

# Safety limit for adaptive selection.
MAX_RESULTS = 8

# First experimental adaptive rule.
# This is NOT a production threshold.
GAP_THRESHOLD = 3.0


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


# ============================================================
# METRICS
# ============================================================


def calculate_reciprocal_rank(
    retrieved_ids: list[str],
    relevant_ids: set[str],
) -> float:

    for rank, chunk_id in enumerate(
        retrieved_ids,
        start=1,
    ):
        if chunk_id in relevant_ids:
            return 1 / rank

    return 0.0


def calculate_recall_at_k(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    k: int,
) -> float:

    if not relevant_ids:
        return 0.0

    retrieved_at_k = set(
        retrieved_ids[:k]
    )

    relevant_retrieved = (
        retrieved_at_k & relevant_ids
    )

    return (
        len(relevant_retrieved)
        / len(relevant_ids)
    )


def calculate_hit_at_k(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    k: int,
) -> bool:

    return bool(
        set(retrieved_ids[:k])
        & relevant_ids
    )


def calculate_metrics(results):

    total = len(results)

    hit_1 = (
        sum(
            item["hit_at_1"]
            for item in results
        )
        / total
    )

    hit_3 = (
        sum(
            item["hit_at_3"]
            for item in results
        )
        / total
    )

    hit_5 = (
        sum(
            item["hit_at_5"]
            for item in results
        )
        / total
    )

    answerable_results = [
        item
        for item in results
        if item["answerable"]
    ]

    recall_1 = (
        sum(
            item["recall_at_1"]
            for item in answerable_results
        )
        / len(answerable_results)
        if answerable_results
        else 0.0
    )

    recall_3 = (
        sum(
            item["recall_at_3"]
            for item in answerable_results
        )
        / len(answerable_results)
        if answerable_results
        else 0.0
    )

    recall_5 = (
        sum(
            item["recall_at_5"]
            for item in answerable_results
        )
        / len(answerable_results)
        if answerable_results
        else 0.0
    )

    mrr = (
        sum(
            item["reciprocal_rank"]
            for item in answerable_results
        )
        / len(answerable_results)
        if answerable_results
        else 0.0
    )

    return {
        "hit_at_1": hit_1,
        "hit_at_3": hit_3,
        "hit_at_5": hit_5,
        "recall_at_1": recall_1,
        "recall_at_3": recall_3,
        "recall_at_5": recall_5,
        "mrr": mrr,
    }


# ============================================================
# ADAPTIVE SELECTOR
# ============================================================


def adaptive_select(
    scored_candidates: list[dict],
    max_results: int = MAX_RESULTS,
) -> list[dict]:
    """
    Experimental adaptive context selector.

    Input:
        Reranked candidates sorted from highest score
        to lowest score.

    Strategy:
        1. Look for the largest score drop.
        2. If the drop is meaningful, cut after it.
        3. Otherwise keep up to max_results.

    IMPORTANT:
        This is an experiment.
        The score-gap rule is NOT considered final.
    """

    if not scored_candidates:
        return []

    if len(scored_candidates) <= 1:
        return scored_candidates[:max_results]

    scores = [
        float(item["score"])
        for item in scored_candidates
    ]

    gaps = [
        scores[index] - scores[index + 1]
        for index in range(len(scores) - 1)
    ]

    largest_gap_index = max(
        range(len(gaps)),
        key=lambda index: gaps[index],
    )

    largest_gap = gaps[largest_gap_index]

    if largest_gap >= GAP_THRESHOLD:
        cutoff = largest_gap_index + 1
    else:
        cutoff = min(
            len(scored_candidates),
            max_results,
        )

    cutoff = max(1, cutoff)

    return scored_candidates[:min(
        cutoff,
        max_results,
    )]


# ============================================================
# EVALUATION
# ============================================================


def evaluate_retrieval(
    questions,
    embedding_service,
    store,
    reranker,
    candidate_k,
    selection_mode,
    verbose=True,
):

    results = []

    for index, item in enumerate(
        questions,
        start=1,
    ):

        question = item["question"]

        relevant_ids = set(
            item["relevant_chunks"]
        )

        answerable = bool(
            relevant_ids
        )

        query_embedding = (
            embedding_service.embed_query(
                question
            )
        )

        chroma_results = store.search(
            query_embedding=query_embedding,
            top_k=candidate_k,
        )

        candidate_ids = (
            chroma_results["ids"][0]
        )

        candidate_documents = (
            chroma_results["documents"][0]
        )

        # ----------------------------------------------------
        # Reranking
        # ----------------------------------------------------

        reranked = reranker.rerank(
            query=question,
            documents=candidate_documents,
            top_k=len(candidate_documents),
        )

        document_to_id = {
            document: chunk_id
            for document, chunk_id in zip(
                candidate_documents,
                candidate_ids,
            )
        }

        scored_candidates = []

        for result in reranked:

            chunk_id = document_to_id[
                result["text"]
            ]

            scored_candidates.append(
                {
                    "chunk_id": chunk_id,
                    "text": result["text"],
                    "score": result["score"],
                    "relevant": (
                        chunk_id in relevant_ids
                    ),
                }
            )

        # ----------------------------------------------------
        # Selection strategy
        # ----------------------------------------------------

        if selection_mode == "top5":

            selected = (
                scored_candidates[:5]
            )

        elif selection_mode == "adaptive":

            selected = adaptive_select(
                scored_candidates
            )

        elif selection_mode == "all":

            selected = scored_candidates

        else:
            raise ValueError(
                f"Unknown selection mode: "
                f"{selection_mode}"
            )

        retrieved_ids = [
            candidate["chunk_id"]
            for candidate in selected
        ]

        # ----------------------------------------------------
        # Metrics
        # ----------------------------------------------------

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

        recall_at_1 = calculate_recall_at_k(
            retrieved_ids,
            relevant_ids,
            1,
        )

        recall_at_3 = calculate_recall_at_k(
            retrieved_ids,
            relevant_ids,
            3,
        )

        recall_at_5 = calculate_recall_at_k(
            retrieved_ids,
            relevant_ids,
            5,
        )

        reciprocal_rank = (
            calculate_reciprocal_rank(
                retrieved_ids,
                relevant_ids,
            )
        )

        results.append(
            {
                "question": question,
                "answerable": answerable,
                "expected": sorted(
                    relevant_ids
                ),
                "retrieved": retrieved_ids,
                "scored_candidates": (
                    scored_candidates
                ),
                "selected_count": len(
                    selected
                ),
                "hit_at_1": hit_at_1,
                "hit_at_3": hit_at_3,
                "hit_at_5": hit_at_5,
                "recall_at_1": recall_at_1,
                "recall_at_3": recall_at_3,
                "recall_at_5": recall_at_5,
                "reciprocal_rank": (
                    reciprocal_rank
                ),
            }
        )

        # ----------------------------------------------------
        # Detailed output
        # ----------------------------------------------------

        if verbose:

            print(
                f"{index:02d}. {question}"
            )

            print(
                f"    Answerable: "
                f"{answerable}"
            )

            print(
                f"    Expected:   "
                f"{sorted(relevant_ids)}"
            )

            print(
                f"    Retrieved:  "
                f"{retrieved_ids}"
            )

            print(
                f"    Selected chunks: "
                f"{len(selected)}"
            )

            print(
                "    Reranker scores:"
            )

            for rank, candidate in enumerate(
                scored_candidates,
                start=1,
            ):

                print(
                    f"      {rank:02d}. "
                    f"chunk={candidate['chunk_id']} "
                    f"score="
                    f"{candidate['score']:.4f} "
                    f"relevant="
                    f"{candidate['relevant']}"
                )

            print(
                f"    Hit@1={hit_at_1} "
                f"Hit@3={hit_at_3} "
                f"Hit@5={hit_at_5}"
            )

            if answerable:

                print(
                    f"    Recall@1="
                    f"{recall_at_1:.2f} "
                    f"Recall@3="
                    f"{recall_at_3:.2f} "
                    f"Recall@5="
                    f"{recall_at_5:.2f}"
                )

            print()

    return results


# ============================================================
# PRINT METRICS
# ============================================================


def print_metrics(
    title,
    metrics,
):

    print("=" * 60)
    print(title)
    print("=" * 60)

    print(
        f"Hit@1:     "
        f"{metrics['hit_at_1']:.2%}"
    )

    print(
        f"Hit@3:     "
        f"{metrics['hit_at_3']:.2%}"
    )

    print(
        f"Hit@5:     "
        f"{metrics['hit_at_5']:.2%}"
    )

    print(
        f"Recall@1:  "
        f"{metrics['recall_at_1']:.2%}"
    )

    print(
        f"Recall@3:  "
        f"{metrics['recall_at_3']:.2%}"
    )

    print(
        f"Recall@5:  "
        f"{metrics['recall_at_5']:.2%}"
    )

    print(
        f"MRR:       "
        f"{metrics['mrr']:.3f}"
    )

    print()


def print_selection_stats(
    results,
):

    counts = [
        item["selected_count"]
        for item in results
    ]

    answerable_counts = [
        item["selected_count"]
        for item in results
        if item["answerable"]
    ]

    unanswerable_results = [
        item
        for item in results
        if not item["answerable"]
    ]

    correct_abstentions = sum(
        item["selected_count"] == 0
        for item in unanswerable_results
    )

    print("Selection statistics")
    print("--------------------")

    print(
        f"Average selected: "
        f"{sum(counts) / len(counts):.2f}"
    )

    print(
        f"Minimum selected: "
        f"{min(counts)}"
    )

    print(
        f"Maximum selected: "
        f"{max(counts)}"
    )

    if answerable_counts:

        print(
            f"Average selected "
            f"(answerable): "
            f"{sum(answerable_counts) / len(answerable_counts):.2f}"
        )

    print(
        f"Unanswerable questions: "
        f"{len(unanswerable_results)}"
    )

    print(
        f"Correct empty selections: "
        f"{correct_abstentions}"
    )

    if unanswerable_results:

        print(
            f"Unanswerable rejection rate: "
            f"{correct_abstentions / len(unanswerable_results):.2%}"
        )

    print()


# ============================================================
# COMPARISON
# ============================================================


def print_comparison(
    comparisons,
):

    print()
    print("#" * 90)
    print("SELECTION STRATEGY COMPARISON")
    print("#" * 90)

    print()

    print(
        f"{'Strategy':<20}"
        f"{'Hit@1':>10}"
        f"{'Hit@3':>10}"
        f"{'Recall@3':>12}"
        f"{'Recall@5':>12}"
        f"{'MRR':>10}"
        f"{'Avg Chunks':>14}"
    )

    print("-" * 90)

    for name, metrics, results in comparisons:

        avg_chunks = (
            sum(
                item["selected_count"]
                for item in results
            )
            / len(results)
        )

        print(
            f"{name:<20}"
            f"{metrics['hit_at_1']:>9.2%}"
            f"{metrics['hit_at_3']:>9.2%}"
            f"{metrics['recall_at_3']:>11.2%}"
            f"{metrics['recall_at_5']:>11.2%}"
            f"{metrics['mrr']:>9.3f}"
            f"{avg_chunks:>13.2f}"
        )

    print()


# ============================================================
# MAIN
# ============================================================


def main():

    questions = load_questions()

    print(
        f"Evaluation questions: "
        f"{len(questions)}"
    )

    answerable_count = sum(
        bool(item["relevant_chunks"])
        for item in questions
    )

    unanswerable_count = (
        len(questions)
        - answerable_count
    )

    print(
        f"Answerable:   "
        f"{answerable_count}"
    )

    print(
        f"Unanswerable: "
        f"{unanswerable_count}"
    )

    # --------------------------------------------------------
    # Build chunks
    # --------------------------------------------------------

    print(
        "\nBuilding transcript chunks..."
    )

    chunks = build_chunks()

    print(
        f"Chunks: {len(chunks)}"
    )

    # --------------------------------------------------------
    # Embeddings
    # --------------------------------------------------------

    print(
        "\nLoading embedding model..."
    )

    embedding_service = (
        EmbeddingService()
    )

    # --------------------------------------------------------
    # Reranker
    # --------------------------------------------------------

    print(
        "\nLoading reranker..."
    )

    reranker = Reranker()

    # --------------------------------------------------------
    # Chroma
    # --------------------------------------------------------

    print(
        "\nCreating in-memory Chroma..."
    )

    chroma_client = (
        chromadb.EphemeralClient()
    )

    store = ChromaVectorStore(
        client=chroma_client
    )

    # --------------------------------------------------------
    # Embeddings
    # --------------------------------------------------------

    print(
        "\nGenerating document embeddings..."
    )

    embeddings = (
        embedding_service.embed_documents(
            [
                chunk.text
                for chunk in chunks
            ]
        )
    )

    store.add_chunks(
        chunks,
        embeddings,
    )

    # ========================================================
    # BASELINE
    # ========================================================

    print("\n")
    print("#" * 60)
    print("BASELINE")
    print("E5 → Chroma → Top 5")
    print("#" * 60)

    baseline_results = []

    for index, item in enumerate(
        questions,
        start=1,
    ):

        question = item["question"]

        relevant_ids = set(
            item["relevant_chunks"]
        )

        query_embedding = (
            embedding_service.embed_query(
                question
            )
        )

        chroma_results = store.search(
            query_embedding=query_embedding,
            top_k=5,
        )

        retrieved_ids = (
            chroma_results["ids"][0]
        )[:5]

        baseline_results.append(
            {
                "question": question,
                "answerable": bool(
                    relevant_ids
                ),
                "expected": sorted(
                    relevant_ids
                ),
                "retrieved": retrieved_ids,
                "selected_count": len(
                    retrieved_ids
                ),
                "hit_at_1": calculate_hit_at_k(
                    retrieved_ids,
                    relevant_ids,
                    1,
                ),
                "hit_at_3": calculate_hit_at_k(
                    retrieved_ids,
                    relevant_ids,
                    3,
                ),
                "hit_at_5": calculate_hit_at_k(
                    retrieved_ids,
                    relevant_ids,
                    5,
                ),
                "recall_at_1": calculate_recall_at_k(
                    retrieved_ids,
                    relevant_ids,
                    1,
                ),
                "recall_at_3": calculate_recall_at_k(
                    retrieved_ids,
                    relevant_ids,
                    3,
                ),
                "recall_at_5": calculate_recall_at_k(
                    retrieved_ids,
                    relevant_ids,
                    5,
                ),
                "reciprocal_rank": calculate_reciprocal_rank(
                    retrieved_ids,
                    relevant_ids,
                ),
            }
        )

    baseline_metrics = calculate_metrics(
        baseline_results
    )

    print_metrics(
        "BASELINE RESULTS",
        baseline_metrics,
    )

    # ========================================================
    # CANDIDATE K + SELECTION EXPERIMENT
    # ========================================================

    comparisons = []

    for candidate_k in CANDIDATE_K_VALUES:

        effective_k = min(
            candidate_k,
            len(chunks),
        )

        print("\n")
        print("#" * 70)
        print(
            f"CANDIDATE K = {candidate_k} "
            f"(effective={effective_k})"
        )
        print("#" * 70)

        # ----------------------------------------------------
        # Top 5
        # ----------------------------------------------------

        print(
            f"\nE5 → Chroma Top {candidate_k} "
            f"→ CrossEncoder → Top 5"
        )

        top5_results = evaluate_retrieval(
            questions=questions,
            embedding_service=embedding_service,
            store=store,
            reranker=reranker,
            candidate_k=effective_k,
            selection_mode="top5",
            verbose=False,
        )

        top5_metrics = calculate_metrics(
            top5_results
        )

        print_metrics(
            f"TOP-5 RESULTS (K={candidate_k})",
            top5_metrics,
        )

        # ----------------------------------------------------
        # Adaptive
        # ----------------------------------------------------

        print(
            f"\nE5 → Chroma Top {candidate_k} "
            f"→ CrossEncoder → Adaptive"
        )

        adaptive_results = evaluate_retrieval(
            questions=questions,
            embedding_service=embedding_service,
            store=store,
            reranker=reranker,
            candidate_k=effective_k,
            selection_mode="adaptive",
            verbose=False,
        )

        adaptive_metrics = calculate_metrics(
            adaptive_results
        )

        print_metrics(
            f"ADAPTIVE RESULTS (K={candidate_k})",
            adaptive_metrics,
        )

        print_selection_stats(
            adaptive_results
        )

        # ----------------------------------------------------
        # Comparison
        # ----------------------------------------------------

        comparisons.append(
            (
                f"Top-5 K={candidate_k}",
                top5_metrics,
                top5_results,
            )
        )

        comparisons.append(
            (
                f"Adaptive K={candidate_k}",
                adaptive_metrics,
                adaptive_results,
            )
        )

    # ========================================================
    # FINAL COMPARISON
    # ========================================================

    print_comparison(
        comparisons
    )

    # ========================================================
    # BEST ADAPTIVE CONFIGURATION
    # ========================================================

    adaptive_comparisons = [
        item
        for item in comparisons
        if item[0].startswith("Adaptive")
    ]

    best_adaptive = max(
        adaptive_comparisons,
        key=lambda item: item[1]["mrr"],
    )

    print(
        "#" * 70
    )

    print(
        "BEST ADAPTIVE CONFIGURATION"
    )

    print(
        "#" * 70
    )

    print(
        f"\nStrategy: "
        f"{best_adaptive[0]}"
    )

    print(
        f"MRR: "
        f"{best_adaptive[1]['mrr']:.3f}"
    )

    print(
        f"Recall@3: "
        f"{best_adaptive[1]['recall_at_3']:.2%}"
    )

    print(
        f"Recall@5: "
        f"{best_adaptive[1]['recall_at_5']:.2%}"
    )

    print_selection_stats(
        best_adaptive[2]
    )

    print(
        "\nEvaluation complete."
    )


if __name__ == "__main__":
    main()