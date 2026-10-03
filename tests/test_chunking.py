from app.models.source import TranscriptSegment
from app.services.chunking.transcript import chunk_transcript


def test_chunk_transcript():
    segments = [
        TranscriptSegment(
            text="This is the first segment.",
            start=0.0,
            end=2.0,
        ),
        TranscriptSegment(
            text="This is the second segment.",
            start=2.0,
            end=4.0,
        ),
        TranscriptSegment(
            text="This is the third segment.",
            start=4.0,
            end=6.0,
        ),
    ]

    chunks = chunk_transcript(
        source_id="test-video",
        segments=segments,
        target_words=8,
        overlap_segments=1,
    )

    assert len(chunks) >= 1
    assert chunks[0].source_id == "test-video"
    assert chunks[0].start == 0.0
    assert chunks[0].end is not None
    assert chunks[0].text


def test_empty_transcript_returns_no_chunks():
    chunks = chunk_transcript(
        source_id="test-video",
        segments=[],
    )

    assert chunks == []