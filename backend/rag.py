"""Learner-owned RAG algorithms."""

from langchain_text_splitters import RecursiveCharacterTextSplitter # Temp; Use semantic splitter when available
from langchain_core.documents import Document

from backend.ingestion import load_articles
from backend.models import Article

__all__ = ["Article", "Document", "chunk_article", "load_articles"]


def chunk_article(
    article: Article, *, target_chars: int = 600, overlap_chars: int = 100
) -> list[Document]:
    """Split one article into stable LangChain documents for later indexing."""
    text_splitter = RecursiveCharacterTextSplitter(
        separators=[
            "\n\n",
            "\n",
            "\uff0c",  # Fullwidth comma
            "\u3001",  # Ideographic comma
            "\uff0e",  # Fullwidth full stop
            "\u3002",  # Ideographic full stop
        ],
    )
    chunks = text_splitter.split_text(article.text)
    return chunks
