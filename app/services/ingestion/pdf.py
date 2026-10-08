"""PDF ingestor — extracts text as Markdown via pymupdf4llm, then parses
into ContentSegments with page numbers and section headings."""

import re
import uuid
from pathlib import Path

import pymupdf4llm

from app.models.source import ContentSegment, NormalizedSource


class PDFIngestor:
    source_type = "pdf"

    def ingest(self, input_value: str | Path, **kwargs) -> NormalizedSource:
        path = Path(input_value)
        if not path.exists():
            raise ValueError(f"File not found: {path}")

        md_text = pymupdf4llm.to_markdown(str(path))
        segments = _parse_markdown_segments(md_text)

        if not segments:
            raise ValueError("PDF produced no extractable text.")

        title = kwargs.get("title") or path.stem

        return NormalizedSource(
            source_id=str(uuid.uuid4()),
            source_type="pdf",
            title=title,
            uri=str(path),
            segments=segments,
        )


def _parse_markdown_segments(md_text: str) -> list[ContentSegment]:
    """Split pymupdf4llm Markdown output into segments.

    pymupdf4llm emits page breaks as "-----" or "---" separators,
    and headings as "# Heading" / "## Heading" lines.
    """
    segments: list[ContentSegment] = []
    current_section: str | None = None
    current_page = 1
    paragraph_idx = 0

    for line in md_text.split("\n"):
        stripped = line.strip()

        # Page break marker — pymupdf4llm uses horizontal rules
        if re.fullmatch(r"-{3,}", stripped):
            current_page += 1
            paragraph_idx = 0
            continue

        # Heading — becomes the section name
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading_match:
            current_section = heading_match.group(2).strip()
            continue

        # Skip empty lines
        if not stripped:
            continue

        paragraph_idx += 1
        segments.append(ContentSegment(
            text=stripped,
            page=current_page,
            section=current_section,
            paragraph_index=paragraph_idx,
        ))

    return segments
