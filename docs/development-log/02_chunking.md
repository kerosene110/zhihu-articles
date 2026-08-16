# Stage 02 development log: deterministic text chunking

**Status:** In progress — interface and TDD contract established

**Implementation ownership:** The project author implements the production chunking
algorithm. Codex established the interface and black-box tests and provides code
review.

## Goal

This stage converts one cleaned `Article` into ordered LangChain `Document` objects
that can be embedded and indexed without exposing source-format details. The work is
isolated in [`backend/rag.py`](../../backend/rag.py).

```python
def chunk_article(
    article: Article,
    *,
    target_chars: int = 600,
    overlap_chars: int = 100,
) -> list[Document]:
```

## Design decisions

- `RecursiveCharacterTextSplitter` provides a transparent, deterministic baseline.
  A more complex semantic splitter is deferred until retrieval evaluation demonstrates
  a measurable need.
- Character length is used initially because it is deterministic and easy to inspect
  for a primarily Chinese corpus.
- Separators are ordered from structural boundaries to a character-level fallback:

```python
[
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
]
```

- `target_chars` and `overlap_chars` remain explicit parameters so their retrieval
  impact can be evaluated later without rewriting the interface.
- Chroma is intentionally outside this stage. It consumes the resulting documents in
  Stage 03; it does not load raw JSON or MHTML sources.

## Document contract

Each output document carries:

- chunk text in `page_content`;
- a stable ID derived from the article ID, SHA-256 of the complete article text, and
  zero-based chunk position;
- source metadata: article ID, title, author, URL, ISO-8601 timestamps, and position.

Hashing the complete source text invalidates every derived chunk ID when an article is
updated. Stable positions make repeated indexing idempotent for unchanged content.

Invalid sizing parameters are rejected when `target_chars <= 0`,
`overlap_chars < 0`, or `overlap_chars >= target_chars`.

## TDD validation contract

[`tests/test_chunking.py`](../../tests/test_chunking.py) was added before completion of
the implementation. Its black-box coverage checks:

1. non-empty LangChain `Document` output;
2. Chinese sentence-boundary preference and maximum size;
3. fallback splitting and overlap for boundary-free text;
4. source metadata and consecutive positions;
5. stable IDs and source-change invalidation;
6. rejection of invalid size settings.

The stage is complete when these checks and the full repository suite pass:

```bash
python -m pytest tests/test_chunking.py -v
python -m pytest
python -m ruff check backend tests
```

An optional corpus-level inspection records the number and length distribution of
chunks before selecting final production defaults.

## Next stage

After this contract is validated, Stage 03 will add embeddings and idempotent local
Chroma persistence. Retrieval behavior will be evaluated before prompt construction
is introduced.

## Technical references

- [LangChain recursive splitter](https://docs.langchain.com/oss/python/integrations/splitters/recursive_text_splitter)
- [LangChain text splitters](https://docs.langchain.com/oss/python/integrations/splitters)
- [LangChain Chroma integration](https://docs.langchain.com/oss/python/integrations/vectorstores/chroma)
- [Python `hashlib`](https://docs.python.org/3/library/hashlib.html)
