# Xuzhe Finance RAG

A portfolio-focused, corpus-grounded assistant for approximately 50 Chinese finance
articles by Xu Zhe. The UI and API are ready; learner-owned RAG stages are added one
at a time and reviewed before integration.

## Architecture

```text
saved sources → canonical ingestion → learner-owned RAG pipeline → persisted Chroma
                                               ↑
browser → React → FastAPI → RagService ─────────┘
```

- `backend/app.py`: FastAPI routes and static frontend delivery
- `backend/schemas.py`: stable browser/API models
- `backend/service.py`: the single web-to-RAG integration contract
- `backend/ingestion.py`: completed JSON and MHTML loading/cleaning
- `backend/models.py`: shared framework-independent Article model
- `backend/rag.py`: the current learner-owned algorithm stub
- `frontend/`: responsive grounded-chat UI
- `crawler/output/`: saved JSON and manually downloaded MHTML sources
- `docs/exercises/`: one learner assignment at a time

The detailed product scope and ownership boundary are in [PLAN.md](PLAN.md).

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
the persisted index. A learner-owned indexing command will be added in its assigned
stage.

## Current learner task

Complete only [Exercise 02: LangChain text splitting](docs/exercises/02_chunking.md), then stop for review. Do not start embedding or indexing yet.
