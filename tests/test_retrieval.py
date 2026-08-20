from pathlib import Path

import pytest
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from backend.rag import index_documents, retrieve_documents


class KeywordEmbeddings(Embeddings):
    @staticmethod
    def _embed(text: str) -> list[float]:
        return [1.0, 0.0] if "债券" in text or "利率" in text else [0.0, 1.0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


def make_vector_store(tmp_path: Path) -> Chroma:
    documents = [
        Document(
            page_content="债券价格通常与利率反向变化。",
            metadata={"article_id": "bonds", "position": 0},
        ),
        Document(
            page_content="自由现金流可用于企业估值。",
            metadata={"article_id": "cash-flow", "position": 0},
        ),
    ]
    return index_documents(
        documents,
        embedding=KeywordEmbeddings(),
        persist_directory=tmp_path,
    )


def test_returns_ranked_documents_with_scores(tmp_path: Path) -> None:
    results = retrieve_documents(
        make_vector_store(tmp_path), "利率如何影响债券？", k=2
    )

    assert len(results) == 2
    assert results[0][0].metadata["article_id"] == "bonds"
    assert results[0][0].page_content == "债券价格通常与利率反向变化。"
    assert results[0][1] >= results[1][1]


def test_respects_k(tmp_path: Path) -> None:
    results = retrieve_documents(make_vector_store(tmp_path), "企业估值", k=1)

    assert len(results) == 1
    assert results[0][0].metadata["article_id"] == "cash-flow"


@pytest.mark.parametrize(("query", "k"), [("", 1), ("   ", 1), ("问题", 0)])
def test_rejects_invalid_query_settings(tmp_path: Path, query: str, k: int) -> None:
    with pytest.raises(ValueError):
        retrieve_documents(make_vector_store(tmp_path), query, k=k)
