from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNBOOK = ROOT / "docs" / "M8_PILOT_RUNBOOK.md"
REVIEW_TEMPLATE = ROOT / "docs" / "templates" / "M8_PILOT_REVIEW_TEMPLATE.md"
RERUN_TEMPLATE = ROOT / "docs" / "templates" / "M8_FIX_RERUN_LOG_TEMPLATE.md"


CRITERIA = (
    "Evidence Integrity",
    "Research Quality",
    "Analysis Quality",
    "Evaluation Consistency",
    "Report Usability",
)


def test_review_template_requires_every_problem_audit_and_five_verdicts() -> None:
    content = REVIEW_TEMPLATE.read_text(encoding="utf-8")

    assert "## Record-by-record audit" in content
    assert "every `Problem ID`" in content
    assert "`Pass` or `Fail`" in content
    assert "## Unresolved uncertainty and next validation" in content
    for criterion in CRITERIA:
        assert criterion in content


def test_rerun_template_requires_targeted_comparison_without_scope_expansion() -> None:
    content = RERUN_TEMPLATE.read_text(encoding="utf-8")

    assert "## Targeted correction proposal" in content
    assert "Responsible boundary" in content
    assert "## Rerun comparison" in content
    assert "Newly introduced issues" in content
    assert "does not authorize an automatic rerun, scope expansion" in content


def test_runbook_preserves_human_authorization_and_artifact_audit_boundaries() -> None:
    content = RUNBOOK.read_text(encoding="utf-8")

    assert "A human has authorized" in content
    assert "Evaluation → Problem → Finding/Evidence → original URL" in content
    assert "A successful Flow or test suite cannot itself pass" in content
    assert "Do not automatically rerun" in content
