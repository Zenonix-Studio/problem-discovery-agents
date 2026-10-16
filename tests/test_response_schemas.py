"""Model-facing response schemas must be accepted by OpenAI strict structured output.

Regression for run-20261016T172923Z-2eed52c6: `Stage2ProposalBatch` used a dict with
`min_length`, which emits `minProperties`; OpenAI rejected it with HTTP 400. Fake agents in
other tests never exercise the real schema check, so this scans every response type offline.
"""

from __future__ import annotations

import pytest

from problem_discovery_agents.analysis_agent.models import AnalysisPlan
from problem_discovery_agents.evaluation_agent import Stage1ProposalBatch, Stage2ProposalBatch
from problem_discovery_agents.research_agent import CandidateSelection, PassPlan

RESPONSE_FORMATS = (PassPlan, CandidateSelection, AnalysisPlan, Stage1ProposalBatch, Stage2ProposalBatch)
REJECTED_KEYWORDS = ("minProperties", "maxProperties", "patternProperties", "propertyNames")


def _violations(node: object, path: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key in REJECTED_KEYWORDS:
                found.append(f"{key} at {path or '/'}")
            if key == "additionalProperties" and isinstance(value, dict):
                found.append(f"schema-valued additionalProperties at {path or '/'}")
            found.extend(_violations(value, f"{path}/{key}"))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found.extend(_violations(value, f"{path}[{index}]"))
    return found


@pytest.mark.parametrize("response_format", RESPONSE_FORMATS, ids=lambda model: model.__name__)
def test_response_schema_avoids_constructs_openai_rejects(response_format: type) -> None:
    assert _violations(response_format.model_json_schema()) == []
