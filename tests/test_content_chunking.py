from app.models.source import ContentSegment
from app.services.chunking.content import chunk_content


def test_chunk_content_with_timestamps():
    segments = [
        ContentSegment(text="Hello world this is segment one", start=0.0, end=5.0),
        ContentSegment(text="And this is segment two with more words added here", start=5.0, end=10.0),
        ContentSegment(text="Third segment completes the first chunk nicely now", start=10.0, end=15.0),
    ]
    chunks = chunk_content("src1", segments, target_words=15, overlap_segments=1)
    assert len(chunks) >= 1
    assert chunks[0].source_id == "src1"
    assert chunks[0].start == 0.0
    assert chunks[0].chunk_id == "src1-1"


def test_chunk_content_with_pages():
    segments = [
        ContentSegment(text="Page one content here with enough words to fill", page=1, section="Intro"),
        ContentSegment(text="More content on page one with additional details", page=1, section="Intro"),
        ContentSegment(text="Page two starts here with new content for reading", page=2, section="Methods"),
    ]
    chunks = chunk_content("doc1", segments, target_words=10, overlap_segments=1)
    assert len(chunks) >= 2
    assert chunks[0].page == 1
    assert chunks[0].section == "Intro"


def test_chunk_content_empty():
    chunks = chunk_content("src1", [])
    assert chunks == []


def test_backward_compat_transcript_chunk():
    from app.models.chunk import TranscriptChunk, ContentChunk
    assert TranscriptChunk is ContentChunk


def test_backward_compat_transcript_segment():
    from app.models.source import TranscriptSegment, ContentSegment
    assert TranscriptSegment is ContentSegment


def test_backward_compat_chunk_transcript():
    from app.services.chunking.transcript import chunk_transcript
    segments = [
        ContentSegment(text="Hello world test", start=0.0, end=3.0),
        ContentSegment(text="More text here now", start=3.0, end=6.0),
    ]
    chunks = chunk_transcript("yt1", segments, target_words=5, overlap_segments=1)
    assert len(chunks) >= 1
    assert chunks[0].start == 0.0
