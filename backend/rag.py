"""Learner-owned RAG algorithms."""

from langchain_core.documents import Document

from backend.ingestion import load_articles
from backend.models import Article

__all__ = ["Article", "Document", "chunk_article", "load_articles"]


def chunk_article(
    article: Article, *, target_chars: int = 600, overlap_chars: int = 100
) -> list[Document]:
    """Split one article into stable LangChain documents for later indexing."""
    raise NotImplementedError("Complete Exercise 02: LangChain text splitting")
