"""The model-proposed evidence class is a closed vocabulary, not free text.

Regression for live run run-20261016T160833Z-f68aef61: the model wrote
"GitHub issue lead" / "issue_or_pull_request", so no evidence ever matched the
validator's exact "firsthand" rule and `corroborated` was unreachable.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from problem_discovery_agents.analysis_agent.models import SourceRequest
from problem_discovery_agents.analysis_agent.prompts import ANALYSIS_INSTRUCTIONS
from problem_discovery_agents.research_agent.models import CandidateSignal
from problem_discovery_agents.research_agent.prompts import SELECTION_INSTRUCTIONS

ALLOWED = ("firsthand", "documentation", "technical_verification")
FREE_TEXT = ("GitHub issue lead", "issue_or_pull_request")


def _candidate(evidence_class: str) -> CandidateSignal:
    return CandidateSignal(
        source_url="https://github.com/o/r/issues/1", user_segment="developers", workflow="CI",
        friction_hypothesis="Developers struggle to diagnose CI failures.", evidence_class=evidence_class,
    )


@pytest.mark.parametrize("value", ALLOWED)
def test_candidate_accepts_vocabulary(value: str) -> None:
    assert _candidate(value).evidence_class == value


@pytest.mark.parametrize("value", FREE_TEXT)
def test_candidate_rejects_free_text_class(value: str) -> None:
    with pytest.raises(ValidationError):
        _candidate(value)


@pytest.mark.parametrize("value", ALLOWED)
def test_source_request_accepts_vocabulary(value: str) -> None:
    assert SourceRequest(source_url="https://example.test/x", evidence_class=value).evidence_class == value


@pytest.mark.parametrize("value", FREE_TEXT)
def test_source_request_rejects_free_text_class(value: str) -> None:
    with pytest.raises(ValidationError):
        SourceRequest(source_url="https://example.test/x", evidence_class=value)


def test_validator_uses_the_shared_constant() -> None:
    from problem_discovery_agents.contracts import FIRSTHAND

    assert FIRSTHAND == "firsthand"


@pytest.mark.parametrize("prompt", (SELECTION_INSTRUCTIONS, ANALYSIS_INSTRUCTIONS))
def test_prompts_define_each_class(prompt: str) -> None:
    for value in ALLOWED:
        assert f"{value}:" in prompt


def test_analysis_prompt_states_the_corroborated_threshold() -> None:
    assert "at least two linked evidence items are independent and firsthand" in ANALYSIS_INSTRUCTIONS
    assert "needs_validation" in ANALYSIS_INSTRUCTIONS
