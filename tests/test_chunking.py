from datetime import UTC, datetime

import pytest
from langchain_core.documents import Document

from backend.models import Article
from backend.rag import chunk_article


def make_article(*, text: str = "第一段。第二段。第三段。") -> Article:
    return Article(
        id="answer-123",
        title="测试文章",
        author="测试作者",
        url="https://www.zhihu.com/question/1/answer/123",
        created_at=datetime(2024, 1, 2, 3, 4, tzinfo=UTC),
        updated_at=datetime(2024, 2, 3, 4, 5, tzinfo=UTC),
        text=text,
    )


def test_returns_non_empty_langchain_documents() -> None:
    chunks = chunk_article(make_article(), target_chars=8, overlap_chars=2)

    assert chunks
    assert all(isinstance(chunk, Document) for chunk in chunks)
    assert all(chunk.page_content.strip() for chunk in chunks)


def test_prefers_chinese_boundaries_and_respects_target_size() -> None:
    article = make_article(text=f"{'甲' * 8}。{'乙' * 8}。{'丙' * 8}")

    chunks = chunk_article(article, target_chars=10, overlap_chars=0)

    contents = [chunk.page_content for chunk in chunks]
    assert [content.replace("。", "") for content in contents] == [
        "甲" * 8,
        "乙" * 8,
        "丙" * 8,
    ]
    assert "".join(contents) == article.text
    assert all(len(content) <= 10 for content in contents)


def test_boundary_free_text_has_requested_overlap() -> None:
    chunks = chunk_article(
        make_article(text="ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        target_chars=10,
        overlap_chars=3,
    )

    assert len(chunks) > 1
    assert all(len(chunk.page_content) <= 10 for chunk in chunks)
    for previous, current in zip(chunks, chunks[1:], strict=False):
        assert previous.page_content[-3:] == current.page_content[:3]


def test_copies_metadata_and_assigns_consecutive_positions() -> None:
    article = make_article(text="A" * 25)

    chunks = chunk_article(article, target_chars=10, overlap_chars=2)

    expected_common_metadata = {
        "article_id": article.id,
        "title": article.title,
        "author": article.author,
        "url": article.url,
        "created_at": article.created_at.isoformat(),
        "updated_at": article.updated_at.isoformat(),
    }
    for position, chunk in enumerate(chunks):
        assert chunk.metadata == {
            **expected_common_metadata,
            "position": position,
        }


def test_ids_are_stable_and_change_when_source_text_changes() -> None:
    article = make_article(text="A" * 25)

    first_ids = [
        chunk.id
        for chunk in chunk_article(article, target_chars=10, overlap_chars=2)
    ]
    repeated_ids = [
        chunk.id
        for chunk in chunk_article(article, target_chars=10, overlap_chars=2)
    ]
    changed_ids = [
        chunk.id
        for chunk in chunk_article(
            make_article(text=f"{'A' * 24}B"),
            target_chars=10,
            overlap_chars=2,
        )
    ]

    assert all(first_ids)
    assert len(first_ids) == len(set(first_ids))
    assert first_ids == repeated_ids
    assert len(first_ids) == len(changed_ids)
    assert all(old != new for old, new in zip(first_ids, changed_ids, strict=True))


@pytest.mark.parametrize(
    ("target_chars", "overlap_chars"),
    [(0, 0), (-1, 0), (10, -1), (10, 10), (10, 11)],
)
def test_rejects_invalid_size_settings(
    target_chars: int, overlap_chars: int
) -> None:
    with pytest.raises(ValueError):
        chunk_article(
            make_article(),
            target_chars=target_chars,
            overlap_chars=overlap_chars,
        )
