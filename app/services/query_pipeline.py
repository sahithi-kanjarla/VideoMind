from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.core.config import settings
from app.schemas.chat import Citation
from app.services.chunking.content import chunk_content
from app.services.conversation_service import ConversationService
from app.services.embeddings.service import EmbeddingService
from app.services.ingestion.registry import get_ingestor
from app.services.message_service import MessageService
from app.services.rag.groq_service import GroqGenerator
from app.services.retrieval.reranker import Reranker
from app.services.retrieval.retriever import Retriever
from app.services.source_service import SourceService
from app.services.vector_store.chroma import ChromaVectorStore


@lru_cache(maxsize=1)
def get_services():
    embeddings = EmbeddingService()
    store = ChromaVectorStore(persist_directory=settings.chroma_path)
    reranker = Reranker()
    retriever = Retriever(embeddings, store, reranker)
    generator = GroqGenerator()
    return embeddings, store, retriever, generator


class QueryPipeline:
    def __init__(self, services=None):
        self.embeddings, self.store, self.retriever, self.generator = (
            services or get_services()
        )

    def ingest_source(
        self,
        conversation_id: str,
        source_type: str,
        input_value: str | Path,
    ) -> dict:
        ingestor = get_ingestor(source_type)
        normalized = ingestor.ingest(input_value)

        chunks = chunk_content(normalized.source_id, normalized.segments)
        if not chunks:
            raise ValueError("Source produced no content chunks.")

        for chunk in chunks:
            chunk.metadata.update({
                "source_type": source_type,
                "uri": str(normalized.uri or input_value),
            })

        vectors = self.embeddings.embed_documents([c.text for c in chunks])
        self.store.add_chunks(chunks, vectors)

        source = SourceService.create(
            name=normalized.title or f"{source_type} source",
            source_type=source_type,
            uri=str(normalized.uri or input_value),
            metadata={
                "chunk_count": len(chunks),
                "source_id": normalized.source_id,
                "language": normalized.language,
            },
        )

        SourceService.update_status(source["id"], "ready")
        SourceService.link_to_conversation(conversation_id, source["id"])

        return {
            "source_id": normalized.source_id,
            "db_source_id": source["id"],
            "name": normalized.title or f"{source_type} source",
            "source_type": source_type,
            "status": "ready",
            "chunks": len(chunks),
        }

    def query(self, conversation_id: str, question: str) -> dict:
        question = question.strip()
        if not question:
            raise ValueError("Question cannot be empty.")

        conversation = ConversationService.get(conversation_id)
        if conversation is None:
            raise LookupError("Conversation not found.")

        source_records = SourceService.get_conversation_sources(conversation_id)
        if not source_records:
            return {
                "answer": "No sources have been added to this conversation yet. "
                "Add a YouTube video, document, or other source first.",
                "citations": [],
                "answerable": False,
            }

        source_ids = [
            s.get("metadata", {}).get("source_id", s["id"])
            for s in source_records
        ]

        context = self.retriever.retrieve(question, source_ids=source_ids)
        if not context:
            return {
                "answer": "I couldn't find relevant information in the provided sources.",
                "citations": [],
                "answerable": False,
            }

        answer = self.generator.answer(question, context)

        citations = self._build_citations(context, source_records)

        MessageService.append(conversation_id, "user", question)
        MessageService.append(
            conversation_id,
            "assistant",
            answer,
            citations=[c.model_dump() for c in citations],
        )

        return {
            "answer": answer,
            "citations": [c.model_dump() for c in citations],
            "answerable": True,
        }

    def _build_citations(
        self,
        context: list[dict],
        source_records: list[dict],
    ) -> list[Citation]:
        source_type_map = {
            s.get("metadata", {}).get("source_id", s["id"]): s.get("source_type", "unknown")
            for s in source_records
        }

        seen: set[str] = set()
        citations: list[Citation] = []

        for item in context:
            meta = item.get("metadata", {})
            src_id = meta.get("source_id", "")
            src_type = source_type_map.get(src_id, meta.get("source_type", "unknown"))
            start = meta.get("start")
            page = meta.get("page")
            section = meta.get("section")

            if src_type in ("youtube", "video", "audio") and start is not None:
                second = int(float(start))
                key = f"{src_id}:{second}"
                if key in seen:
                    continue
                seen.add(key)
                label = f"{second // 60:02d}:{second % 60:02d}"
                citations.append(Citation(
                    source_id=src_id,
                    source_type=src_type,
                    label=label,
                    start=float(start),
                ))
            elif page is not None:
                key = f"{src_id}:p{page}"
                if key in seen:
                    continue
                seen.add(key)
                citations.append(Citation(
                    source_id=src_id,
                    source_type=src_type,
                    label=f"Page {page}",
                    page=page,
                ))
            elif section:
                key = f"{src_id}:s:{section}"
                if key in seen:
                    continue
                seen.add(key)
                citations.append(Citation(
                    source_id=src_id,
                    source_type=src_type,
                    label=section,
                    section=section,
                ))

            if len(citations) >= 5:
                break

        return citations
