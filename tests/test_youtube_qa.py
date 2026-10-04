from app.services.youtube_qa import YouTubeQA


class FakeEmbeddings:
    def embed_documents(self, texts):
        return [[0.1] for _ in texts]


class FakeStore:
    def add_chunks(self, chunks, vectors):
        self.chunks = chunks
        self.vectors = vectors


class FakeRetriever:
    def retrieve(self, question, source_id=None):
        self.question = question
        self.source_id = source_id
        return [{"chunk_id": "v-1", "text": "supported excerpt", "metadata": {"start": 312.0}}]


class FakeGenerator:
    def answer(self, question, context):
        return "A concise grounded answer."


def test_load_and_follow_up_queries_use_video_filter(monkeypatch):
    from app.services import youtube_qa as module

    monkeypatch.setattr(module, "fetch_transcript", lambda url: [
        {"start": 312.0, "duration": 2.0, "text": "A timestamped statement from the video."}
    ])
    monkeypatch.setattr(module, "fetch_video_title", lambda url, fallback: "A test video")
    embeddings, store, retriever, generator = FakeEmbeddings(), FakeStore(), FakeRetriever(), FakeGenerator()
    service = YouTubeQA((embeddings, store, retriever, generator))

    video = service.load("https://www.youtube.com/watch?v=Y681hXWwhQY")
    first = service.query(video["video_id"], "What was said?")
    second = service.query(video["video_id"], "Can you explain that simply?")

    assert video["status"] == "ready"
    assert len(store.chunks) == len(store.vectors) == 1
    assert store.chunks[0].metadata["source_type"] == "youtube"
    assert store.chunks[0].metadata["uri"].startswith("https://www.youtube.com/")
    assert first["answer"] == second["answer"] == "A concise grounded answer."
    assert first["sources"][0].label == "05:12"
    assert retriever.source_id == video["video_id"]
    assert retriever.question == "Can you explain that simply?"


def test_empty_question_is_rejected():
    service = YouTubeQA((FakeEmbeddings(), FakeStore(), FakeRetriever(), FakeGenerator()))
    service.videos["Y681hXWwhQY"] = {"video_id": "Y681hXWwhQY"}
    try:
        service.query("Y681hXWwhQY", "   ")
    except ValueError as exc:
        assert "empty" in str(exc).lower()
    else:
        raise AssertionError("Expected empty questions to be rejected")
