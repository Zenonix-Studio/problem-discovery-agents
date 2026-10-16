"""Private M5 decision and diagnostic models for one-pass analysis."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..contracts import AnalysisOutput, EvidenceClass, EvidenceRegistry, GapOutcome, ProblemStatus


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _nonblank(value: str) -> str:
    if not value.strip():
        raise ValueError("must not be blank")
    return value.strip()


class RetrievalIntent(_StrictModel):
    query: str
    purpose: str

    _text = field_validator("query", "purpose")(_nonblank)


class SourceRequest(_StrictModel):
    source_url: str
    evidence_class: EvidenceClass = "documentation"

    _text = field_validator("source_url", "evidence_class")(_nonblank)


class AlternativeProposal(_StrictModel):
    name: str
    kind: str
    what_it_solves: str
    gap_outcome: GapOutcome
    source_urls: list[str] = Field(default_factory=list)

    _text = field_validator("name", "kind", "what_it_solves")(_nonblank)


class ProblemProposal(_StrictModel):
    finding_ids: list[str] = Field(min_length=1)
    statement: str
    user_segment: str
    workflow: str
    clustering_rationale: str
    status_rationale: str
    evidence_ids: list[str] = Field(min_length=1)
    independence_context: str
    alternatives: list[AlternativeProposal] = Field(default_factory=list)
    counterevidence_intents: list[RetrievalIntent] = Field(min_length=1)
    counterevidence_sources: list[SourceRequest] = Field(default_factory=list)
    current_resolution_uncertainty: str
    research_gaps: list[str] = Field(default_factory=list)
    status: ProblemStatus

    _text = field_validator(
        "statement", "user_segment", "workflow", "clustering_rationale", "status_rationale",
        "independence_context", "current_resolution_uncertainty",
    )(_nonblank)


class AnalysisPlan(_StrictModel):
    retrieval_intents: list[RetrievalIntent] = Field(default_factory=list)
    problems: list[ProblemProposal] = Field(default_factory=list)


class AnalysisDiagnostics(_StrictModel):
    queries: list[str] = Field(default_factory=list)
    unsuccessful_searches: list[str] = Field(default_factory=list)
    rejected_source_urls: list[str] = Field(default_factory=list)


class AnalysisRunResult(_StrictModel):
    analysis_output: AnalysisOutput
    evidence_registry: EvidenceRegistry
    diagnostics: AnalysisDiagnostics
