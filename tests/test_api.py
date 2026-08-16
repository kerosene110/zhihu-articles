"""API plumbing tests."""

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app import create_app
from backend.schemas import ArticleSummary, ChatResponse, HistoryMessage
from backend.service import RagNotReadyError


class FakeService:
    def __init__(self, *, ready: bool = True) -> None:
        self.ready = ready
        self.last_question: str | None = None
        self.last_history: Sequence[HistoryMessage] = []

    def list_articles(self) -> Sequence[ArticleSummary]:
        return [
            ArticleSummary(
                id="42",
                title="测试文章",
                author="许哲",
                url="https://zhuanlan.zhihu.com/p/42",
                created_at=datetime(2024, 1, 2, tzinfo=UTC),
                updated_at=datetime(2024, 1, 3, tzinfo=UTC),
            )
        ]

    def answer(
        self, question: str, history: Sequence[HistoryMessage]
    ) -> ChatResponse:
        if not self.ready:
            raise RagNotReadyError("index missing")
        self.last_question = question
        self.last_history = history
        return ChatResponse(
            answer="Grounded answer", citations=[], insufficient_evidence=False
        )


def client(service: FakeService) -> TestClient:
    app = create_app(rag_service=service, frontend_dir=Path("/not-present"))
    return TestClient(app)


def test_health() -> None:
    response = client(FakeService()).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_articles_match_frontend_contract() -> None:
    response = client(FakeService()).get("/articles")
    assert response.status_code == 200
    assert response.json()[0] == {
        "id": "42",
        "title": "测试文章",
        "author": "许哲",
        "url": "https://zhuanlan.zhihu.com/p/42",
        "created_at": "2024-01-02T00:00:00Z",
        "updated_at": "2024-01-03T00:00:00Z",
    }


def test_chat_validates_and_forwards_history() -> None:
    service = FakeService()
    response = client(service).post(
        "/chat",
        json={
            "question": "What is convexity?",
            "history": [{"role": "user", "content": "Earlier question"}],
        },
    )
    assert response.status_code == 200
    assert service.last_question == "What is convexity?"
    assert service.last_history[0].content == "Earlier question"


def test_chat_rejects_more_than_eight_history_messages() -> None:
    response = client(FakeService()).post(
        "/chat",
        json={
            "question": "Question",
            "history": [{"role": "user", "content": str(i)} for i in range(9)],
        },
    )
    assert response.status_code == 422


def test_chat_reports_pipeline_not_ready() -> None:
    response = client(FakeService(ready=False)).post(
        "/chat", json={"question": "Question", "history": []}
    )
    assert response.status_code == 503
    assert response.json() == {"detail": "index missing"}



def test_serves_frontend_without_shadowing_api(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<h1>Xuzhe RAG</h1>", encoding="utf-8")
    app = create_app(rag_service=FakeService(), frontend_dir=tmp_path)
    test_client = TestClient(app)

    assert "Xuzhe RAG" in test_client.get("/").text
    assert test_client.get("/health").json() == {"status": "ok"}
