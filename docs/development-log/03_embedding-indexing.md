# Stage 03 development log: embedding and Chroma indexing

**Status:** Complete

**Implementation ownership:** The project author implements embedding and indexing.
Codex established the interface and black-box tests and provides code review.

## Purpose

This stage turns the `Document` objects produced by chunking into a persistent local
Chroma collection. It establishes storage and identity behavior only; retrieval
ranking, thresholds, prompt construction, and evaluation remain later stages.

## Interface

Implement [`index_documents`](../../backend/rag.py):

```python
def index_documents(
    documents: list[Document],
    *,
    embedding: Embeddings,
    persist_directory: str | Path,
    collection_name: str = "xuzhe_articles",
) -> Chroma:
```

Inputs:

- `documents`: already-cleaned, already-chunked LangChain documents;
- `embedding`: an injected LangChain `Embeddings` implementation;
- `persist_directory`: local directory used by Chroma;
- `collection_name`: logical Chroma collection, with a stable default.

Output: an open `langchain_chroma.Chroma` instance backed by that directory.

## Design boundaries

- Do not load JSON or MHTML here; ingestion already owns source loading.
- Do not split text here; chunking already owns document boundaries and positions.
- Do not instantiate a production embedding provider inside the function. Dependency
  injection keeps tests offline and lets model selection change independently.
- Generate deterministic document IDs from `article_id` and `position`, then pass
  those IDs when adding documents. Repeating the same indexing operation must upsert
  the same records instead of creating duplicates.
- Do not add retrieval helpers yet.

For this MVP, a deployment rebuild starts from the complete checked-in corpus. Removal
of stale chunks after partial article updates is intentionally deferred until the
offline indexing command is added.

## Acceptance criteria

[`tests/test_indexing.py`](../../tests/test_indexing.py) uses a deterministic embedding
test double and makes no network calls. The stage is complete when:

1. two documents create exactly two distinct records;
2. indexing the same documents twice preserves the same IDs and count;
3. a new Chroma instance can reopen the persisted collection;
4. similarity search returns the expected document with its metadata;
5. the complete repository suite and Ruff pass.

Run:

```bash
python -m pytest tests/test_indexing.py -v
python -m pytest
python -m ruff check backend tests
```

At completion, both indexing tests and all 23 backend tests passed. Ruff also passed.
The project author implemented Chroma persistence; Codex reviewed it and corrected
the ID boundary so repeated indexing uses deterministic upserts.

## Technical references

- [LangChain Chroma integration](https://docs.langchain.com/oss/python/integrations/vectorstores/chroma)
- [LangChain embeddings interface](https://reference.langchain.com/python/langchain-core/embeddings/)
