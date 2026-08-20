from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.ingestion import load_articles
from backend.models import Article

__all__ = [
    "Article",
    "Document",
    "chunk_article",
    "index_documents",
    "load_articles",
    "retrieve_documents",
]


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


def index_documents(
    documents: list[Document],
    *,
    embedding: Embeddings,
    persist_directory: str | Path,
    collection_name: str = "xuzhe_articles",
) -> Chroma:
    """Embed and upsert already-chunked documents into a persistent Chroma collection."""
    document_ids = [
        f"{document.metadata['article_id']}:{document.metadata['position']}"
        for document in documents
    ]
    vector_store = Chroma(
        embedding_function=embedding,
        collection_name=collection_name,
        persist_directory=str(persist_directory),
    )
    vector_store.add_documents(documents, ids=document_ids)

    return vector_store


def retrieve_documents(
    vector_store: Chroma, query: str, *, k: int = 5
) -> list[tuple[Document, float]]:
    """Return the top-k chunks and relevance scores for one query."""
    if k <= 0:
        raise TypeError(f"Number of requested results {k}, cannot be negative, or zero.")
    if query.strip() == "":
        raise TypeError("Query cannot be empty.")
    
    result = vector_store.similarity_search_with_score(
        query=query,
        k = k,
    )
    return result
