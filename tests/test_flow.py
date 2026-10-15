import json
from datetime import date
from pathlib import Path

import pytest

from problem_discovery_agents.contracts import (
    AnalysisOutput, EvaluationOutput, EvaluationRecord, EvidenceItem, EvidenceRegistry,
    Finding, Independence, Problem, ProblemStatus, ResearchCoverage, ResearchOutput,
    ScoreAssessment, Stage1Scores, Stage1Status, VerificationStatus,
)
from problem_discovery_agents.analysis_agent.models import AnalysisDiagnostics, AnalysisRunResult
from problem_discovery_agents.evaluation_agent.models import EvaluationDiagnostics, EvaluationRunResult
from problem_discovery_agents.flow import FlowServices, ProblemDiscoveryFlow
from problem_discovery_agents.research_agent.models import ResearchDiagnostics, ResearchRunResult


def _research() -> ResearchOutput:
    evidence = EvidenceItem(evidence_id="EV-001", source_url="https://example.test/source", source_type="forum", published_at=None, accessed_at=date(2026, 10, 15), source_excerpt="I repeat this task.", observation="A developer reports recurring friction.", interpretation=None, evidence_class="firsthand", independence=Independence.UNCERTAIN, independence_rationale="Only one report is available.", verification_status=VerificationStatus.VERIFIED, limitations="No second report.")
    return ResearchOutput(findings=[Finding(finding_id="F-001", category="Developer Tools & Productivity", user_segment="developer", workflow="build", friction_hypothesis="Developers struggle to inspect build failures.", evidence_ids=["EV-001"])], evidence_registry=EvidenceRegistry(evidence=[evidence]), research_coverage=ResearchCoverage())


class Research:
    def __init__(self, calls: list[str]) -> None: self.calls = calls
    def run(self, request):
        self.calls.append("research")
        return ResearchRunResult(research_output=_research(), diagnostics=ResearchDiagnostics())


class Analysis:
    def __init__(self, calls: list[str]) -> None: self.calls = calls
    def run(self, research):
        self.calls.append("analysis")
        delta = EvidenceItem(evidence_id="EV-002", source_url="https://example.test/fix", source_type="documentation", published_at=None, accessed_at=date(2026, 10, 15), source_excerpt=None, observation="A possible alternative is documented.", interpretation=None, evidence_class="documentation", independence=Independence.UNCERTAIN, independence_rationale="Documentation is not a firsthand report.", verification_status=VerificationStatus.VERIFIED, limitations="No user-adoption evidence.")
        output = AnalysisOutput(problems=[Problem(problem_id="P-001", finding_ids=["F-001"], statement="Developers struggle to inspect build failures because context is fragmented, causing delays.", user_segment="developer", workflow="build", clustering_rationale="One finding.", status_rationale="One report requires validation.", evidence_ids=["EV-001"], independence_context="One uncertain firsthand report.", current_resolution_uncertainty="Current state unknown.", status=ProblemStatus.NEEDS_VALIDATION)], evidence_registry_delta=EvidenceRegistry(evidence=[delta]))
        return AnalysisRunResult(analysis_output=output, evidence_registry=research.evidence_registry.merge(output.evidence_registry_delta), diagnostics=AnalysisDiagnostics())


class Evaluation:
    def __init__(self, calls: list[str]) -> None: self.calls = calls
    def run(self, research, analysis, evidence_registry):
        self.calls.append("evaluation")
        score = ScoreAssessment(score=1, rationale="Limited evidence.", evidence_ids=["EV-001"])
        record = EvaluationRecord(problem_id="P-001", stage1_scores=Stage1Scores(problem_reality=score, frequency_recurrence=score, alternative_gap=score, meaningful_benefit=score), stage1_total=4, stage1_status=Stage1Status.LOW_PRIORITY)
        return EvaluationRunResult(evaluation_output=EvaluationOutput(evaluations=[record]), evidence_registry=evidence_registry, report_markdown="# Report\nP-001 EV-001 https://example.test/source", diagnostics=EvaluationDiagnostics())


def test_flow_writes_validated_artifacts_once(tmp_path: Path) -> None:
    calls: list[str] = []
    flow = ProblemDiscoveryFlow(services=FlowServices(Research(calls), Analysis(calls), Evaluation(calls)), output_root=tmp_path, category="Developer Tools & Productivity")
    flow.kickoff()
    assert calls == ["research", "analysis", "evaluation"]
    assert {path.name for path in flow.run_dir.iterdir()} == {"research_output.json", "analysis_output.json", "evaluation_output.json", "evidence_registry.json", "report.md", "run_manifest.json"}
    assert {item["evidence_id"] for item in json.loads((flow.run_dir / "evidence_registry.json").read_text())["evidence"]} == {"EV-001", "EV-002"}
    assert '"status": "succeeded"' in (flow.run_dir / "run_manifest.json").read_text()


def test_failure_stops_later_stages_and_keeps_prior_artifacts(tmp_path: Path) -> None:
    calls: list[str] = []
    class BadAnalysis(Analysis):
        def run(self, research):
            self.calls.append("analysis")
            raise ValueError("bad schema")
    flow = ProblemDiscoveryFlow(services=FlowServices(Research(calls), BadAnalysis(calls), Evaluation(calls)), output_root=tmp_path, category="Developer Tools & Productivity")
    with pytest.raises(ValueError, match="bad schema"):
        flow.kickoff()
    assert calls == ["research", "analysis"]
    assert (flow.run_dir / "research_output.json").exists()
    assert not (flow.run_dir / "evaluation_output.json").exists()
    assert '"status": "failed"' in (flow.run_dir / "run_manifest.json").read_text()


def test_evaluation_registry_mismatch_fails_without_final_artifacts(tmp_path: Path) -> None:
    calls: list[str] = []

    class BadEvaluation(Evaluation):
        def run(self, research, analysis, evidence_registry):
            result = super().run(research, analysis, evidence_registry)
            return result.model_copy(update={"evidence_registry": EvidenceRegistry(evidence=[])})

    flow = ProblemDiscoveryFlow(
        services=FlowServices(Research(calls), Analysis(calls), BadEvaluation(calls)),
        output_root=tmp_path,
        category="Developer Tools & Productivity",
    )
    with pytest.raises(ValueError, match="does not match the validated Analysis registry"):
        flow.kickoff()
    assert calls == ["research", "analysis", "evaluation"]
    assert (flow.run_dir / "research_output.json").exists()
    assert (flow.run_dir / "analysis_output.json").exists()
    assert not (flow.run_dir / "evaluation_output.json").exists()
    assert not (flow.run_dir / "evidence_registry.json").exists()
