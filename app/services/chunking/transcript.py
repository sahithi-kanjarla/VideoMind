"""Backward-compatible transcript chunking.

Delegates to the generalized content chunker. Import paths that
reference this module continue to work.
"""
from app.models.chunk import ContentChunk
from app.models.source import ContentSegment
from app.services.chunking.content import chunk_content

TranscriptChunk = ContentChunk


def chunk_transcript(
    source_id: str,
    segments: list[ContentSegment],
    target_words: int = 100,
    overlap_segments: int = 1,
) -> list[ContentChunk]:
    """Group transcript segments into timestamp-aware chunks."""
    return chunk_content(source_id, segments, target_words, overlap_segments)
