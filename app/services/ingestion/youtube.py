import re
from urllib.parse import parse_qs, urlparse
from youtube_transcript_api import YouTubeTranscriptApi
from app.models.source import NormalizedSource, TranscriptSegment

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
    transcripts = api.list(video_id)

    # Prefer manually created English transcripts.
    for transcript in transcripts:
        if transcript.language_code.startswith("en") and not transcript.is_generated:
            fetched = transcript.fetch()

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
            fetched = transcript.fetch()

            return [
                {
                    "start": snippet.start,
                    "duration": snippet.duration,
                    "text": snippet.text,
                }
                for snippet in fetched
            ]

    raise ValueError("No English transcript available for this video")

def normalize_youtube_transcript(
    url: str,
    segments: list[dict],
) -> NormalizedSource:
    """Convert YouTube transcript segments into the VideoMind format."""

    video_id = extract_video_id(url)

    normalized_segments = [
        TranscriptSegment(
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