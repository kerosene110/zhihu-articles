#!/usr/bin/env python3
import argparse
import html
import json
import os
import re
import sys
import time
from typing import Dict, Iterable, List, Optional, Set

import requests
from readability import Document

try:
    from weasyprint import HTML as WeasyHTML  # type: ignore
except Exception:
    WeasyHTML = None

try:
    import pdfkit  # type: ignore
except Exception:
    pdfkit = None

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)
COLUMN_SLUG = "wontfallinyourlap"
COLUMN_URL = f"https://www.zhihu.com/column/{COLUMN_SLUG}"
ITEMS_API_URL = f"https://www.zhihu.com/api/v4/columns/{COLUMN_SLUG}/items"
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


def _headers(referer: str) -> Dict[str, str]:
    return {
        "User-Agent": USER_AGENT,
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": referer,
    }


def log(message: str) -> None:
    print(message, flush=True)


def load_manual_payload(raw: str, source: str) -> List[Dict]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Manual response from {source} is not valid JSON: {exc}"
        ) from exc

    data = payload.get("data")
    if not isinstance(data, list):
        raise RuntimeError(f"Manual response from {source} does not contain a list in 'data'.")
    return data


def prompt_for_manual_page(next_url: str, page_num: int) -> List[Dict]:
    log("")
    log(f"Page {page_num} returned an empty API response for {next_url}")
    log("Open that URL in your browser, copy the full JSON response, paste it below, then submit EOF.")
    log("If terminal paste is unreliable, save the response to a file and paste a single line like @/tmp/page2.json instead.")
    log("EOF is Ctrl-D on Linux/macOS and Ctrl-Z then Enter on Windows.")
    raw_bytes = sys.stdin.buffer.read()
    if not raw_bytes:
        raise RuntimeError("No manual response was provided.")

    try:
        raw = raw_bytes.decode("utf-8").strip()
    except UnicodeDecodeError:
        log("Manual response was not valid UTF-8; decoding with replacement for invalid bytes.")
        raw = raw_bytes.decode("utf-8", errors="replace").strip()
    if not raw:
        raise RuntimeError("No manual response was provided.")

    if raw.startswith("@"):
        path = raw[1:].strip()
        if not path:
            raise RuntimeError("Manual response file path after '@' is empty.")
        with open(path, "r", encoding="utf-8") as f:
            return load_manual_payload(f.read(), path)

    try:
        return load_manual_payload(raw, "stdin")
    except RuntimeError:
        debug_path = f"/tmp/zhihu-manual-page-{page_num}.json"
        with open(debug_path, "w", encoding="utf-8", errors="replace") as f:
            f.write(raw)
        raise RuntimeError(
            f"Manual response was saved to {debug_path}. "
            f"Inspect or fix that file, then rerun and provide @{debug_path}."
        )


def iter_column_items(session: requests.Session, limit: int, sleep_s: float) -> Iterable[Dict]:
    offset = 0
    page_num = 0
    while True:
        page_num += 1
        next_url = f"{ITEMS_API_URL}?limit={limit}&offset={offset}"
        log(f"Crawling page {page_num}: {next_url}")

        resp = session.get(next_url, headers=_headers(COLUMN_URL), timeout=20)
        resp.raise_for_status()
        payload = resp.json()
        data = payload.get("data", [])
        log(f"Fetched page {page_num}: {len(data)} items")
        if not data:
            if page_num > 1:
                manual_data = prompt_for_manual_page(next_url, page_num)
                log(f"Loaded page {page_num} manually: {len(manual_data)} items")
                data = manual_data
                payload = {"paging": {"is_end": len(data) < limit}}
            else:
                log("Stopping crawl because the API returned an empty page.")
                break
        if not data:
            log("Stopping crawl because the API returned an empty page.")
            break
        for item in data:
            yield item
        paging = payload.get("paging") or {}
        if paging.get("is_end"):
            log("Reached the final page of the column.")
            break
        offset += len(data)
        time.sleep(sleep_s)


def safe_filename(title: str, article_id: str) -> str:
    base = re.sub(r"[^\w\-\s]", "", title, flags=re.UNICODE).strip()
    base = re.sub(r"\s+", " ", base)
    if not base:
        base = f"article-{article_id}"
    return f"{base}-{article_id}.pdf"


