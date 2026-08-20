# Xuzhe Finance RAG

A portfolio-focused, corpus-grounded assistant for approximately 50 Chinese finance
articles by Xu Zhe. The system is being delivered in independently testable stages,
with architectural decisions and validation results recorded as it develops.

## Architecture

```text
saved sources → canonical ingestion → RAG pipeline → persisted Chroma
                                               ↑
browser → React → FastAPI → RagService ─────────┘
```

- `backend/app.py`: FastAPI routes and static frontend delivery
- `backend/schemas.py`: stable browser/API models
- `backend/service.py`: the single web-to-RAG integration contract
- `backend/ingestion.py`: completed JSON and MHTML loading/cleaning
- `backend/models.py`: shared framework-independent Article model
- `backend/rag.py`: RAG algorithms, currently focused on deterministic chunking
- `frontend/`: responsive grounded-chat UI
- `crawler/output/`: saved JSON and manually downloaded MHTML sources
- `docs/development-log/`: chronological records of each implementation stage

The detailed product scope, architecture, and delivery plan are in [PLAN.md](PLAN.md).

## Contribution split

- **Implemented by the project author:** chunking, embedding and indexing, retrieval, grounded prompt
  construction, and retrieval evaluation.
- **Implemented by Codex:** frontend, FastAPI application plumbing, schemas, integration
  boundaries, Docker and deployment setup, CI/test scaffolding, and canonical
  JSON/MHTML ingestion.

For the RAG stages, Codex provides interface design, tests, and code review while the
project author implements and explains the production algorithms.

## Local development

Install backend dependencies and start FastAPI:

```bash
python -m pip install -r requirements-dev.txt
uvicorn backend.app:app --reload
```

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Vite proxies `/api/*` to FastAPI at `http://127.0.0.1:8000`. Until a completed
RAG implementation is integrated, `GET /articles` returns an empty list and
`POST /chat` returns `503` intentionally.

## Checks

```bash
python -m ruff check backend tests
python -m pytest
cd frontend && npm run build
docker build -t xuzhe-rag .
```

## Container

```bash
docker compose up --build
```

Open <http://localhost:8000>. The image contains saved JSON and MHTML sources under
`/app/corpus`; the `rag-data` volume at `/data/rag` is reserved for
the persisted index. The indexing command will be added during the indexing stage.

## Current development stage

[Stage 04: scored top-k retrieval](docs/development-log/04_retrieval.md) is in
progress. Its query interface and TDD validation contract are established; threshold
calibration follows after ranked retrieval is validated.
