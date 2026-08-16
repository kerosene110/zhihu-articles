"""FastAPI application factory and production entry point."""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.staticfiles import StaticFiles

from backend.schemas import ArticleSummary, ChatRequest, ChatResponse, HealthResponse
from backend.service import RagNotReadyError, RagService, UnavailableRagService


def create_app(
    *, rag_service: RagService | None = None, frontend_dir: Path | None = None
) -> FastAPI:
    """Build the web app around a replaceable RAG service."""

    app = FastAPI(title="Xuzhe Finance RAG", version="0.1.0")
    app.state.rag_service = rag_service or UnavailableRagService()

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.get("/articles", response_model=list[ArticleSummary], tags=["corpus"])
    def articles(request: Request) -> list[ArticleSummary]:
        service: RagService = request.app.state.rag_service
        return list(service.list_articles())

    @app.post("/chat", response_model=ChatResponse, tags=["chat"])
    def chat(payload: ChatRequest, request: Request) -> ChatResponse:
        service: RagService = request.app.state.rag_service
        try:
            return service.answer(payload.question, payload.history)
        except RagNotReadyError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
            ) from exc

    resolved_frontend = (
        frontend_dir or Path(__file__).resolve().parents[1] / "frontend" / "dist"
    )
    if resolved_frontend.is_dir():
        # Mount last so the SPA fallback cannot shadow the API routes.
        app.mount(
            "/", StaticFiles(directory=resolved_frontend, html=True), name="frontend"
        )

    return app


app = create_app()

