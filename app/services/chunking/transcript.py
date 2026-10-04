from app.models.chunk import TranscriptChunk
from app.models.source import TranscriptSegment


def chunk_transcript(
    source_id: str,
    segments: list[TranscriptSegment],
    target_words: int = 100,
    overlap_segments: int = 1,
) -> list[TranscriptChunk]:
    """Group transcript segments into timestamp-aware chunks."""

    if not segments:
        return []

    chunks = []
    current_segments = []
    current_words = 0
    chunk_number = 0

    for segment in segments:
        current_segments.append(segment)
        current_words += len(segment.text.split())

        if current_words >= target_words:
            chunk_number += 1

            chunks.append(
                _create_chunk(
                    source_id,
                    chunk_number,
                    current_segments,
                )
            )

            overlap = current_segments[-overlap_segments:]

            current_segments = overlap.copy()
            current_words = sum(
                len(item.text.split()) for item in current_segments
            )

    if current_segments:
        chunk_number += 1

        chunks.append(
            _create_chunk(
                source_id,
                chunk_number,
                current_segments,
            )
        )

    return chunks


def _create_chunk(
    source_id: str,
    chunk_number: int,
    segments: list[TranscriptSegment],
) -> TranscriptChunk:

    text = " ".join(segment.text.strip() for segment in segments)

    start = segments[0].start
    end = segments[-1].end

    return TranscriptChunk(
        chunk_id=f"{source_id}-{chunk_number}",
        source_id=source_id,
        text=text,
        start=start,
        end=end,
        metadata={
            "chunk_id": f"{source_id}-{chunk_number}",
            "segment_count": len(segments),
        },
    )
