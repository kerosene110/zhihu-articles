"""Start with: uvicorn backend.main:app --reload"""

from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# First exercise: define a Pydantic ArticleSummary model, then implement
# GET /articles using a small hard-coded list. This lets you learn response
# models and verify the frontend contract before introducing Chroma.
