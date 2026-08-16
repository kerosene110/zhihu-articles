"""Stable HTTP request and response models."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ArticleSummary(StrictModel):
    id: str
    title: str
    author: str
    url: str
    created_at: datetime
    updated_at: datetime


class HistoryMessage(StrictModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8_000)


class ChatRequest(StrictModel):
    question: str = Field(min_length=1, max_length=2_000)
    history: list[HistoryMessage] = Field(default_factory=list, max_length=8)


class Citation(StrictModel):
    article_id: str
    title: str
    url: str
    excerpt: str


class ChatResponse(StrictModel):
    answer: str
    citations: list[Citation]
    insufficient_evidence: bool
