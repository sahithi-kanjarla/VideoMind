from functools import lru_cache

from app.core.config import settings
from app.models.source import NormalizedSource
from app.schemas.youtube import SourceTimestamp
from app.services.chunking.transcript import chunk_transcript
from app.services.embeddings.service import EmbeddingService
from app.services.ingestion.youtube import (
    extract_video_id,
    fetch_transcript,
    fetch_video_title,
    normalize_youtube_transcript,
)
from app.services.rag.gemini import GeminiGenerator
from app.services.retrieval.reranker import Reranker
from app.services.retrieval.retriever import Retriever
from app.services.vector_store.chroma import ChromaVectorStore


@lru_cache(maxsize=1)
def get_services():
    embeddings = EmbeddingService()
    store = ChromaVectorStore(persist_directory=settings.chroma_path)
    reranker = Reranker()
    return embeddings, store, Retriever(embeddings, store, reranker), GeminiGenerator()


class YouTubeQA:
    def __init__(self, services=None):
        self.embeddings, self.store, self.retriever, self.generator = services or get_services()
        self.videos: dict[str, dict] = {}

    def load(self, url: str) -> dict:
        video_id = extract_video_id(url)
        raw_segments = fetch_transcript(url)
        source: NormalizedSource = normalize_youtube_transcript(url, raw_segments)
        chunks = chunk_transcript(source.source_id, source.segments)
        if not chunks:
            raise ValueError("The video transcript is empty.")
        for chunk in chunks:
            chunk.metadata.update({"source_type": "youtube", "uri": url})
        vectors = self.embeddings.embed_documents([chunk.text for chunk in chunks])
        self.store.add_chunks(chunks, vectors)
        video = {
            "video_id": video_id,
            "url": url,
            "title": fetch_video_title(url, f"YouTube video {video_id}"),
            "status": "ready",
            "chunks": len(chunks),
        }
        self.videos[video_id] = video
        return video

    def get_video(self, video_id: str) -> dict | None:
        return self.videos.get(video_id)

    def query(self, video_id: str, question: str) -> dict:
        question = question.strip()
        if not question:
            raise ValueError("Question cannot be empty.")
        video = self.videos.get(video_id)
        if video is None:
            raise LookupError("Video is not loaded. Load its YouTube URL first.")
        context = self.retriever.retrieve(question, source_id=video_id)
        if not context:
            return {"answer": "I couldn't find information about that in this video's transcript.", "sources": []}
        answer = self.generator.answer(question, context)
        seen = set()
        sources = []
        for item in context:
            start = float(item["metadata"].get("start") or 0)
            second = int(start)
            if second in seen:
                continue
            seen.add(second)
            sources.append(SourceTimestamp(start=start, label=f"{second // 60:02d}:{second % 60:02d}"))
            if len(sources) == 3:
                break
        return {"answer": answer, "sources": sources}
