import re
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from urllib.request import urlopen
from youtube_transcript_api import YouTubeTranscriptApi
from app.models.source import ContentSegment, NormalizedSource

YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "youtu.be",
}


def extract_video_id(url: str) -> str:
    """Extract an 11-character YouTube video ID from a supported URL."""

    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if host not in YOUTUBE_HOSTS:
        raise ValueError("Invalid YouTube URL")

    # https://youtu.be/VIDEO_ID
    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]

    # https://youtube.com/watch?v=VIDEO_ID
    elif parsed.path == "/watch":
        video_id = parse_qs(parsed.query).get("v", [None])[0]

    # https://youtube.com/shorts/VIDEO_ID
    elif parsed.path.startswith("/shorts/"):
        video_id = parsed.path.split("/")[2]

    # https://youtube.com/embed/VIDEO_ID
    elif parsed.path.startswith("/embed/"):
        video_id = parsed.path.split("/")[2]

    else:
        raise ValueError("Unsupported YouTube URL format")

    if not video_id or not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise ValueError("Invalid YouTube video ID")

    return video_id

def fetch_transcript(url: str) -> list[dict]:
    """Fetch the best available English transcript from a YouTube video."""

    video_id = extract_video_id(url)

    api = YouTubeTranscriptApi()
    try:
        transcripts = api.list(video_id)
    except Exception as exc:
        raise ValueError(f"Transcript unavailable: {exc}") from exc

    # Prefer manually created English transcripts.
    for transcript in transcripts:
        if transcript.language_code.startswith("en") and not transcript.is_generated:
            try:
                fetched = transcript.fetch()
            except Exception as exc:
                raise ValueError(f"Transcript unavailable: {exc}") from exc

            return [
                {
                    "start": snippet.start,
                    "duration": snippet.duration,
                    "text": snippet.text,
                }
                for snippet in fetched
            ]

    # Fall back to generated English transcripts.
    for transcript in transcripts:
        if transcript.language_code.startswith("en") and transcript.is_generated:
            try:
                fetched = transcript.fetch()
            except Exception as exc:
                raise ValueError(f"Transcript unavailable: {exc}") from exc

            return [
                {
                    "start": snippet.start,
                    "duration": snippet.duration,
                    "text": snippet.text,
                }
                for snippet in fetched
            ]

    raise ValueError("No English transcript available for this video")


def fetch_video_title(url: str, fallback: str) -> str:
    """Return the public YouTube oEmbed title, falling back to the video ID."""
    import urllib.parse

    endpoint = "https://www.youtube.com/oembed?" + urllib.parse.urlencode(
        {"url": url, "format": "json"}
    )
    try:
        with urlopen(endpoint, timeout=5) as response:
            return json.loads(response.read()).get("title") or fallback
    except Exception:
        return fallback

def normalize_youtube_transcript(
    url: str,
    segments: list[dict],
) -> NormalizedSource:
    """Convert YouTube transcript segments into the VideoMind format."""

    video_id = extract_video_id(url)

    normalized_segments = [
        ContentSegment(
            text=segment["text"],
            start=segment["start"],
            end=segment["start"] + segment["duration"],
        )
        for segment in segments
    ]

    return NormalizedSource(
        source_id=video_id,
        source_type="youtube",
        uri=url,
        segments=normalized_segments,
    )


class YouTubeIngestor:
    source_type = "youtube"

    def ingest(self, input_value: str | Path, **kwargs) -> NormalizedSource:
        url = str(input_value)
        extract_video_id(url)
        raw_segments = fetch_transcript(url)
        source = normalize_youtube_transcript(url, raw_segments)
        source.title = fetch_video_title(url, f"YouTube video {source.source_id}")
        return source
