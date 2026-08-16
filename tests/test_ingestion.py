"""Tests for canonical JSON and MHTML ingestion."""

import json
from datetime import UTC, datetime
from email.message import EmailMessage
from pathlib import Path

import pytest

from backend.ingestion import load_articles


def _json_record(
    article_id: str = "42",
    *,
    content: str = "<p>First paragraph.</p><p>Second paragraph.</p>",
    created: int = 1_700_000_000,
    updated: int = 1_700_000_100,
) -> dict[str, object]:
    return {
        "id": article_id,
        "title": f"Article {article_id}",
        "author": {"name": "许哲"},
        "url": f"https://zhuanlan.zhihu.com/p/{article_id}",
        "created": created,
        "updated": updated,
        "content": content,
    }


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_mhtml(path: Path, *, answer_id: str = "2306281723") -> None:
    url = f"https://www.zhihu.com/question/23005134/answer/{answer_id}"
    html = f"""
    <html><body>
      <div class="ContentItem AnswerItem"
           data-zop='{{"authorName":"Other","itemId":"999","title":"Other answer"}}'>
        <meta itemprop="dateCreated" content="2020-01-01T00:00:00.000Z">
        <meta itemprop="dateModified" content="2020-01-01T00:00:00.000Z">
        <span itemprop="text"><p>Do not ingest me.</p></span>
      </div>
      <div class="ContentItem AnswerItem"
           data-zop='{{"authorName":"许哲","itemId":"{answer_id}","title":"自由现金流折现"}}'>
        <meta itemprop="dateCreated" content="2022-01-11T05:51:07.000Z">
        <meta itemprop="dateModified" content="2022-01-11T06:25:46.000Z">
        <span class="RichText" itemprop="text">
          <h2>估值</h2>
          <p>Hello <b>world</b>.</p>
          <script>ignore()</script><img src="ignored.png">
          <ul><li>First idea</li><li>Second idea</li></ul>
        </span>
      </div>
    </body></html>
    """
    message = EmailMessage()
    message["Snapshot-Content-Location"] = url
    message["Content-Location"] = url
    message.set_content(html, subtype="html", charset="utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(message.as_bytes())


def test_loads_array_json_and_cleans_content(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "page1.json",
        [_json_record(content="<p>Hello <b>world</b>.</p><p>Second.</p>")],
    )

    [article] = load_articles(tmp_path)

    assert article.id == "42"
    assert article.author == "许哲"
    assert article.created_at == datetime.fromtimestamp(1_700_000_000, tz=UTC)
    assert article.updated_at.tzinfo is UTC
    assert article.text == "Hello world.\nSecond."


def test_accepts_data_wrapped_json(tmp_path: Path) -> None:
    _write_json(tmp_path / "page1.json", {"data": [_json_record()]})

    assert [article.id for article in load_articles(tmp_path)] == ["42"]


def test_json_duplicates_prefer_longer_text_then_later_update(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "a.json",
        [
            _json_record("1", content="<p>short</p>", updated=300),
            _json_record("2", content="same", updated=100),
        ],
    )
    _write_json(
        tmp_path / "b.json",
        [
            _json_record("1", content="<p>meaningfully longer</p>", updated=100),
            _json_record("2", content="same", updated=200),
        ],
    )

    articles = {article.id: article for article in load_articles(tmp_path)}

    assert articles["1"].text == "meaningfully longer"
    assert articles["2"].updated_at == datetime.fromtimestamp(200, tz=UTC)


def test_loads_only_target_answer_from_mhtml(tmp_path: Path) -> None:
    source = tmp_path / "answer.mhtml"
    _write_mhtml(source)

    [article] = load_articles(source)

    assert article.id == "2306281723"
    assert article.title == "自由现金流折现"
    assert article.author == "许哲"
    assert article.url.endswith("/answer/2306281723")
    assert article.created_at == datetime(2022, 1, 11, 5, 51, 7, tzinfo=UTC)
    assert article.text == "估值\nHello world.\nFirst idea\nSecond idea"
    assert "Do not ingest me" not in article.text


def test_directory_recursively_loads_both_formats(tmp_path: Path) -> None:
    _write_json(tmp_path / "metadata" / "page1.json", [_json_record("42")])
    _write_mhtml(tmp_path / "manual" / "answer.mhtml")

    articles = load_articles(tmp_path)

    assert {article.id for article in articles} == {"42", "2306281723"}


def test_invalid_json_shape_names_source_file(tmp_path: Path) -> None:
    _write_json(tmp_path / "broken.json", {"items": []})

    with pytest.raises(ValueError, match="broken.json"):
        load_articles(tmp_path)
