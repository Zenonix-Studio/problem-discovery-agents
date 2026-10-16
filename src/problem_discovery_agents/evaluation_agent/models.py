"""Private proposal and result models for the M6 Evaluation Agent."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..contracts import (
    EvaluationOutput,
    EvidenceRegistry,
    QualitativeAssessment,
    ScoreAssessment,
    Stage1Scores,
    Stage2Value,
    ValidationGap,
)


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _nonblank(value: str | None) -> str | None:
    if value is None:
        return None
    if not value.strip():
        raise ValueError("must not be blank")
    return value.strip()


class Stage1Proposal(_StrictModel):
    """LLM-proposed judgments only; derived fields deliberately do not exist."""

    problem_id: str
    stage1_scores: Stage1Scores
    user_benefit: str | None = None
    validation_gaps: list[ValidationGap] = Field(default_factory=list)

    _text = field_validator("problem_id", "user_benefit")(_nonblank)


class Stage1ProposalBatch(_StrictModel):
    proposals: list[Stage1Proposal]


class Stage2Item(_StrictModel):
    """One qualitative Stage 2 judgment. A list item, not a dict entry, because OpenAI
    structured output rejects the `minProperties`/dict schema a mapping would produce."""

    dimension: str
    value: Stage2Value
    rationale: str

    _text = field_validator("dimension", "rationale")(_nonblank)


class Stage2Proposal(_StrictModel):
    problem_id: str
    assessments: list[Stage2Item]

    _problem_id = field_validator("problem_id")(_nonblank)


class Stage2ProposalBatch(_StrictModel):
    proposals: list[Stage2Proposal]


class EvaluationDiagnostics(_StrictModel):
    eligible_problem_ids: list[str] = Field(default_factory=list)


class EvaluationRunResult(_StrictModel):
    evaluation_output: EvaluationOutput
    evidence_registry: EvidenceRegistry
    report_markdown: str
    diagnostics: EvaluationDiagnostics
