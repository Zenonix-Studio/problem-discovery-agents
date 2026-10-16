"""Small, M4-local types for two-pass research orchestration.

The public handoff remains ``ResearchOutput`` from :mod:`..contracts`.
These types describe only request, planning, and in-memory diagnostics.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator


PILOT_CATEGORY = "Developer Tools & Productivity"


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _nonblank(value: str) -> str:
    if not value.strip():
        raise ValueError("must not be blank")
    return value.strip()


class ResearchRequest(_StrictModel):
    """The deliberately narrow, first-pilot research boundary."""

    category: str
    workflow_focus: str | None = None

    _category = field_validator("category")(_nonblank)
    _focus = field_validator("workflow_focus")(
        lambda value: _nonblank(value) if value is not None else None
    )

    @field_validator("category")
    @classmethod
    def _pilot_only(cls, value: str) -> str:
        if value != PILOT_CATEGORY:
            raise ValueError(
                f"M4 only supports the pilot category {PILOT_CATEGORY!r}; got {value!r}."
            )
        return value


class Query(_StrictModel):
    query: str
    purpose: str

    _text = field_validator("query", "purpose")(_nonblank)


class CandidateSignal(_StrictModel):
    """A model/planner proposal, not a verified research finding."""

    source_url: str
    user_segment: str
    workflow: str
    friction_hypothesis: str
    observation: str | None = None
    evidence_class: str = "firsthand"
    interpretation: str | None = None

    _text = field_validator(
        "source_url", "user_segment", "workflow", "friction_hypothesis", "evidence_class"
    )(_nonblank)
    _observation = field_validator("observation")(
        lambda value: _nonblank(value) if value is not None else None
    )
    _optional = field_validator("interpretation")(
        lambda value: _nonblank(value) if value is not None else None
    )

    @field_validator("friction_hypothesis")
    @classmethod
    def _solution_neutral(cls, value: str) -> str:
        forbidden = ("solution", "product", "score", "validated demand")
        if any(term in value.lower() for term in forbidden):
            raise ValueError("friction_hypothesis must remain solution-neutral and unscored")
        return value


class PassPlan(_StrictModel):
    workflows: list[str] = Field(default_factory=list)
    queries: list[Query] = Field(default_factory=list)

    @field_validator("workflows")
    @classmethod
    def _workflows_nonblank(cls, values: list[str]) -> list[str]:
        return [_nonblank(value) for value in values]


class CandidateSelection(_StrictModel):
    """Candidates selected only after the current pass has returned leads."""

    candidates: list[CandidateSignal] = Field(default_factory=list)


class InspectedSignal(_StrictModel):
    """Pass 1 proposal enriched only with retrieved-source context for Pass 2."""

    source_url: str
    user_segment: str
    workflow: str
    friction_hypothesis: str
    source_excerpt: str
    source_type: str
    author: str | None = None
    published_at: date | None = None
    limitations: list[str] = Field(default_factory=list)

    _text = field_validator(
        "source_url", "user_segment", "workflow", "friction_hypothesis", "source_excerpt", "source_type"
    )(_nonblank)
    _author = field_validator("author")(
        lambda value: _nonblank(value) if value is not None else None
    )

    @field_validator("limitations")
    @classmethod
    def _limitations_nonblank(cls, values: list[str]) -> list[str]:
        return [_nonblank(value) for value in values]


class ResearchDiagnostics(_StrictModel):
    pass_one_queries: list[str] = Field(default_factory=list)
    pass_two_queries: list[str] = Field(default_factory=list)
    unsuccessful_searches: list[str] = Field(default_factory=list)
    rejected_candidate_urls: list[str] = Field(default_factory=list)


class ResearchRunResult(_StrictModel):
    research_output: "ResearchOutput"
    diagnostics: ResearchDiagnostics


from ..contracts import ResearchOutput  # noqa: E402

ResearchRunResult.model_rebuild()
