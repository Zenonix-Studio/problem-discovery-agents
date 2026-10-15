from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from problem_discovery_agents.contracts import (
    AnalysisOutput,
    EvaluationOutput,
    EvidenceItem,
    Finding,
    Independence,
    ResearchOutput,
    VerificationStatus,
)


def test_evidence_round_trip_preserves_nullable_provenance() -> None:
    item = EvidenceItem(
        evidence_id="EV-001",
        source_url="https://example.test/original",
        source_type="GitHub Issue",
        published_at=None,
        accessed_at=date(2026, 10, 15),
        source_excerpt=None,
        observation="The source supports this bounded observation.",
        interpretation=None,
        evidence_class="firsthand",
        independence=Independence.UNCERTAIN,
        independence_rationale="Author relationship is not known.",
        verification_status=VerificationStatus.PARTIAL,
        limitations="The full thread was unavailable.",
    )

    restored = EvidenceItem.model_validate_json(item.model_dump_json())

    assert restored == item
    assert restored.published_at is None
    assert restored.source_excerpt is None


def test_representative_json_fixture_is_a_valid_evidence_record() -> None:
    fixture = Path(__file__).parent / "fixtures" / "contracts" / "evidence.json"

    item = EvidenceItem.model_validate_json(fixture.read_text())

    assert item.evidence_id == "EV-001"
    assert item.published_at is None


@pytest.mark.parametrize(
    ("filename", "model"),
    [
        ("research_output.json", ResearchOutput),
        ("analysis_output.json", AnalysisOutput),
        ("evaluation_output.json", EvaluationOutput),
    ],
)
def test_representative_handoff_fixtures_are_valid(filename: str, model: type[object]) -> None:
    fixture = Path(__file__).parent / "fixtures" / "contracts" / filename

    assert hasattr(model, "model_validate_json")
    model.model_validate_json(fixture.read_text())  # type: ignore[attr-defined]


def test_dangling_reference_fixture_remains_structurally_parseable() -> None:
    fixture = Path(__file__).parent / "fixtures" / "contracts" / "finding_dangling_evidence.json"

    finding = Finding.model_validate_json(fixture.read_text())

    assert finding.evidence_ids == ["EV-MISSING"]


@pytest.mark.parametrize("field,value", [("evidence_id", " "), ("source_type", "")])
def test_required_evidence_text_cannot_be_blank(field: str, value: str) -> None:
    payload = {
        "evidence_id": "EV-001",
        "source_url": "https://example.test/original",
        "source_type": "GitHub Issue",
        "accessed_at": "2026-10-15",
        "observation": "Observed friction.",
        "evidence_class": "firsthand",
        "independence": "independent",
        "independence_rationale": "Separate author.",
        "verification_status": "verified",
        "limitations": "Limited context.",
    }
    payload[field] = value

    with pytest.raises(ValidationError, match="must not be blank"):
        EvidenceItem.model_validate(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [("independence", "unrelated"), ("verification_status", "unchecked")],
)
def test_invalid_evidence_enum_is_rejected(field: str, value: str) -> None:
    payload = {
        "evidence_id": "EV-001",
        "source_url": "https://example.test/original",
        "source_type": "forum",
        "accessed_at": "2026-10-15",
        "observation": "Observed friction.",
        "evidence_class": "firsthand",
        "independence": "independent",
        "independence_rationale": "Unknown.",
        "verification_status": "verified",
        "limitations": "Limited context.",
    }
    payload[field] = value

    with pytest.raises(ValidationError):
        EvidenceItem.model_validate(payload)
