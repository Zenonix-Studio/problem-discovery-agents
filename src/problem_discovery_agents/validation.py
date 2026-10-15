"""Deterministic integrity, score, and eligibility checks for M2 contracts."""

from __future__ import annotations

from collections.abc import Iterable

from .contracts import (
    AnalysisOutput,
    EvaluationOutput,
    ResearchOutput,
    ScoreAssessment,
    Stage1Scores,
    Stage1Status,
)


class ContractValidationError(ValueError):
    """Aggregates machine-checkable contract failures for an actionable handoff."""

    def __init__(self, violations: Iterable[str]):
        self.violations = tuple(violations)
        super().__init__("Contract validation failed: " + "; ".join(self.violations))


def stage1_result(scores: Stage1Scores) -> tuple[int | None, Stage1Status]:
    """Compute the only permitted Stage 1 total and label."""

    values = [assessment.score for assessment in scores.assessments()]
    if any(value is None for value in values):
        return None, Stage1Status.RESEARCH_NEEDED
    total = sum(value for value in values if value is not None)
    if total >= 10:
        return total, Stage1Status.STRONG
    if total >= 7:
        return total, Stage1Status.PROMISING
    return total, Stage1Status.LOW_PRIORITY


def _duplicates(ids: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for item_id in ids:
        if item_id in seen:
            duplicates.add(item_id)
        seen.add(item_id)
    return sorted(duplicates)


def _check_references(label: str, ids: Iterable[str], available: set[str], errors: list[str]) -> None:
    for item_id in ids:
        if item_id not in available:
            errors.append(f"{label} references unknown ID {item_id!r}")


def _validate_assessment(
    label: str, assessment: ScoreAssessment, evidence_ids: set[str], errors: list[str]
) -> None:
    _check_references(f"{label}.evidence_ids", assessment.evidence_ids, evidence_ids, errors)
    _check_references(
        f"{label}.counterevidence_ids", assessment.counterevidence_ids, evidence_ids, errors
    )
    if assessment.score is not None and not assessment.evidence_ids:
        errors.append(f"{label} is scored but has no Evidence IDs")
    if assessment.score is None:
        if assessment.evidence_gap is None:
            errors.append(f"{label} is unscoreable and lacks an evidence gap")
        if assessment.next_validation_action is None:
            errors.append(
                f"{label} is unscoreable and lacks a next validation action"
            )


def validate_handoffs(
    research: ResearchOutput, analysis: AnalysisOutput, evaluation: EvaluationOutput
) -> None:
    """Fail fast on structural and derived-state violations across all handoffs."""

    errors: list[str] = []
    findings = {finding.finding_id: finding for finding in research.findings}
    finding_duplicates = _duplicates(finding.finding_id for finding in research.findings)
    if finding_duplicates:
        errors.append(f"duplicate Finding IDs: {', '.join(finding_duplicates)}")

    try:
        registry = research.evidence_registry.merge(analysis.evidence_registry_delta)
    except ValueError as error:
        errors.append(str(error))
        registry = research.evidence_registry
    evidence_ids = set(registry.by_id())

    for finding in research.findings:
        _check_references(f"Finding {finding.finding_id}", finding.evidence_ids, evidence_ids, errors)

    problem_duplicates = _duplicates(problem.problem_id for problem in analysis.problems)
    if problem_duplicates:
        errors.append(f"duplicate Problem IDs: {', '.join(problem_duplicates)}")
    problem_ids = {problem.problem_id for problem in analysis.problems}
    for problem in analysis.problems:
        _check_references(f"Problem {problem.problem_id}.finding_ids", problem.finding_ids, set(findings), errors)
        _check_references(f"Problem {problem.problem_id}.evidence_ids", problem.evidence_ids, evidence_ids, errors)
        _check_references(
            f"Problem {problem.problem_id}.counterevidence_ids",
            problem.counterevidence_ids,
            evidence_ids,
            errors,
        )
        for alternative in problem.alternatives:
            _check_references(
                f"Problem {problem.problem_id}.alternative[{alternative.name}].evidence_ids",
                alternative.evidence_ids,
                evidence_ids,
                errors,
            )

    evaluation_duplicates = _duplicates(record.problem_id for record in evaluation.evaluations)
    if evaluation_duplicates:
        errors.append(f"duplicate Evaluation problem IDs: {', '.join(evaluation_duplicates)}")
    for record in evaluation.evaluations:
        if record.problem_id not in problem_ids:
            errors.append(f"Evaluation references unknown Problem ID {record.problem_id!r}")
        for name, assessment in zip(
            ("problem_reality", "frequency_recurrence", "alternative_gap", "meaningful_benefit"),
            record.stage1_scores.assessments(),
            strict=True,
        ):
            _validate_assessment(
                f"Evaluation {record.problem_id}.{name}", assessment, evidence_ids, errors
            )
        computed_total, computed_status = stage1_result(record.stage1_scores)
        if record.stage1_total != computed_total:
            errors.append(
                f"Evaluation {record.problem_id} has stage1_total {record.stage1_total!r}; "
                f"expected {computed_total!r}"
            )
        if record.stage1_status != computed_status:
            errors.append(
                f"Evaluation {record.problem_id} has stage1_status {record.stage1_status!r}; "
                f"expected {computed_status.value!r}"
            )
        eligible = computed_status in {Stage1Status.STRONG, Stage1Status.PROMISING}
        if record.stage2_assessment is not None and (not eligible or record.user_benefit is None):
            errors.append(
                f"Evaluation {record.problem_id} has Stage 2 without fully scored Strong/Promising "
                "status and a nonblank user benefit"
            )

    if errors:
        raise ContractValidationError(errors)
