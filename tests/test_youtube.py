import pytest

from app.services.ingestion.youtube import extract_video_id
from app.models.source import NormalizedSource
from app.services.ingestion.youtube import normalize_youtube_transcript

def test_normalize_youtube_transcript():
    url = "https://www.youtube.com/watch?v=Y681hXWwhQY"

    segments = [
        {
            "start": 9.18,
            "duration": 2.76,
            "text": "Hello. This is 6 Minute English from",
        }
    ]

    source = normalize_youtube_transcript(url, segments)

    assert isinstance(source, NormalizedSource)
    assert source.source_id == "Y681hXWwhQY"
    assert source.source_type == "youtube"
    assert source.uri == url

    assert len(source.segments) == 1
    assert source.segments[0].text == "Hello. This is 6 Minute English from"
    assert source.segments[0].start == 9.18
    assert source.segments[0].end == 11.94

def test_extract_watch_url():
    url = "https://www.youtube.com/watch?v=Y681hXWwhQY"

    assert extract_video_id(url) == "Y681hXWwhQY"


def test_extract_short_url():
    url = "https://youtu.be/Y681hXWwhQY"

    assert extract_video_id(url) == "Y681hXWwhQY"


def test_extract_shorts_url():
    url = "https://www.youtube.com/shorts/Y681hXWwhQY"

    assert extract_video_id(url) == "Y681hXWwhQY"


def test_reject_invalid_url():
    with pytest.raises(ValueError):
        extract_video_id("https://example.com/video")