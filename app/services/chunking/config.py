from dataclasses import dataclass, field


@dataclass
class ChunkingConfig:
    """Configurable chunking parameters — tunable per benchmark run."""
    target_words: int = 100
    overlap_segments: int = 1
    # When True, force chunk boundaries at section/heading changes
    respect_section_boundaries: bool = False
    # Max words before forcing a split even mid-section
    max_chunk_words: int = 300

# Shared default — import and override for benchmarks
DEFAULT_CONFIG = ChunkingConfig()
