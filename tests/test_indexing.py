from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from backend.rag import index_documents


class KeywordEmbeddings(Embeddings):
    """Small deterministic test double; no model download or API call."""

    @staticmethod
    def _embed(text: str) -> list[float]:
        return [1.0, 0.0] if "债券" in text or "利率" in text else [0.0, 1.0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


def make_documents() -> list[Document]:
    common = {
        "article_id": "answer-123",
        "title": "测试文章",
        "author": "测试作者",
        "url": "https://www.zhihu.com/question/1/answer/123",
    }
    return [
        Document(
            page_content="债券价格通常与利率反向变化。",
            metadata={**common, "position": 0},
        ),
        Document(
            page_content="自由现金流可用于企业估值。",
            metadata={**common, "position": 1},
        ),
    ]


def test_repeated_indexing_is_idempotent(tmp_path: Path) -> None:
    first = index_documents(
        make_documents(),
        embedding=KeywordEmbeddings(),
        persist_directory=tmp_path,
    )
    first_ids = first.get()["ids"]

    second = index_documents(
        make_documents(),
        embedding=KeywordEmbeddings(),
        persist_directory=tmp_path,
    )
    second_ids = second.get()["ids"]

    assert len(first_ids) == 2
    assert len(set(first_ids)) == 2
    assert set(second_ids) == set(first_ids)
    assert len(second_ids) == 2


def test_persisted_collection_can_be_reopened_and_searched(tmp_path: Path) -> None:
    index_documents(
        make_documents(),
        embedding=KeywordEmbeddings(),
        persist_directory=tmp_path,
    )

    reopened = Chroma(
        collection_name="xuzhe_articles",
        embedding_function=KeywordEmbeddings(),
        persist_directory=str(tmp_path),
    )
    results = reopened.similarity_search("利率如何影响债券？", k=1)

    assert len(results) == 1
    assert results[0].page_content == "债券价格通常与利率反向变化。"
    assert results[0].metadata["article_id"] == "answer-123"
    assert results[0].metadata["position"] == 0
