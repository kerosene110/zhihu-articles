# Xuzhe Finance RAG — MVP plan

## Product goal

Deploy one portfolio-quality application that answers English or Chinese questions
about Xu Zhe's Chinese finance articles. Every supported answer must cite retrieved
Chinese passages and link to the original article. Unsupported questions must return
an explicit insufficient-evidence result.

## Delivery areas

The contribution split is intentionally explicit: application infrastructure and
ingestion were implemented by Codex, while the project author owns the production RAG
algorithms and can explain their design and tradeoffs.

### Implemented by Codex

- React UI and browser-held chat history
- FastAPI routes, validation schemas, and error mapping
- the `RagService` integration boundary
- Docker, Compose, CI, deployment documentation, and integration tests
- JSON and MHTML ingestion plus HTML preprocessing
- test scaffolding, interface guidance, and review for the RAG stages

### Implemented by the project author

- deterministic chunking
- embedding and idempotent Chroma indexing
- retrieval and threshold calibration
- evidence-dependent prompt construction, token budgeting, and citation validation
- retrieval evaluation

Development proceeds through small, independently testable stages. Each stage records
its interface, engineering decisions, and verification evidence before the next stage
is integrated.

## Minimal architecture

```text
Offline indexing:
saved JSON + MHTML → Article[] → LangChain Document[] → embeddings → persisted Chroma

Online request:
React → FastAPI → RagService → retrieve evidence → generate grounded answer
                                      ↓
                             answer + validated citations
```

FastAPI depends on one interface: `RagService.list_articles()` and
`RagService.answer()`. Internal RAG stages should start as concrete functions.
Add another interface only when there is a real second implementation or a testing
boundary that cannot be handled with a small fake.

## Stable HTTP contract

- `GET /health` → `{"status": "ok"}`
- `GET /articles` → indexed article summaries
- `POST /chat` → `answer`, `citations`, and `insufficient_evidence`
- history is bounded and supplied by the browser; the server does not persist it

## Shortest path to deployed MVP

1. Ingest and clean the checked-in JSON and MHTML sources. **Complete.**
2. Configure deterministic LangChain splitting. **Complete.**
3. Embed and idempotently persist chunks in Chroma. **Complete.**
4. Retrieve relevant passages and establish a threshold. **In progress.**
5. Build evidence-only prompts with a model-aware token budget and validate citations.
   Reserve the response allowance first, count the system prompt, query, and bounded
   history, then include ranked chunks only while they fit the remaining context
   window. Record actual provider-reported input/output usage when available; do not
   use whitespace-based estimates because the corpus is primarily Chinese.
6. Wire the completed implementation behind `RagService`.
7. Add 20 evaluation questions and record Hit@1, Hit@5, and MRR.
8. Build the container, create the persistent index, deploy, and run smoke checks.

## Deliberately deferred

Streaming, authentication, server-side chat history, crawler sync endpoints, PDF
ingestion, multiple vector databases, hybrid search, reranking, agent frameworks,
article-reading pages, and generalized HTML normalization.
