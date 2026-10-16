"""Fixture-testable M6 evaluation, deterministic gate, and report service."""

from __future__ import annotations

from typing import Protocol

from ..contracts import (
    AnalysisOutput, EvaluationOutput, EvaluationRecord, EvidenceRegistry, ResearchOutput,
    QualitativeAssessment, Stage1Status, Stage2Assessment,
)
from ..validation import ContractValidationError, stage1_result, validate_analysis_output, validate_handoffs
from .models import (
    EvaluationDiagnostics, EvaluationRunResult, Stage1ProposalBatch, Stage2ProposalBatch,
)
from .report import build_report_context, validate_report_markdown


class EvaluationPlanner(Protocol):
    def propose_stage1(self, research: ResearchOutput, analysis: AnalysisOutput, registry: EvidenceRegistry) -> Stage1ProposalBatch: ...
    def propose_stage2(self, evaluation: EvaluationOutput, team_context: str) -> Stage2ProposalBatch: ...
    def write_report(self, report_context: dict[str, object]) -> str: ...


class EvaluationAgent:
    """Run M6 with one injected agent and deterministic score/gate authority."""

    def __init__(self, *, planner: EvaluationPlanner, team_context: str | None = None) -> None:
        self._planner = planner
        self._team_context = team_context or (
            "Team strengths: AI/ML, backend, evaluation and observability; iOS/mobile "
            "architecture, developer tooling, MCP, and release workflows."
        )

    def run(
        self, research: ResearchOutput, analysis: AnalysisOutput, evidence_registry: EvidenceRegistry,
    ) -> EvaluationRunResult:
        merged_registry = validate_analysis_output(research, analysis)
        if evidence_registry.model_dump(mode="json") != merged_registry.model_dump(mode="json"):
            raise ContractValidationError((
                "Evaluation must receive the exact merged authoritative EvidenceRegistry from Analysis",
            ))

        stage1 = self._planner.propose_stage1(research, analysis, merged_registry)
        evaluation = self._assemble_stage1(analysis, stage1)
        validate_handoffs(research, analysis, evaluation)

        eligible = [
            record.problem_id for record in evaluation.evaluations
            if record.stage1_status in {Stage1Status.STRONG, Stage1Status.PROMISING}
            and record.user_benefit is not None
        ]
        if eligible:
            eligible_evaluation = EvaluationOutput(evaluations=[
                record.model_copy(deep=True)
                for record in evaluation.evaluations
                if record.problem_id in eligible
            ])
            stage2 = self._planner.propose_stage2(eligible_evaluation, self._team_context)
            self._attach_stage2(evaluation, eligible, stage2)
            validate_handoffs(research, analysis, evaluation)

        report = self._planner.write_report(build_report_context(research, analysis, evaluation, merged_registry))
        validate_report_markdown(report, evaluation, merged_registry)
        return EvaluationRunResult(
            evaluation_output=evaluation, evidence_registry=merged_registry,
            report_markdown=report, diagnostics=EvaluationDiagnostics(eligible_problem_ids=eligible),
        )

    @staticmethod
    def _assemble_stage1(analysis: AnalysisOutput, batch: Stage1ProposalBatch) -> EvaluationOutput:
        expected = [problem.problem_id for problem in analysis.problems]
        received = [proposal.problem_id for proposal in batch.proposals]
        duplicates = sorted({item_id for item_id in received if received.count(item_id) > 1})
        missing = sorted(set(expected) - set(received))
        unknown = sorted(set(received) - set(expected))
        if duplicates or missing or unknown:
            details: list[str] = []
            if duplicates:
                details.append("duplicate Evaluation proposal Problem IDs: " + ", ".join(duplicates))
            if missing:
                details.append("missing Evaluation proposals for Problem IDs: " + ", ".join(missing))
            if unknown:
                details.append("Evaluation proposals reference unknown Problem IDs: " + ", ".join(unknown))
            raise ContractValidationError(details)
        proposals = {proposal.problem_id: proposal for proposal in batch.proposals}
        records: list[EvaluationRecord] = []
        for problem_id in expected:
            proposal = proposals[problem_id]
            total, status = stage1_result(proposal.stage1_scores)
            records.append(EvaluationRecord(
                problem_id=problem_id, stage1_scores=proposal.stage1_scores,
                stage1_total=total, stage1_status=status, user_benefit=proposal.user_benefit,
                validation_gaps=proposal.validation_gaps,
            ))
        return EvaluationOutput(evaluations=records)

    @staticmethod
    def _attach_stage2(
        evaluation: EvaluationOutput, eligible: list[str], batch: Stage2ProposalBatch,
    ) -> None:
        received = [proposal.problem_id for proposal in batch.proposals]
        duplicates = sorted({item_id for item_id in received if received.count(item_id) > 1})
        missing = sorted(set(eligible) - set(received))
        unknown = sorted(set(received) - set(eligible))
        if duplicates or missing or unknown:
            details: list[str] = []
            if duplicates:
                details.append("duplicate Stage 2 proposal Problem IDs: " + ", ".join(duplicates))
            if missing:
                details.append("missing Stage 2 proposals for eligible Problem IDs: " + ", ".join(missing))
            if unknown:
                details.append("Stage 2 proposals reference ineligible Problem IDs: " + ", ".join(unknown))
            raise ContractValidationError(details)
        by_id = {proposal.problem_id: proposal for proposal in batch.proposals}
        shape_errors: list[str] = []
        for problem_id, proposal in by_id.items():
            names = [item.dimension.casefold() for item in proposal.assessments]
            if not names:
                shape_errors.append(f"Stage 2 proposal for {problem_id} has no assessments")
            repeated = sorted({name for name in names if names.count(name) > 1})
            if repeated:
                shape_errors.append(
                    f"Stage 2 proposal for {problem_id} has duplicate dimensions: " + ", ".join(repeated)
                )
        if shape_errors:
            raise ContractValidationError(shape_errors)
        for record in evaluation.evaluations:
            if record.problem_id in by_id:
                record.stage2_assessment = Stage2Assessment(
                    assessments={
                        item.dimension: QualitativeAssessment(value=item.value, rationale=item.rationale)
                        for item in by_id[record.problem_id].assessments
                    }
                )
