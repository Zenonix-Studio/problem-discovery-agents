import json
from datetime import date
from pathlib import Path

from problem_discovery_agents.artifacts import ArtifactWriter
from problem_discovery_agents.contracts import EvidenceItem, EvidenceRegistry, Independence, ResearchCoverage, ResearchOutput, VerificationStatus


def _research() -> ResearchOutput:
    return ResearchOutput(findings=[], evidence_registry=EvidenceRegistry(evidence=[EvidenceItem(evidence_id="EV-001", source_url="https://example.test/source", source_type="forum", published_at=None, accessed_at=date(2026, 10, 15), source_excerpt=None, observation="Observed source text.", interpretation=None, evidence_class="firsthand", independence=Independence.UNCERTAIN, independence_rationale="No comparison report.", verification_status=VerificationStatus.PARTIAL, limitations="Partial retrieval.")]), research_coverage=ResearchCoverage())


def test_writer_creates_unique_safe_failure_manifest(tmp_path: Path) -> None:
    first = ArtifactWriter(tmp_path, request={"category": "Developer Tools & Productivity", "workflow_focus": None})
    second = ArtifactWriter(tmp_path, request={"category": "Developer Tools & Productivity", "workflow_focus": None})
    assert first.run_dir != second.run_dir
    first.write_research(_research(), {"safe": "diagnostic"})
    first.fail("analysis", ValueError("safe error"), {})
    manifest = json.loads((first.run_dir / "run_manifest.json").read_text())
    assert manifest["status"] == "failed"
    assert manifest["completed_stage"] == "research"
    assert (first.run_dir / "research_output.json").exists()
    assert not (first.run_dir / "report.md").exists()


def test_failure_manifest_does_not_persist_arbitrary_error_text(tmp_path: Path) -> None:
    writer = ArtifactWriter(tmp_path, request={"category": "Developer Tools & Productivity", "workflow_focus": None})
    writer.fail("research", RuntimeError("sentinel-secret-value"), {})
    manifest = json.loads((writer.run_dir / "run_manifest.json").read_text())
    assert manifest["error"] == "RuntimeError: operation failed; inspect the failed stage and safe diagnostics."
    assert "sentinel-secret-value" not in (writer.run_dir / "run_manifest.json").read_text()


def test_writer_merges_stage_diagnostics(tmp_path: Path) -> None:
    writer = ArtifactWriter(tmp_path, request={"category": "Developer Tools & Productivity", "workflow_focus": None})
    writer.write_research(_research(), {"research": {"rejected_candidate_urls": ["https://example.test/off-lead"]}})
    writer.fail("analysis", ValueError("ignored"), {"usage": {"known": False}})
    manifest = json.loads((writer.run_dir / "run_manifest.json").read_text())
    assert manifest["diagnostics"] == {
        "research": {"rejected_candidate_urls": ["https://example.test/off-lead"]},
        "usage": {"known": False},
    }
