# Xuzhe Finance RAG

A portfolio-focused, corpus-grounded assistant for approximately 50 Chinese finance
articles by Xu Zhe. The UI and API are ready; learner-owned RAG stages are added one
at a time and reviewed before integration.

## Architecture

```text
crawler metadata → learner-owned RAG pipeline → persisted Chroma
                                               ↑
browser → React → FastAPI → RagService ─────────┘
```

- `backend/app.py`: FastAPI routes and static frontend delivery
- `backend/schemas.py`: stable browser/API models
- `backend/service.py`: the single web-to-RAG integration contract
- `backend/rag.py`: learner-owned algorithms; implement only the current exercise
- `frontend/`: responsive grounded-chat UI
- `crawler/output/wontfallinyourlap/metadata/`: the MVP ingestion source
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

Open <http://localhost:8000>. The image contains the saved metadata at
`/app/corpus/metadata`; the `rag-data` volume at `/data/rag` is reserved for
the persisted index. A learner-owned indexing command will be added in its assigned
stage.

## Current learner task

Complete only [Exercise 01: saved metadata ingestion](docs/exercises/01_saved_metadata_source.md),
then stop for review. Do not start chunking yet.
