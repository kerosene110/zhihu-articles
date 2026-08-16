# Xuzhe Finance RAG — MVP plan

## Product goal

Deploy one portfolio-quality application that answers English or Chinese questions
about Xu Zhe's Chinese finance articles. Every supported answer must cite retrieved
Chinese passages and link to the original article. Unsupported questions must return
an explicit insufficient-evidence result.

## Ownership

### App plumbing and completed foundation (Codex implements)

- React UI and browser-held chat history
- FastAPI routes, validation schemas, and error mapping
- the `RagService` integration boundary
- Docker, Compose, CI, deployment documentation, and integration tests
- JSON and MHTML ingestion plus HTML preprocessing

### RAG system (learner implements and explains)

- deterministic chunking
- embedding and idempotent Chroma indexing
- retrieval and threshold calibration
- evidence-dependent prompt construction and citation validation
- retrieval evaluation

Only the current learner component should have an implementation stub. Each component
is reviewed before the next is introduced.

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
2. Configure deterministic LangChain splitting with stable IDs. **Current exercise.**
3. Embed and idempotently persist chunks in Chroma.
4. Retrieve relevant passages and establish a threshold.
5. Build evidence-only prompts and validate citations.
6. Wire the completed implementation behind `RagService`.
7. Add 20 evaluation questions and record Hit@1, Hit@5, and MRR.
8. Build the container, create the persistent index, deploy, and run smoke checks.

## Deliberately deferred

Streaming, authentication, server-side chat history, crawler sync endpoints, PDF
ingestion, multiple vector databases, hybrid search, reranking, agent frameworks,
article-reading pages, and generalized HTML normalization.
