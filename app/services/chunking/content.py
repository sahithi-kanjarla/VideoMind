from app.models.chunk import ContentChunk
from app.models.source import ContentSegment


def chunk_content(
    source_id: str,
    segments: list[ContentSegment],
    target_words: int = 100,
    overlap_segments: int = 1,
) -> list[ContentChunk]:
    """Group content segments into chunks, preserving location metadata."""

    if not segments:
        return []

    chunks: list[ContentChunk] = []
    current_segments: list[ContentSegment] = []
    current_words = 0
    chunk_number = 0

    for segment in segments:
        current_segments.append(segment)
        current_words += len(segment.text.split())

        if current_words >= target_words:
            chunk_number += 1
            chunks.append(
                _create_chunk(source_id, chunk_number, current_segments)
            )
            overlap = current_segments[-overlap_segments:]
            current_segments = overlap.copy()
            current_words = sum(len(s.text.split()) for s in current_segments)

    if current_segments:
        chunk_number += 1
        chunks.append(
            _create_chunk(source_id, chunk_number, current_segments)
        )

    return chunks


def _create_chunk(
    source_id: str,
    chunk_number: int,
    segments: list[ContentSegment],
) -> ContentChunk:
    text = " ".join(segment.text.strip() for segment in segments)

    first = segments[0]
    last = segments[-1]

    return ContentChunk(
        chunk_id=f"{source_id}-{chunk_number}",
        source_id=source_id,
        text=text,
        start=first.start,
        end=last.end,
        page=first.page,
        section=first.section,
        paragraph_index=first.paragraph_index,
        metadata={
            "chunk_id": f"{source_id}-{chunk_number}",
            "segment_count": len(segments),
        },
    )
