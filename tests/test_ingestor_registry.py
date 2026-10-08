from pathlib import Path

import pytest

from app.models.source import NormalizedSource
from app.services.ingestion.registry import (
    register,
    get_ingestor,
    registered_types,
    _registry,
)


class FakeIngestor:
    source_type = "fake"

    def ingest(self, input_value: str | Path, **kwargs) -> NormalizedSource:
        return NormalizedSource(
            source_id="fake-1",
            source_type="youtube",
            title="Fake Source",
            segments=[],
        )


@pytest.fixture(autouse=True)
def clean_registry():
    saved = dict(_registry)
    yield
    _registry.clear()
    _registry.update(saved)


def test_register_and_get():
    ingestor = FakeIngestor()
    register("fake", ingestor)
    assert get_ingestor("fake") is ingestor


def test_get_unregistered_raises():
    with pytest.raises(ValueError, match="No ingestor registered"):
        get_ingestor("nonexistent")


def test_registered_types():
    register("fake", FakeIngestor())
    assert "fake" in registered_types()
