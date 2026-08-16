from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.ingestion import load_articles
from backend.models import Article

__all__ = ["Article", "Document", "chunk_article", "load_articles"]


def chunk_article(
    article: Article, *, target_chars: int = 600, overlap_chars: int = 100
) -> list[Document]:
    """Split one article into stable LangChain documents for later indexing."""
    if target_chars <= 0 or overlap_chars < 0 or target_chars <= overlap_chars:
        raise ValueError("target_chars must be > 0 and overlap_chars must be >= 0")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=target_chars,
        chunk_overlap=overlap_chars,
        separators=[
            "\n\n",
            "\n",
            "。",
            "！",
            "？",
            "；",
            ".",
            "!",
            "?",
            ";",
            "，",
            ",",
            "、",
            " ",
            "",
        ],
    )
    metadata = {
        "article_id": article.id,
        "title": article.title,
        "author": article.author,
        "url": article.url,
        "created_at": article.created_at.isoformat(),
        "updated_at": article.updated_at.isoformat(),
    }

    return [
        Document(
            page_content=content,
            metadata={**metadata, "position": position},
        )
        for position, content in enumerate(text_splitter.split_text(article.text))
    ]
    