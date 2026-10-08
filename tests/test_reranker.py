from app.services.retrieval.reranker import Reranker


def test_reranker_returns_top_k():
    reranker = Reranker()

    documents = [
        "Lions can sleep for around 20 hours a day.",
        "Ants live together in colonies.",
        "Some ants remain inactive as reserve workers.",
    ]

    results = reranker.rerank(
        query="Why are some ants inactive?",
        documents=documents,
        top_k=2,
    )

    assert len(results) == 2
    assert all("text" in result for result in results)
    assert all("score" in result for result in results)

    assert results[0]["score"] >= results[1]["score"]


def test_reranker_prioritizes_relevant_document():
    reranker = Reranker()

    documents = [
        "Lions can sleep for around 20 hours a day.",
        "Some ants remain inactive as reserve workers.",
        "Boredom can encourage invention.",
    ]

    results = reranker.rerank(
        query="Why are some ants inactive?",
        documents=documents,
        top_k=3,
    )

    assert results[0]["text"] == (
        "Some ants remain inactive as reserve workers."
    )