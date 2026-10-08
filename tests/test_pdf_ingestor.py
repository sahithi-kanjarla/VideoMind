"""Tests for PDF ingestor."""
import tempfile
from pathlib import Path
import pytest

from app.services.ingestion.pdf import _parse_markdown_segments, PDFIngestor


class TestParseMarkdownSegments:
    def test_basic_paragraphs(self):
        md = "First paragraph.\n\nSecond paragraph."
        segments = _parse_markdown_segments(md)
        assert len(segments) == 2
        assert segments[0].text == "First paragraph."
        assert segments[1].text == "Second paragraph."

    def test_headings_become_sections(self):
        md = "## Introduction\n\nSome intro text.\n\n## Methods\n\nSome methods text."
        segments = _parse_markdown_segments(md)
        assert len(segments) == 2
        assert segments[0].section == "Introduction"
        assert segments[1].section == "Methods"

    def test_page_breaks_increment_page(self):
        md = "Page one text.\n\n---\n\nPage two text.\n\n-----\n\nPage three text."
        segments = _parse_markdown_segments(md)
        assert segments[0].page == 1
        assert segments[1].page == 2
        assert segments[2].page == 3

    def test_empty_lines_skipped(self):
        md = "\n\n\nSome text.\n\n\n"
        segments = _parse_markdown_segments(md)
        assert len(segments) == 1

    def test_paragraph_index_resets_per_page(self):
        md = "Para one.\n\nPara two.\n\n---\n\nPara three."
        segments = _parse_markdown_segments(md)
        assert segments[0].paragraph_index == 1
        assert segments[1].paragraph_index == 2
        # After page break, index resets
        assert segments[2].paragraph_index == 1


class TestPDFIngestor:
    def test_file_not_found_raises(self):
        ingestor = PDFIngestor()
        with pytest.raises(ValueError, match="File not found"):
            ingestor.ingest("/nonexistent/file.pdf")
