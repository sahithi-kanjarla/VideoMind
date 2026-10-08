"""Plain text ingestor — splits on double newlines into paragraph segments."""

import uuid
from pathlib import Path

from app.models.source import ContentSegment, NormalizedSource


class TextIngestor:
    source_type = "text"

    def ingest(self, input_value: str | Path, **kwargs) -> NormalizedSource:
        path = Path(input_value)
        if not path.exists():
            raise ValueError(f"File not found: {path}")

        content = path.read_text(encoding="utf-8")
        segments = _split_paragraphs(content)

        if not segments:
            raise ValueError("Text file is empty.")

        title = kwargs.get("title") or path.stem

        return NormalizedSource(
            source_id=str(uuid.uuid4()),
            source_type="text",
            title=title,
            uri=str(path),
            segments=segments,
        )


def _split_paragraphs(content: str) -> list[ContentSegment]:
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    return [
        ContentSegment(text=p, paragraph_index=i + 1)
        for i, p in enumerate(paragraphs)
    ]
