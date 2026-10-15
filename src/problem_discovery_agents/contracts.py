"""Typed, serializable handoff contracts for the research pilot.

These models preserve provenance and uncertainty.  They deliberately do not
decide whether an observation is true or whether a score is well justified.
Cross-output checks and derived score rules live in :mod:`.validation`.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    field_validator,
    model_validator,
)


class ContractModel(BaseModel):
    """Shared strict model behavior for JSON handoff records."""

    model_config = ConfigDict(extra="forbid")


def _nonblank(value: str | None) -> str | None:
    if value is None:
        return None
    if not value.strip():
        raise ValueError("must not be blank")
    return value.strip()


class Independence(StrEnum):
    INDEPENDENT = "independent"
    DEPENDENT = "dependent"
    UNCERTAIN = "uncertain"


class VerificationStatus(StrEnum):
    VERIFIED = "verified"
    PARTIAL = "partial"
    UNVERIFIED = "unverified"


class ProblemStatus(StrEnum):
    CORROBORATED = "corroborated"
    NEEDS_VALIDATION = "needs_validation"
    OUTDATED = "outdated"
    CONTRADICTED = "contradicted"


class Stage1Status(StrEnum):
    STRONG = "Strong"
    PROMISING = "Promising"
    LOW_PRIORITY = "Low priority"
    RESEARCH_NEEDED = "Research needed"


class Stage2Value(StrEnum):
    STRONG = "Strong"
    PARTIAL = "Partial"
    WEAK = "Weak"
    UNKNOWN = "Unknown"


class GapOutcome(StrEnum):
    """Evidence-based conclusion about how well an alternative addresses a need."""

    SUPPORTED_GAP = "supported_gap"
    UNKNOWN_GAP = "unknown_gap"
    NEED_SUBSTANTIALLY_MET = "need_substantially_met"


class EvidenceItem(ContractModel):
    evidence_id: str
    source_url: AnyHttpUrl
    source_type: str
    published_at: date | None = None
    accessed_at: date
    source_excerpt: str | None = None
    observation: str
    interpretation: str | None = None
    evidence_class: str
    independence: Independence
    independence_rationale: str
    verification_status: VerificationStatus
    limitations: str

    _required_text = field_validator(
        "evidence_id", "source_type", "observation", "evidence_class",
        "independence_rationale", "limitations",
    )(_nonblank)
    _optional_text = field_validator("source_excerpt", "interpretation")(_nonblank)


class EvidenceRegistry(ContractModel):
    """The one authoritative collection of evidence records for a run."""

    evidence: list[EvidenceItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unique_ids(self) -> EvidenceRegistry:
        ids = [item.evidence_id for item in self.evidence]
        duplicates = sorted({item_id for item_id in ids if ids.count(item_id) > 1})
        if duplicates:
            raise ValueError(f"duplicate Evidence IDs: {', '.join(duplicates)}")
        return self

    def by_id(self) -> dict[str, EvidenceItem]:
        return {item.evidence_id: item for item in self.evidence}

    def add(self, item: EvidenceItem) -> EvidenceRegistry:
        return self.merge(EvidenceRegistry(evidence=[item]))

    def merge(self, incoming: EvidenceRegistry) -> EvidenceRegistry:
        """Return a new registry; never overwrite an existing Evidence ID."""

        existing = self.by_id()
        conflicts = sorted(existing.keys() & incoming.by_id().keys())
        if conflicts:
            raise ValueError(f"conflicting Evidence IDs: {', '.join(conflicts)}")
        return EvidenceRegistry(evidence=[*self.evidence, *incoming.evidence])


class ResearchCoverage(ContractModel):
    examined_workflows: list[str] = Field(default_factory=list)
    unexamined_workflows: list[str] = Field(default_factory=list)
    unsuccessful_searches: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    research_gaps: list[str] = Field(default_factory=list)


class Finding(ContractModel):
    finding_id: str
    category: str
    user_segment: str
    workflow: str
    friction_hypothesis: str
    evidence_ids: list[str] = Field(min_length=1)

    _text = field_validator(
        "finding_id", "category", "user_segment", "workflow", "friction_hypothesis"
    )(_nonblank)


class ResearchOutput(ContractModel):
    findings: list[Finding]
    evidence_registry: EvidenceRegistry
    research_coverage: ResearchCoverage


class Alternative(ContractModel):
    name: str
    kind: str
    what_it_solves: str
    gap_outcome: GapOutcome
    evidence_ids: list[str] = Field(default_factory=list)

    _text = field_validator("name", "kind", "what_it_solves")(_nonblank)


class Problem(ContractModel):
    problem_id: str
    finding_ids: list[str] = Field(min_length=1)
    statement: str
    user_segment: str
    workflow: str
    clustering_rationale: str
    status_rationale: str
    evidence_ids: list[str] = Field(min_length=1)
    independence_context: str
    alternatives: list[Alternative] = Field(default_factory=list)
    counterevidence_ids: list[str] = Field(default_factory=list)
    current_resolution_uncertainty: str
    research_gaps: list[str] = Field(default_factory=list)
    status: ProblemStatus

    _text = field_validator(
        "problem_id", "statement", "user_segment", "workflow", "clustering_rationale",
        "status_rationale",
        "independence_context", "current_resolution_uncertainty",
    )(_nonblank)


class AnalysisOutput(ContractModel):
    problems: list[Problem]
    evidence_registry_delta: EvidenceRegistry = Field(default_factory=EvidenceRegistry)


class ValidationGap(ContractModel):
    evidence_gap: str
    next_validation_action: str
    user_access_validation: str | None = None

    _text = field_validator("evidence_gap", "next_validation_action", "user_access_validation")(_nonblank)


class ScoreAssessment(ContractModel):
    score: StrictInt | None = Field(default=None, ge=0, le=3)
    rationale: str
    evidence_ids: list[str] = Field(default_factory=list)
    counterevidence_ids: list[str] = Field(default_factory=list)
    evidence_gap: str | None = None
    next_validation_action: str | None = None

    _text = field_validator("rationale", "evidence_gap", "next_validation_action")(_nonblank)


class Stage1Scores(ContractModel):
    problem_reality: ScoreAssessment
    frequency_recurrence: ScoreAssessment
    alternative_gap: ScoreAssessment
    meaningful_benefit: ScoreAssessment

    def assessments(self) -> tuple[ScoreAssessment, ScoreAssessment, ScoreAssessment, ScoreAssessment]:
        return (
            self.problem_reality,
            self.frequency_recurrence,
            self.alternative_gap,
            self.meaningful_benefit,
        )


class QualitativeAssessment(ContractModel):
    value: Stage2Value
    rationale: str

    _rationale = field_validator("rationale")(_nonblank)


class Stage2Assessment(ContractModel):
    assessments: dict[str, QualitativeAssessment] = Field(min_length=1)


class EvaluationRecord(ContractModel):
    problem_id: str
    stage1_scores: Stage1Scores
    stage1_total: StrictInt | None = Field(default=None, ge=0, le=12)
    stage1_status: Stage1Status
    user_benefit: str | None = None
    stage2_assessment: Stage2Assessment | None = None
    validation_gaps: list[ValidationGap] = Field(default_factory=list)

    _problem_id = field_validator("problem_id")(_nonblank)
    _benefit = field_validator("user_benefit")(_nonblank)


class EvaluationOutput(ContractModel):
    evaluations: list[EvaluationRecord]
