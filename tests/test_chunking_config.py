"""Tests for configurable chunking."""
from app.models.source import ContentSegment
from app.services.chunking.content import chunk_content
from app.services.chunking.config import ChunkingConfig


def _seg(text, section=None, page=None):
    return ContentSegment(text=text, section=section, page=page)


class TestChunkingConfig:
    def test_default_behavior_unchanged(self):
        """Default config matches original 100-word target."""
        segments = [_seg(f"word{i} " * 20) for i in range(10)]
        chunks = chunk_content("src1", segments)
        # ~200 words per 10 segments, should produce ~2 chunks at 100-word target
        assert len(chunks) >= 2

    def test_custom_target_words(self):
        segments = [_seg("hello world " * 10) for _ in range(5)]
        # 20 words per segment, 5 segments = 100 words total
        config = ChunkingConfig(target_words=50, overlap_segments=0)
        chunks = chunk_content("src1", segments, config=config)
        # At 50-word target, 100 words should give ~2 chunks
        assert len(chunks) >= 2

    def test_explicit_params_override_config(self):
        segments = [_seg("word " * 50) for _ in range(4)]
        config = ChunkingConfig(target_words=200)
        # Explicit target_words=50 should override config's 200
        chunks = chunk_content("src1", segments, target_words=50, config=config)
        assert len(chunks) >= 3

    def test_section_boundary_respect(self):
        segments = [
            _seg("First section content one.", section="Intro"),
            _seg("First section content two.", section="Intro"),
            _seg("Second section content.", section="Methods"),
            _seg("More methods content here.", section="Methods"),
        ]
        config = ChunkingConfig(
            target_words=500,  # High enough to not trigger word-count split
            respect_section_boundaries=True,
            overlap_segments=0,
        )
        chunks = chunk_content("src1", segments, config=config)
        # Should split at section boundary even though word count is low
        assert len(chunks) == 2
        assert "First section" in chunks[0].text
        assert "Second section" in chunks[1].text

    def test_max_chunk_words_ceiling(self):
        segments = [_seg("word " * 100) for _ in range(5)]
        config = ChunkingConfig(target_words=1000, max_chunk_words=150, overlap_segments=0)
        chunks = chunk_content("src1", segments, config=config)
        # 500 words total, max 150 per chunk, should produce >=3 chunks
        assert len(chunks) >= 3
