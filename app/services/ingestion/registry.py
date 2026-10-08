from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from app.models.source import NormalizedSource


@runtime_checkable
class Ingestor(Protocol):
    source_type: str

    def ingest(self, input_value: str | Path, **kwargs) -> NormalizedSource: ...


_registry: dict[str, Ingestor] = {}


def register(source_type: str, ingestor: Ingestor) -> None:
    _registry[source_type] = ingestor


def get_ingestor(source_type: str) -> Ingestor:
    ingestor = _registry.get(source_type)
    if ingestor is None:
        raise ValueError(f"No ingestor registered for source type: {source_type}")
    return ingestor


def registered_types() -> list[str]:
    return list(_registry.keys())
