"""DOCX ingestor — extracts paragraphs with heading-based sections."""

import uuid
from pathlib import Path

from docx import Document

from app.models.source import ContentSegment, NormalizedSource


class DocxIngestor:
    source_type = "docx"

    def ingest(self, input_value: str | Path, **kwargs) -> NormalizedSource:
        path = Path(input_value)
        if not path.exists():
            raise ValueError(f"File not found: {path}")

        doc = Document(str(path))
        segments = _extract_segments(doc)

        if not segments:
            raise ValueError("DOCX produced no extractable text.")

        title = kwargs.get("title") or path.stem

        return NormalizedSource(
            source_id=str(uuid.uuid4()),
            source_type="docx",
            title=title,
            uri=str(path),
            segments=segments,
        )


def _extract_segments(doc: Document) -> list[ContentSegment]:
    segments: list[ContentSegment] = []
    current_section: str | None = None
    paragraph_idx = 0

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        # python-docx style names: 'Heading 1', 'Heading 2', etc.
        if para.style and para.style.name and para.style.name.startswith("Heading"):
            current_section = text
            continue

        paragraph_idx += 1
        segments.append(ContentSegment(
            text=text,
            section=current_section,
            paragraph_index=paragraph_idx,
        ))

    return segments
