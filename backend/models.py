"""Framework-independent domain models shared by RAG stages."""

from dataclasses import dataclass
from datetime import datetime


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

