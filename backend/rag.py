"""Learner-owned RAG algorithms.

Implement only the function named by the current exercise. Later stages will be
added here after review; avoid designing them in advance.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Article:
    """Canonical article passed from ingestion to later RAG stages."""

    id: str
    title: str
    author: str
    url: str
    created_at: datetime
    updated_at: datetime
    text: str


def load_saved_metadata(metadata_dir: Path) -> list[Article]:
    """Load saved crawler JSON as deterministic canonical articles."""
    raise NotImplementedError("Complete Exercise 01: saved metadata ingestion")
