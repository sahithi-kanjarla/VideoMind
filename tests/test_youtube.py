import pytest

from app.services.ingestion.youtube import extract_video_id


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