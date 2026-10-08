from app.models.chunk import ContentChunk
from app.models.source import ContentSegment
from app.services.chunking.config import ChunkingConfig, DEFAULT_CONFIG


def chunk_content(
    source_id: str,
    segments: list[ContentSegment],
    target_words: int | None = None,
    overlap_segments: int | None = None,
    config: ChunkingConfig | None = None,
) -> list[ContentChunk]:
    """Group content segments into chunks, preserving location metadata.

    Accepts either explicit target_words/overlap_segments (backward compat)
    or a ChunkingConfig for full control.
    """
    if config is None:
        config = DEFAULT_CONFIG

    tw = target_words if target_words is not None else config.target_words
    ov = overlap_segments if overlap_segments is not None else config.overlap_segments

    if not segments:
        return []

    chunks: list[ContentChunk] = []
    current_segments: list[ContentSegment] = []
    current_words = 0
    chunk_number = 0

    for i, segment in enumerate(segments):
        # Section boundary: flush the current chunk if configured
        if (
            config.respect_section_boundaries
            and current_segments
            and _section_changed(current_segments[-1], segment)
            and current_words > 0
        ):
            chunk_number += 1
            chunks.append(_create_chunk(source_id, chunk_number, current_segments))
            current_segments = []
            current_words = 0

        current_segments.append(segment)
        current_words += len(segment.text.split())

        # Hard ceiling — never exceed max_chunk_words
        should_flush = current_words >= tw or current_words >= config.max_chunk_words

        if should_flush:
            chunk_number += 1
            chunks.append(_create_chunk(source_id, chunk_number, current_segments))
            overlap = current_segments[-ov:] if ov > 0 else []
            current_segments = list(overlap)
            current_words = sum(len(s.text.split()) for s in current_segments)

    if current_segments:
        chunk_number += 1
        chunks.append(_create_chunk(source_id, chunk_number, current_segments))

    return chunks


def _section_changed(prev: ContentSegment, curr: ContentSegment) -> bool:
    return (
        prev.section is not None
        and curr.section is not None
        and prev.section != curr.section
    )


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
