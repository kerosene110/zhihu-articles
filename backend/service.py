"""The single integration boundary between FastAPI and learner-owned RAG code."""

from collections.abc import Sequence
from typing import Protocol

from backend.schemas import ArticleSummary, ChatResponse, HistoryMessage


class RagNotReadyError(RuntimeError):
    """The index or model providers are not configured."""


class RagService(Protocol):
    """What the web layer needs from the completed RAG pipeline."""

    def list_articles(self) -> Sequence[ArticleSummary]: ...

    def answer(
        self, question: str, history: Sequence[HistoryMessage]
    ) -> ChatResponse: ...


class UnavailableRagService:
    """Fail closed until the learner-owned pipeline is integrated."""

    def list_articles(self) -> Sequence[ArticleSummary]:
        return []

    def answer(
        self, question: str, history: Sequence[HistoryMessage]
    ) -> ChatResponse:
        raise RagNotReadyError(
            "The RAG service is not configured yet. Build and index the corpus first."
        )
