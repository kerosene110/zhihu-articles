# Stage 04 development log: scored top-k retrieval

**Status:** In progress — interface and TDD contract established

**Implementation ownership:** The project author implements retrieval. Codex
established the interface and black-box tests and provides review.

## Purpose

This stage converts one user query into ranked evidence candidates. It exposes scores
for later threshold calibration but does not choose a threshold, construct prompts,
or call an LLM.

## Interface

Implement [`retrieve_documents`](../../backend/rag.py):

```python
def retrieve_documents(
    vector_store: Chroma,
    query: str,
    *,
    k: int = 5,
) -> list[tuple[Document, float]]:
```

Inputs are an open Chroma store, a non-blank query, and a positive result limit.
The output is Chroma relevance-ranked `(Document, score)` pairs.

## Acceptance criteria

[`tests/test_retrieval.py`](../../tests/test_retrieval.py) checks that:

1. the semantically matching synthetic document ranks first;
2. documents retain their content and source metadata;
3. scores are ordered from most to least relevant;
4. `k` limits the result count;
5. blank queries and non-positive `k` raise `ValueError`.

Run:

```bash
python -m pytest tests/test_retrieval.py -v
python -m ruff check backend tests
```

Implement only `retrieve_documents`, then send it to Codex for review. Do not add a
threshold until retrieval scores have been inspected on representative questions.

## Technical reference

- [LangChain Chroma similarity search](https://docs.langchain.com/oss/python/integrations/vectorstores/chroma#similarity-search)
