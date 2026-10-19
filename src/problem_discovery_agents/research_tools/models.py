"""Normalized retrieval records for the approved research-tool boundary.

These types intentionally preserve what a provider returned and what could not
be retrieved.  They are not evidence records and make no evidence-quality or
issue-resolution judgment.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RetrievalState(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    INACCESSIBLE = "inaccessible"
    FAILED = "failed"


class RetrievalError(BaseModel):
    """A safe provider/transport error; never include request credentials."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: str
    category: str
    message: str
    http_status: int | None = Field(default=None, ge=100, le=599)
    retryable: bool = False
    attempts: int = Field(default=1, ge=1)
    retry_after_seconds: float | None = Field(default=None, ge=0)


class Pagination(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    pages_fetched: int = Field(default=1, ge=0)
    next_page_available: bool = False
    truncated: bool = False


class SourceRecord(BaseModel):
    """Provider-returned material for one original source or GitHub object."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: str
    request_kind: str
    requested_url: str
    canonical_url: str | None = None
    source_type: str | None = None
    title: str | None = None
    text: str | None = None
    comments_text: str | None = None
    author: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    closed_at: datetime | None = None
    github_state: str | None = None
    retrieved_at: datetime
    retrieval_state: RetrievalState
    limitations: list[str] = Field(default_factory=list)
    error: RetrievalError | None = None
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)

    @field_validator("limitations")
    @classmethod
    def _no_blank_limitations(cls, values: list[str]) -> list[str]:
        if any(not value.strip() for value in values):
            raise ValueError("limitations must not contain blank values")
        return values


class CollectionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    items: list[SourceRecord] = Field(default_factory=list)
    primary_source: SourceRecord | None = None
    retrieved_at: datetime
    retrieval_state: RetrievalState
    pagination: Pagination = Field(default_factory=Pagination)
    limitations: list[str] = Field(default_factory=list)
    error: RetrievalError | None = None


class SearchLead(BaseModel):
    """Discovery-only Tavily result; ``snippet`` is never source content."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: str = "tavily"
    original_url: str
    title: str | None = None
    snippet: str | None = None
    published_at: datetime | None = None
    score: float | None = None
    retrieved_at: datetime
    limitations: list[str] = Field(default_factory=lambda: ["Search snippet is a discovery lead, not verified source content."])


class SearchResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    query: str
    leads: list[SearchLead] = Field(default_factory=list)
    retrieved_at: datetime
    retrieval_state: RetrievalState
    limitations: list[str] = Field(default_factory=list)
    error: RetrievalError | None = None
