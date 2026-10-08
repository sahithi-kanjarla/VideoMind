"""Tests for text and markdown ingestors."""
import tempfile
from pathlib import Path
import pytest

from app.services.ingestion.text import TextIngestor, _split_paragraphs
from app.services.ingestion.markdown import MarkdownIngestor, _parse_markdown


class TestTextSplitParagraphs:
    def test_double_newline_split(self):
        content = "First paragraph.\n\nSecond paragraph.\n\nThird."
        segments = _split_paragraphs(content)
        assert len(segments) == 3
        assert segments[0].text == "First paragraph."
        assert segments[2].paragraph_index == 3

    def test_empty_content(self):
        assert _split_paragraphs("") == []
        assert _split_paragraphs("   \n\n   ") == []


class TestTextIngestor:
    def test_ingest_real_file(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as tmp:
            tmp.write("Hello world.\n\nSecond paragraph.")
            tmp_path = Path(tmp.name)

        try:
            result = TextIngestor().ingest(tmp_path)
            assert result.source_type == "text"
            assert len(result.segments) == 2
        finally:
            tmp_path.unlink()


class TestMarkdownParse:
    def test_headings_and_content(self):
        md = "# Title\n\nIntro text.\n\n## Section A\n\nContent A.\n\n## Section B\n\nContent B."
        segments = _parse_markdown(md)
        assert len(segments) == 3
        assert segments[0].section == "Title"
        assert segments[1].section == "Section A"
        assert segments[2].section == "Section B"

    def test_no_headings(self):
        md = "Just some text.\n\nAnother line."
        segments = _parse_markdown(md)
        assert len(segments) == 2
        assert segments[0].section is None


class TestMarkdownIngestor:
    def test_ingest_real_file(self):
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as tmp:
            tmp.write("# My Doc\n\nSome content here.")
            tmp_path = Path(tmp.name)

        try:
            result = MarkdownIngestor().ingest(tmp_path)
            assert result.source_type == "markdown"
            assert len(result.segments) == 1
            assert result.segments[0].section == "My Doc"
        finally:
            tmp_path.unlink()
