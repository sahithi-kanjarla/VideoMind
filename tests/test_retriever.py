from app.services.retrieval.retriever import Retriever


def make_retriever():
    return Retriever(
        embedding_service=None,
        vector_store=None,
        reranker=None,
    )


def test_adaptive_selector_keeps_results_before_large_gap():
    retriever = make_retriever()

    results = [
        {"chunk_id": "1", "text": "A", "score": 8.5, "metadata": {}},
        {"chunk_id": "2", "text": "B", "score": 8.1, "metadata": {}},
        {"chunk_id": "3", "text": "C", "score": 7.8, "metadata": {}},
        {"chunk_id": "4", "text": "D", "score": 3.0, "metadata": {}},
        {"chunk_id": "5", "text": "E", "score": 2.5, "metadata": {}},
    ]

    selected = retriever._select_relevant(results)

    assert [item["chunk_id"] for item in selected] == [
        "1",
        "2",
        "3",
    ]


def test_adaptive_selector_limits_results_when_no_large_gap():
    retriever = make_retriever()

    results = [
        {"chunk_id": "1", "text": "A", "score": 8.5, "metadata": {}},
        {"chunk_id": "2", "text": "B", "score": 8.0, "metadata": {}},
        {"chunk_id": "3", "text": "C", "score": 7.5, "metadata": {}},
        {"chunk_id": "4", "text": "D", "score": 7.0, "metadata": {}},
        {"chunk_id": "5", "text": "E", "score": 6.5, "metadata": {}},
        {"chunk_id": "6", "text": "F", "score": 6.0, "metadata": {}},
        {"chunk_id": "7", "text": "G", "score": 5.5, "metadata": {}},
        {"chunk_id": "8", "text": "H", "score": 5.0, "metadata": {}},
        {"chunk_id": "9", "text": "I", "score": 4.5, "metadata": {}},
    ]

    selected = retriever._select_relevant(results)

    assert len(selected) == 5


def test_adaptive_selector_handles_single_result():
    retriever = make_retriever()

    results = [
        {"chunk_id": "1", "text": "A", "score": 8.5, "metadata": {}},
    ]

    selected = retriever._select_relevant(results)

    assert len(selected) == 1
    assert selected[0]["chunk_id"] == "1"


def test_adaptive_selector_handles_empty_results():
    retriever = make_retriever()

    assert retriever._select_relevant([]) == []