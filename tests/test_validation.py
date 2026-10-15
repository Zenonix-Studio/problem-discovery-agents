from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from problem_discovery_agents.contracts import (
    AnalysisOutput,
    EvaluationOutput,
    EvaluationRecord,
    EvidenceItem,
    EvidenceRegistry,
    Finding,
    GapOutcome,
    Independence,
    Problem,
    ProblemStatus,
    ResearchCoverage,
    ResearchOutput,
    ScoreAssessment,
    Stage1Scores,
    Stage1Status,
    Stage2Assessment,
    VerificationStatus,
)
from problem_discovery_agents.validation import (
    ContractValidationError,
    stage1_result,
    validate_handoffs,
    validate_research_output,
)


def _evidence() -> EvidenceItem:
    return EvidenceItem(
        evidence_id="EV-001", source_url="https://example.test/source", source_type="forum",
        accessed_at=date(2026, 10, 15), observation="A recurring friction is reported.",
        evidence_class="firsthand", independence=Independence.INDEPENDENT,
        independence_rationale="Separate author.", verification_status=VerificationStatus.VERIFIED,
        limitations="Small sample.",
    )


def _chain(scores: Stage1Scores, *, total: int | None, status: Stage1Status, stage2: bool = False) -> tuple[ResearchOutput, AnalysisOutput, EvaluationOutput]:
    research = ResearchOutput(
        findings=[Finding(finding_id="F-001", category="Developer Tools & Productivity", user_segment="developers", workflow="CI debugging", friction_hypothesis="Users struggle to identify CI failures.", evidence_ids=["EV-001"])],
        evidence_registry=EvidenceRegistry(evidence=[_evidence()]), research_coverage=ResearchCoverage(),
    )
    analysis = AnalysisOutput(problems=[Problem(problem_id="P-001", finding_ids=["F-001"], statement="Developers struggle to diagnose CI failures.", user_segment="developers", workflow="CI debugging", clustering_rationale="Same workflow and friction.", status_rationale="One report requires further validation.", evidence_ids=["EV-001"], independence_context="One independent report.", current_resolution_uncertainty="Current resolution is unknown.", status=ProblemStatus.NEEDS_VALIDATION)])
    evaluation = EvaluationOutput(evaluations=[EvaluationRecord(problem_id="P-001", stage1_scores=scores, stage1_total=total, stage1_status=status, user_benefit="Fewer repeated debugging steps." if stage2 else None, stage2_assessment=Stage2Assessment(assessments={"feasibility": {"value": "Partial", "rationale": "Requires later validation."}}) if stage2 else None)])
    return research, analysis, evaluation


def _scored(value: int) -> ScoreAssessment:
    return ScoreAssessment(score=value, rationale="Evidence supports this bounded score.", evidence_ids=["EV-001"])


@pytest.mark.parametrize(
    ("values", "expected_total", "expected_status"),
    [((0, 0, 0, 0), 0, Stage1Status.LOW_PRIORITY), ((3, 3, 0, 0), 6, Stage1Status.LOW_PRIORITY), ((2, 2, 2, 1), 7, Stage1Status.PROMISING), ((3, 2, 2, 2), 9, Stage1Status.PROMISING), ((3, 3, 2, 2), 10, Stage1Status.STRONG), ((3, 3, 3, 3), 12, Stage1Status.STRONG)],
)
def test_stage1_boundaries_are_deterministic(values: tuple[int, int, int, int], expected_total: int, expected_status: Stage1Status) -> None:
    scores = Stage1Scores(problem_reality=_scored(values[0]), frequency_recurrence=_scored(values[1]), alternative_gap=_scored(values[2]), meaningful_benefit=_scored(values[3]))
    assert stage1_result(scores) == (expected_total, expected_status)
    validate_handoffs(*_chain(scores, total=expected_total, status=expected_status, stage2=expected_status in {Stage1Status.STRONG, Stage1Status.PROMISING}))


def test_unscoreable_dimension_requires_gap_when_it_has_no_evidence() -> None:
    scores = Stage1Scores(problem_reality=_scored(3), frequency_recurrence=_scored(2), alternative_gap=ScoreAssessment(score=None, rationale="No inspected alternative supports a defensible anchor."), meaningful_benefit=_scored(3))
    research, analysis, evaluation = _chain(scores, total=None, status=Stage1Status.RESEARCH_NEEDED)

    with pytest.raises(ContractValidationError, match="lacks an evidence gap"):
        validate_handoffs(research, analysis, evaluation)

    scores.alternative_gap.evidence_gap = "No firsthand account explains whether alternatives fail."
    scores.alternative_gap.next_validation_action = "Interview affected users about existing alternatives."
    validate_handoffs(research, analysis, evaluation)


def test_unscoreable_dimension_keeps_available_evidence_ids() -> None:
    scores = Stage1Scores(
        problem_reality=_scored(3),
        frequency_recurrence=_scored(2),
        alternative_gap=ScoreAssessment(
            score=None,
            rationale="The inspected evidence does not establish a score anchor.",
            evidence_ids=["EV-001"],
        ),
        meaningful_benefit=_scored(3),
    )
    research, analysis, evaluation = _chain(
        scores, total=None, status=Stage1Status.RESEARCH_NEEDED
    )

    with pytest.raises(ContractValidationError, match="lacks an evidence gap"):
        validate_handoffs(research, analysis, evaluation)

    scores.alternative_gap.evidence_gap = "The available evidence does not establish an anchor."
    scores.alternative_gap.next_validation_action = "Collect firsthand reports about alternatives."
    validate_handoffs(research, analysis, evaluation)


