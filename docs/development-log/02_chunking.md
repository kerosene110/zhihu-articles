# Stage 02 development log: deterministic text chunking

**Status:** Complete

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
- source metadata: article ID, title, author, URL, ISO-8601 timestamps, and position.

Document IDs are deliberately not assigned here. Stable IDs and duplicate handling
belong to Stage 03 because they are persistence concerns. Position remains chunk
metadata because order is established during splitting.

Invalid sizing parameters are rejected when `target_chars <= 0`,
`overlap_chars < 0`, or `overlap_chars >= target_chars`.

## TDD validation contract

[`tests/test_chunking.py`](../../tests/test_chunking.py) was added before completion of
the implementation. Its black-box coverage checks:

1. non-empty LangChain `Document` output;
2. Chinese sentence-boundary preference and maximum size;
3. fallback splitting and overlap for boundary-free text;
4. source metadata and consecutive positions;
5. rejection of invalid size settings.

The checks and full repository suite passed at stage completion:

```bash
python -m pytest tests/test_chunking.py -v
python -m pytest
python -m ruff check backend tests
```

At completion, 9 chunking tests and all 21 backend tests passed. Ruff also passed.
Corpus-level length analysis remains an evaluation task before production defaults
are finalized.

## Next stage

Stage 03 adds injected embeddings and idempotent local Chroma persistence. Retrieval
behavior remains outside that stage and will be evaluated before prompt construction.

## Technical references

- [LangChain recursive splitter](https://docs.langchain.com/oss/python/integrations/splitters/recursive_text_splitter)
- [LangChain text splitters](https://docs.langchain.com/oss/python/integrations/splitters)
- [LangChain Chroma integration](https://docs.langchain.com/oss/python/integrations/vectorstores/chroma)
