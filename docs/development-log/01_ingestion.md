# Stage 01 development log: canonical ingestion

**Status:** Complete

**Implementation:** Codex, at the request of the project author, implemented
canonical loading and preprocessing.

## Outcome

The ingestion stage converts saved Zhihu content into a single canonical `Article`
model. The implementation lives in [`backend/ingestion.py`](../../backend/ingestion.py)
and accepts:

- saved Zhihu API `.json` files;
- manually saved Zhihu answer `.mhtml` files;
- directories recursively containing either format.

## Engineering decisions

- JSON inputs may be top-level arrays or objects containing a `data` list.
- An MHTML snapshot may contain several rendered answers. Its snapshot URL supplies
  the target answer ID, preventing unrelated answers from entering the corpus.
- Both formats pass through the same HTML-to-text cleanup and produce the same domain
  model.
- Timestamps are normalized to UTC, records are deduplicated by answer ID, and output
  ordering is deterministic.
- Format-specific parsing helpers remain private to the ingestion module so later RAG
  stages depend only on `Article`.

## Stable interface

```python
load_articles(source: Path) -> list[Article]
```

This boundary isolates source-format concerns from chunking, indexing, and retrieval.

## Verification

Focused coverage is in
[`tests/test_ingestion.py`](../../tests/test_ingestion.py). It verifies both source
formats, preprocessing, validation, deduplication, and deterministic ordering.

A corpus smoke test loads 51 canonical articles from the checked-in sources.

## Next stage

Canonical articles feed Stage 02, which turns each article into retrieval-sized
LangChain documents with stable identifiers and traceable metadata.
