from __future__ import annotations

from datetime import date

import pytest

from problem_discovery_agents.contracts import (
    EvidenceItem,
    EvidenceRegistry,
    Independence,
    VerificationStatus,
)


def evidence(evidence_id: str = "EV-001") -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        source_url="https://example.test/source",
        source_type="forum post",
        published_at=None,
        accessed_at=date(2026, 10, 15),
        source_excerpt=None,
        observation="A developer describes a repeated workflow failure.",
        interpretation=None,
        evidence_class="firsthand",
        independence=Independence.INDEPENDENT,
        independence_rationale="A distinct author describes their own experience.",
        verification_status=VerificationStatus.VERIFIED,
        limitations="One report does not establish recurrence.",
    )


def test_registry_merge_is_atomic_and_does_not_overwrite() -> None:
    original = EvidenceRegistry(evidence=[evidence("EV-001")])
    merged = original.merge(EvidenceRegistry(evidence=[evidence("EV-002")]))

    assert [item.evidence_id for item in original.evidence] == ["EV-001"]
    assert [item.evidence_id for item in merged.evidence] == ["EV-001", "EV-002"]

    with pytest.raises(ValueError, match="conflicting Evidence IDs: EV-001"):
        original.merge(EvidenceRegistry(evidence=[evidence("EV-001")]))

    assert [item.evidence_id for item in original.evidence] == ["EV-001"]


def test_registry_rejects_duplicate_input_ids() -> None:
    with pytest.raises(ValueError, match="duplicate Evidence IDs: EV-001"):
        EvidenceRegistry(evidence=[evidence(), evidence()])