def test_dangling_reference_and_inconsistent_derived_state_fail() -> None:
    scores = Stage1Scores(problem_reality=_scored(3), frequency_recurrence=_scored(3), alternative_gap=_scored(2), meaningful_benefit=_scored(2))
    research, analysis, evaluation = _chain(scores, total=9, status=Stage1Status.PROMISING)
    analysis.problems[0].finding_ids = ["F-missing"]

    with pytest.raises(ContractValidationError) as raised:
        validate_handoffs(research, analysis, evaluation)

    assert "unknown ID 'F-missing'" in str(raised.value)
    assert "stage1_total 9; expected 10" in str(raised.value)


def test_stage2_is_gated_and_score_range_is_enforced() -> None:
    for value in (4, True, 1.0):
        with pytest.raises(ValidationError):
            ScoreAssessment(score=value, rationale="Invalid.", evidence_ids=["EV-001"])

    scores = Stage1Scores(problem_reality=_scored(1), frequency_recurrence=_scored(1), alternative_gap=_scored(1), meaningful_benefit=_scored(1))
    research, analysis, evaluation = _chain(scores, total=4, status=Stage1Status.LOW_PRIORITY, stage2=True)

    with pytest.raises(ContractValidationError, match="Stage 2"):
        validate_handoffs(research, analysis, evaluation)


def test_stage1_total_requires_a_strict_integer() -> None:
    scores = Stage1Scores(
        problem_reality=_scored(3),
        frequency_recurrence=_scored(3),
        alternative_gap=_scored(2),
        meaningful_benefit=_scored(2),
    )
    for value in (True, 10.0, 13):
        with pytest.raises(ValidationError):
            EvaluationRecord(
                problem_id="P-001",
                stage1_scores=scores,
                stage1_total=value,
                stage1_status=Stage1Status.STRONG,
            )


def test_duplicate_finding_and_problem_ids_fail() -> None:
    scores = Stage1Scores(problem_reality=_scored(3), frequency_recurrence=_scored(3), alternative_gap=_scored(2), meaningful_benefit=_scored(2))
    research, analysis, evaluation = _chain(scores, total=10, status=Stage1Status.STRONG)
    research.findings.append(research.findings[0].model_copy())
    analysis.problems.append(analysis.problems[0].model_copy())

    with pytest.raises(ContractValidationError) as raised:
        validate_handoffs(research, analysis, evaluation)

    assert "duplicate Finding IDs: F-001" in str(raised.value)
    assert "duplicate Problem IDs: P-001" in str(raised.value)


def test_research_only_validation_does_not_need_downstream_placeholders() -> None:
    scores = Stage1Scores(problem_reality=_scored(3), frequency_recurrence=_scored(3), alternative_gap=_scored(2), meaningful_benefit=_scored(2))
    research, _, _ = _chain(scores, total=10, status=Stage1Status.STRONG)
    validate_research_output(research)

    research.findings[0].evidence_ids = ["EV-missing"]
    with pytest.raises(ContractValidationError, match="Finding F-001 references unknown ID 'EV-missing'"):
        validate_research_output(research)


def test_alternative_gap_outcome_is_a_closed_vocabulary() -> None:
    assert GapOutcome.SUPPORTED_GAP.value == "supported_gap"
    with pytest.raises(ValidationError):
        Problem.model_validate(
            {
                "problem_id": "P-001",
                "finding_ids": ["F-001"],
                "statement": "A statement.",
                "user_segment": "developers",
                "workflow": "CI",
                "clustering_rationale": "A rationale.",
                "status_rationale": "A status rationale.",
                "evidence_ids": ["EV-001"],
                "independence_context": "Known.",
                "alternatives": [{"name": "Built-in", "kind": "built-in", "what_it_solves": "Part of the task.", "gap_outcome": "maybe"}],
                "current_resolution_uncertainty": "Unknown.",
                "status": "needs_validation",
            }
        )


def test_invalid_problem_status_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Problem.model_validate(
            {
                "problem_id": "P-001",
                "finding_ids": ["F-001"],
                "statement": "A statement.",
                "user_segment": "developers",
                "workflow": "CI",
                "clustering_rationale": "A rationale.",
                "status_rationale": "A status rationale.",
                "evidence_ids": ["EV-001"],
                "independence_context": "Known.",
                "current_resolution_uncertainty": "Unknown.",
                "status": "resolved",
            }
        )


@pytest.mark.parametrize(
    ("scores", "total", "status"),
    [
        (
            Stage1Scores(
                problem_reality=_scored(3),
                frequency_recurrence=_scored(2),
                alternative_gap=ScoreAssessment(
                    score=None,
                    rationale="Alternative evidence is insufficient.",
                    evidence_ids=["EV-001"],
                ),
                meaningful_benefit=_scored(3),
            ),
            None,
            Stage1Status.RESEARCH_NEEDED,
        ),
        (
            Stage1Scores(
                problem_reality=_scored(3),
                frequency_recurrence=_scored(3),
                alternative_gap=_scored(2),
                meaningful_benefit=_scored(2),
            ),
            10,
            Stage1Status.STRONG,
        ),
    ],
)
def test_stage2_requires_eligibility_and_user_benefit(
    scores: Stage1Scores, total: int | None, status: Stage1Status
) -> None:
    research, analysis, evaluation = _chain(scores, total=total, status=status, stage2=True)
    evaluation.evaluations[0].user_benefit = None

    with pytest.raises(ContractValidationError, match="Stage 2"):
        validate_handoffs(research, analysis, evaluation)
