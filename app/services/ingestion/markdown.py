"""Markdown ingestor — splits on headings into section-aware segments."""

import re
import uuid
from pathlib import Path

from app.models.source import ContentSegment, NormalizedSource


class MarkdownIngestor:
    source_type = "markdown"

    def ingest(self, input_value: str | Path, **kwargs) -> NormalizedSource:
        path = Path(input_value)
        if not path.exists():
            raise ValueError(f"File not found: {path}")

        content = path.read_text(encoding="utf-8")
        segments = _parse_markdown(content)

        if not segments:
            raise ValueError("Markdown file has no content.")

        title = kwargs.get("title") or path.stem

        return NormalizedSource(
            source_id=str(uuid.uuid4()),
            source_type="markdown",
            title=title,
            uri=str(path),
            segments=segments,
        )


def _parse_markdown(content: str) -> list[ContentSegment]:
    segments: list[ContentSegment] = []
    current_section: str | None = None
    paragraph_idx = 0

    for line in content.split("\n"):
        stripped = line.strip()

        heading_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading_match:
            current_section = heading_match.group(2).strip()
            continue

        if not stripped:
            continue

        paragraph_idx += 1
        segments.append(ContentSegment(
            text=stripped,
            section=current_section,
            paragraph_index=paragraph_idx,
        ))

    return segments
