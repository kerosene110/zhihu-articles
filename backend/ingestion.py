"""Helper functions to load saved Zhihu JSON and MHTML into canonical articles."""

import json
import re
from datetime import UTC, datetime
from email import policy
from email.message import Message
from email.parser import BytesParser
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from backend.models import Article

_BLOCK_TAGS = (
    "blockquote",
    "br",
    "figcaption",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "li",
    "p",
    "pre",
)
_SUPPORTED_SUFFIXES = {".json", ".mhtml"}
_ANSWER_ID_PATTERN = re.compile(r"/answer/(\d+)")


def _clean_html(fragment: str | Tag) -> str:
    soup = BeautifulSoup(str(fragment), "html.parser")
    for unwanted in soup.select("script, style, noscript, img, svg"):
        unwanted.decompose()
    for block in soup.find_all(_BLOCK_TAGS):
        block.insert_before("\n")
        block.insert_after("\n")

    lines = []
    for line in soup.get_text().splitlines():
        normalized = re.sub(r"[ \t\f\v]+", " ", line).strip()
        if normalized:
            lines.append(normalized)
    return "\n".join(lines)


def _utc_from_unix(value: object, *, field: str, source: Path) -> datetime:
    try:
        return datetime.fromtimestamp(float(value), tz=UTC)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"Invalid {field!r} timestamp in {source.name}") from exc


def _utc_from_iso(value: str, *, field: str, source: Path) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Invalid {field!r} timestamp in {source.name}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"Naive {field!r} timestamp in {source.name}")
    return parsed.astimezone(UTC)


def _required_text(value: object, *, field: str, source: Path) -> str:
    text = str(value).strip() if value is not None else ""
    if not text:
        raise ValueError(f"Missing {field!r} in {source.name}")
    return text


def _article_from_json(record: dict[str, object], source: Path) -> Article:
    author = record.get("author")
    if not isinstance(author, dict):
        raise ValueError(f"Invalid 'author' in {source.name}")

    text = _clean_html(
        _required_text(record.get("content"), field="content", source=source)
    )
    if not text:
        raise ValueError(f"Empty cleaned 'content' in {source.name}")

    return Article(
        id=_required_text(record.get("id"), field="id", source=source),
        title=_required_text(record.get("title"), field="title", source=source),
        author=_required_text(author.get("name"), field="author.name", source=source),
        url=_required_text(record.get("url"), field="url", source=source),
        created_at=_utc_from_unix(record.get("created"), field="created", source=source),
        updated_at=_utc_from_unix(record.get("updated"), field="updated", source=source),
        text=text,
    )


def _load_json(source: Path) -> list[Article]:
    with source.open(encoding="utf-8") as file:
        payload = json.load(file)

    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict) and isinstance(payload.get("data"), list):
        records = payload["data"]
    else:
        raise ValueError(f"Unsupported JSON metadata shape in {source.name}")

    articles = []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError(f"Expected article objects in {source.name}")
        articles.append(_article_from_json(record, source))
    return articles


def _primary_html_part(message: Message, source: Path) -> tuple[str, str]:
    snapshot_url = str(message.get("Snapshot-Content-Location", ""))
    candidates = [
        part for part in message.walk() if part.get_content_type() == "text/html"
    ]
    if not candidates:
        raise ValueError(f"No HTML document found in {source.name}")

    part = next(
        (
            candidate
            for candidate in candidates
            if str(candidate.get("Content-Location", "")) == snapshot_url
        ),
        None,
    )
    if part is None:
        part = next(
            (
                candidate
                for candidate in candidates
                if str(candidate.get("Content-Location", "")).startswith(
                    ("https://", "http://")
                )
            ),
            candidates[0],
        )

    payload = part.get_payload(decode=True)
    if not isinstance(payload, bytes):
        raise ValueError(f"Could not decode HTML document in {source.name}")
    charset = part.get_content_charset() or "utf-8"
    html = payload.decode(charset, errors="replace")
    page_url = snapshot_url or str(part.get("Content-Location", ""))
    return html, page_url


def _answer_metadata(answer: Tag, source: Path) -> dict[str, object]:
    raw = answer.get("data-zop")
    if not isinstance(raw, str):
        raise ValueError(f"Missing answer metadata in {source.name}")
    try:
        metadata = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid answer metadata in {source.name}") from exc
    if not isinstance(metadata, dict):
        raise ValueError(f"Invalid answer metadata in {source.name}")
    return metadata


def _answer_by_id(soup: BeautifulSoup, answer_id: str, source: Path) -> Tag:
    for answer in soup.select(".ContentItem.AnswerItem"):
        metadata = _answer_metadata(answer, source)
        if str(metadata.get("itemId", "")) == answer_id:
            return answer
    raise ValueError(f"Answer {answer_id} not found in {source.name}")


def _meta_content(node: Tag, itemprop: str, source: Path) -> str:
    tag = node.select_one(f'meta[itemprop="{itemprop}"]')
    if tag is None:
        raise ValueError(f"Missing {itemprop!r} in {source.name}")
    return _required_text(tag.get("content"), field=itemprop, source=source)


def _load_mhtml(source: Path) -> list[Article]:
    with source.open("rb") as file:
        message = BytesParser(policy=policy.default).parse(file)

    html, page_url = _primary_html_part(message, source)
    match = _ANSWER_ID_PATTERN.search(page_url)
    if match is None:
        raise ValueError(f"No Zhihu answer ID found in {source.name}")

    soup = BeautifulSoup(html, "html.parser")
    answer_id = match.group(1)
    answer = _answer_by_id(soup, answer_id, source)
    metadata = _answer_metadata(answer, source)
    body = answer.select_one('[itemprop="text"]')
    if body is None:
        raise ValueError(f"Missing answer body in {source.name}")

    text = _clean_html(body)
    if not text:
        raise ValueError(f"Empty cleaned answer body in {source.name}")

    return [
        Article(
            id=answer_id,
            title=_required_text(metadata.get("title"), field="title", source=source),
            author=_required_text(
                metadata.get("authorName"), field="authorName", source=source
            ),
            url=page_url,
            created_at=_utc_from_iso(
                _meta_content(answer, "dateCreated", source),
                field="dateCreated",
                source=source,
            ),
            updated_at=_utc_from_iso(
                _meta_content(answer, "dateModified", source),
                field="dateModified",
                source=source,
            ),
            text=text,
        )
    ]


def _prefer_candidate(candidate: Article, current: Article) -> bool:
    return (len(candidate.text), candidate.updated_at) > (
        len(current.text),
        current.updated_at,
    )


def load_articles(source: Path) -> list[Article]:
    """Load JSON metadata and saved Zhihu-answer MHTML as canonical articles.

    The source may be one supported file or a directory. Directories are searched
    recursively so crawler/output can be loaded in one call.
    """
    if not source.exists():
        raise FileNotFoundError(source)

    if source.is_dir():
        files = sorted(
            path
            for path in source.rglob("*")
            if path.is_file() and path.suffix.lower() in _SUPPORTED_SUFFIXES
        )
    elif source.suffix.lower() in _SUPPORTED_SUFFIXES:
        files = [source]
    else:
        raise ValueError(f"Unsupported ingestion source: {source}")

    by_id: dict[str, Article] = {}
    for path in files:
        loaded = _load_json(path) if path.suffix.lower() == ".json" else _load_mhtml(path)
        for article in loaded:
            current = by_id.get(article.id)
            if current is None or _prefer_candidate(article, current):
                by_id[article.id] = article

    return sorted(
        by_id.values(),
        key=lambda article: (-article.created_at.timestamp(), article.id),
    )

