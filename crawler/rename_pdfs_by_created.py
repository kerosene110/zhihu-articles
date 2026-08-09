#!/usr/bin/env python3
import argparse
import json
import os
import re
from typing import Dict, List


COLUMN_SLUG = "wontfallinyourlap"
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
DEFAULT_PDF_DIR = os.path.join(DEFAULT_OUTPUT_DIR, COLUMN_SLUG)
DEFAULT_METADATA_PATH = os.path.join(DEFAULT_PDF_DIR, "articles.json")


def load_items_from_metadata_file(meta_path: str) -> List[Dict]:
    with open(meta_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        return payload["data"]
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
        items.extend(load_items_from_metadata_file(json_file))
    return items


def build_article_order(items: List[Dict]) -> Dict[str, int]:
    articles = []
    for item in items:
        if item.get("type") not in (None, "article"):
            continue
        article_id = str(item.get("id") or "").strip()
        created = item.get("created")
        if not article_id or not isinstance(created, int):
            continue
        articles.append((created, article_id))

    ordered_ids = []
    seen = set()
    for _, article_id in sorted(articles):
        if article_id in seen:
            continue
        seen.add(article_id)
        ordered_ids.append(article_id)

    width = max(3, len(str(len(ordered_ids))))
    return {article_id: index for index, article_id in enumerate(ordered_ids, start=1)}, width


def rename_pdfs(pdf_dir: str, order_map: Dict[str, int], width: int, dry_run: bool) -> tuple[int, List[str]]:
    renamed = 0
    unmatched: List[str] = []
    id_pattern = re.compile(r"(\d+)\.pdf$")
    prefix_pattern = re.compile(r"^\d+_")
    plans = []

    for name in sorted(os.listdir(pdf_dir)):
        if not name.endswith(".pdf"):
            continue
        match = id_pattern.search(name)
        if not match:
            unmatched.append(name)
            continue
        article_id = match.group(1)
        order = order_map.get(article_id)
        if order is None:
            unmatched.append(name)
            continue

        base_name = prefix_pattern.sub("", name)
        new_name = f"{order:0{width}d}_{base_name}"
        if new_name == name:
            continue
        plans.append((name, new_name))

    planned_targets = {new_name for _, new_name in plans}
    if len(planned_targets) != len(plans):
        raise RuntimeError("Rename plan contains conflicting target filenames.")

    existing_names = set(os.listdir(pdf_dir))
    for old_name, new_name in plans:
        if new_name in existing_names and new_name != old_name:
            raise RuntimeError(f"Target file already exists: {os.path.join(pdf_dir, new_name)}")

    for old_name, new_name in plans:
        old_path = os.path.join(pdf_dir, old_name)
        new_path = os.path.join(pdf_dir, new_name)
        print(f"{old_name} -> {new_name}")
        if not dry_run:
            os.rename(old_path, new_path)
        renamed += 1

    return renamed, unmatched


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rename existing PDFs so lexical filename order matches article creation time."
    )
    parser.add_argument("--pdf-dir", default=DEFAULT_PDF_DIR, help="PDF directory (default: crawler/output/wontfallinyourlap)")
    parser.add_argument(
        "--metadata-path",
        default=DEFAULT_METADATA_PATH,
        help="Metadata JSON file or directory of page JSON files (default: crawler/output/wontfallinyourlap/articles.json)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print planned renames without changing files")
    args = parser.parse_args()

    items = load_items_from_metadata(args.metadata_path)
    order_map, width = build_article_order(items)
    renamed, unmatched = rename_pdfs(args.pdf_dir, order_map, width, args.dry_run)
    print(f"Renamed {renamed} PDF files in {args.pdf_dir}")
    if unmatched:
        print("Skipped PDFs with no matching metadata entry:")
        for name in unmatched:
            print(f"  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