def build_html(title: str, content_html: str, source_url: str) -> str:
    return f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8"/>
    <title>{html.escape(title)}</title>
    <style>
      body {{ font-family: "Noto Serif CJK SC", "Songti SC", "SimSun", serif; margin: 2.5cm; line-height: 1.7; }}
      h1 {{ font-size: 24px; margin-bottom: 0.2em; }}
      .source {{ color: #666; font-size: 12px; margin-bottom: 1.2em; }}
      img {{ max-width: 100%; height: auto; }}
      pre, code {{ white-space: pre-wrap; }}
      blockquote {{ color: #444; border-left: 3px solid #ddd; margin-left: 0; padding-left: 0.8em; }}
    </style>
  </head>
  <body>
    <h1>{html.escape(title)}</h1>
    <div class="source">{html.escape(source_url)}</div>
    {content_html}
  </body>
</html>
"""


def html_to_pdf(html_text: str, output_path: str, base_url: str) -> bool:
    if WeasyHTML is not None:
        WeasyHTML(string=html_text, base_url=base_url).write_pdf(output_path)
        return True

    if pdfkit is not None:
        try:
            pdfkit.from_string(html_text, output_path, options={"encoding": "UTF-8"})
            return True
        except Exception:
            return False

    return False


def fetch_article_html_from_page(session: requests.Session, article_url: str) -> str:
    resp = session.get(article_url, headers=_headers(article_url), timeout=25)
    resp.raise_for_status()
    doc = Document(resp.text)
    return doc.summary(html_partial=True)


def fetch_article_html_from_api(session: requests.Session, article_id: str) -> str:
    api_url = f"https://www.zhihu.com/api/v4/articles/{article_id}"
    params = {"include": "content"}
    resp = session.get(api_url, params=params, headers=_headers(COLUMN_URL), timeout=20)
    resp.raise_for_status()
    payload = resp.json()
    content = payload.get("content")
    if not content:
        raise RuntimeError(f"Article API returned no content for article {article_id}")
    return content


def get_article_html(session: requests.Session, item: Dict) -> str:
    article_id = str(item.get("id"))
    article_url = item.get("url") or f"https://zhuanlan.zhihu.com/p/{article_id}"
    content = item.get("content")
    if content:
        if item.get("content_need_truncated"):
            log(f"Article {article_id} metadata is marked truncated; refreshing full content from API.")
            try:
                return fetch_article_html_from_api(session, article_id)
            except Exception as exc:
                log(f"Article API refresh failed for {article_id}: {exc}; using metadata content.")
        return content

    log(f"Article {article_id} metadata has no content; fetching from article API.")
    try:
        return fetch_article_html_from_api(session, article_id)
    except Exception as exc:
        log(f"Article API fetch failed for {article_id}: {exc}; falling back to webpage fetch.")
        return fetch_article_html_from_page(session, article_url)


def existing_article_ids(output_dir: str) -> Set[str]:
    ids: Set[str] = set()
    if not os.path.isdir(output_dir):
        return ids

    pattern = re.compile(r"-(\d+)\.pdf$")
    for name in os.listdir(output_dir):
        if name.endswith(".html"):
            ids.add(name[:-5])
            continue
        match = pattern.search(name)
        if match:
            ids.add(match.group(1))
    return ids


def load_items_from_metadata_file(meta_path: str) -> List[Dict]:
    with open(meta_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, list):
            return data
    raise RuntimeError(
        f"Metadata file must contain either a list or an object with a 'data' list: {meta_path}"
    )


def load_items_from_metadata(meta_path: str) -> List[Dict]:
    if not os.path.exists(meta_path):
        raise RuntimeError(f"Metadata path not found: {meta_path}")
    if os.path.isfile(meta_path):
        return load_items_from_metadata_file(meta_path)
    if not os.path.isdir(meta_path):
        raise RuntimeError(f"Metadata path is neither a file nor a directory: {meta_path}")

    json_files = sorted(
        os.path.join(meta_path, name)
        for name in os.listdir(meta_path)
        if name.endswith(".json")
    )
    if not json_files:
        raise RuntimeError(f"No JSON files found in metadata directory: {meta_path}")

    items: List[Dict] = []
    for json_file in json_files:
        log(f"Loading metadata page from {json_file}")
        items.extend(load_items_from_metadata_file(json_file))
    return items


def main() -> int:
    parser = argparse.ArgumentParser(
        description=f"Download articles from {COLUMN_URL} and convert them to PDFs."
    )
    parser.add_argument(
        "--out",
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory (default: crawler/output)",
    )
    parser.add_argument("--limit", type=int, default=20, help="Page size (default: 20)")
    parser.add_argument("--sleep", type=float, default=1.0, help="Sleep seconds between requests (default: 1.0)")
    parser.add_argument("--max", type=int, default=0, help="Max articles to fetch (0 = all)")
    parser.add_argument(
        "--from-metadata",
        action="store_true",
        help="Load crawler/output/wontfallinyourlap/articles.json and generate PDFs without crawling",
    )
    parser.add_argument(
        "--metadata-path",
        help="Path to a metadata JSON file containing article items",
    )
    args = parser.parse_args()

    session = requests.Session()
    output_dir = os.path.join(args.out, COLUMN_SLUG)
    os.makedirs(output_dir, exist_ok=True)
    completed_ids = existing_article_ids(output_dir)
    if completed_ids:
        log(f"Found {len(completed_ids)} existing article files in {output_dir}; they will be skipped.")

    items: List[Dict] = []
    meta_path = os.path.join(output_dir, "articles.json")
    if args.from_metadata or args.metadata_path:
        if args.metadata_path:
            meta_path = args.metadata_path
        log(f"Loading metadata from {meta_path}")
        source_items = load_items_from_metadata(meta_path)
        for item in source_items:
            if item.get("type") != "article":
                continue
            article_id = str(item.get("id") or "")
            title = item.get("title") or article_id or "unknown"
            if article_id in completed_ids:
                log(f"Skipping already saved article: {title}")
                continue
            items.append(item)
            log(f"Queued metadata article {len(items)}: {title}")
            if args.max and len(items) >= args.max:
                log(f"Reached article limit: {args.max}")
                break
    else:
        log(f"Starting crawl for {COLUMN_URL}")
        for item in iter_column_items(session, args.limit, args.sleep):
            if item.get("type") != "article":
                continue
            article_id = str(item.get("id") or "")
            if article_id in completed_ids:
                title = item.get("title") or article_id or "unknown"
                log(f"Skipping already saved article: {title}")
                continue
            items.append(item)
            title = item.get("title") or str(item.get("id") or "unknown")
            log(f"Queued article {len(items)}: {title}")
            if args.max and len(items) >= args.max:
                log(f"Reached article limit: {args.max}")
                break

        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        log(f"Saved metadata: {meta_path}")

    converted = 0
    for index, item in enumerate(items, start=1):
        article_url = item.get("url")
        article_id = str(item.get("id"))
        title = item.get("title") or article_id
        if not article_url:
            log(f"Skipping article {index}/{len(items)} because it has no URL: {title}")
            continue

        log(f"Preparing article {index}/{len(items)}: {title}")
        try:
            html_content = get_article_html(session, item)
        except Exception as exc:
            log(f"Failed to get article HTML {index}/{len(items)}: {title} ({exc})")
            continue

        full_html = build_html(title, html_content, article_url)
        pdf_name = safe_filename(title, article_id)
        pdf_path = os.path.join(output_dir, pdf_name)

        try:
            ok = html_to_pdf(full_html, pdf_path, article_url)
        except Exception as exc:
            log(f"PDF conversion failed for {title}: {exc}")
            ok = False
        if not ok:
            fallback_path = os.path.join(output_dir, f"{article_id}.html")
            with open(fallback_path, "w", encoding="utf-8") as f:
                f.write(full_html)
            log(f"Saved HTML fallback for {title}: {fallback_path}")
        else:
            converted += 1
            log(f"Saved PDF {index}/{len(items)}: {pdf_path}")

        time.sleep(args.sleep)

    log(f"PDFs created: {converted}/{len(items)} in {output_dir}")
    if WeasyHTML is None and pdfkit is None:
        log("No PDF backend found. Install 'weasyprint' (preferred) or 'pdfkit' + wkhtmltopdf.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
