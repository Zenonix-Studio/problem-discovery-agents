from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from problem_discovery_agents.contracts import (
    AnalysisOutput, EvidenceItem, EvidenceRegistry, Finding, Independence, Problem,
    ProblemStatus, ResearchCoverage, ResearchOutput, ScoreAssessment, Stage1Scores,
    VerificationStatus,
)
from problem_discovery_agents.evaluation_agent import (
    CrewAIEvaluationPlanner, EvaluationAgent, Stage1Proposal, Stage1ProposalBatch,
    Stage2Proposal, Stage2ProposalBatch, create_evaluation_crew_agent,
)
from problem_discovery_agents.evaluation_agent.prompts import (
    REPORT_INSTRUCTIONS, STAGE1_INSTRUCTIONS, STAGE2_INSTRUCTIONS,
)
from problem_discovery_agents.validation import ContractValidationError
from problem_discovery_agents.settings import Settings


def _chain(problem_count: int = 1, *, status: ProblemStatus = ProblemStatus.NEEDS_VALIDATION):
    evidence = [
        EvidenceItem(
            evidence_id=f"EV-{index:03d}", source_url=f"https://example.test/source-{index}",
            source_type="forum", accessed_at=date(2026, 10, 15),
            observation="A bounded developer workflow observation.", evidence_class="firsthand",
            independence=Independence.INDEPENDENT, independence_rationale="Separate author.",
            verification_status=VerificationStatus.VERIFIED, limitations="Small sample.",
        )
        for index in range(1, problem_count + 1)
    ]
    research = ResearchOutput(
        findings=[
            Finding(
                finding_id=f"F-{index:03d}", category="Developer Tools & Productivity",
                user_segment="developers", workflow="CI debugging",
                friction_hypothesis="Developers encounter a workflow friction.",
                evidence_ids=[f"EV-{index:03d}"],
            ) for index in range(1, problem_count + 1)
        ], evidence_registry=EvidenceRegistry(evidence=evidence), research_coverage=ResearchCoverage(
            examined_workflows=["CI debugging"], limitations=["Small mocked coverage."],
        ),
    )
    problems = [
        Problem(
            problem_id=f"P-{index:03d}", finding_ids=[f"F-{index:03d}"],
            statement="Developers struggle to diagnose CI failures, causing repeated delay.",
            user_segment="developers", workflow="CI debugging", clustering_rationale="One bounded finding.",
            status_rationale="Evidence remains limited.", evidence_ids=[f"EV-{index:03d}"],
            independence_context="One independent report.",
            counterevidence_ids=[f"EV-{index:03d}"] if status in {ProblemStatus.OUTDATED, ProblemStatus.CONTRADICTED} else [],
            current_resolution_uncertainty="Current status is uncertain.", status=status,
        ) for index in range(1, problem_count + 1)
    ]
    return research, AnalysisOutput(problems=problems), research.evidence_registry


def _scores(values: tuple[int | None, int | None, int | None, int | None]) -> Stage1Scores:
    def assessment(value: int | None) -> ScoreAssessment:
        kwargs = {"score": value, "rationale": "Evidence supports this bounded anchor assessment.", "evidence_ids": ["EV-001"]}
        if value is None:
            kwargs.update({"evidence_gap": "Evidence does not support a defensible anchor.", "next_validation_action": "Collect direct firsthand evidence."})
        return ScoreAssessment(**kwargs)
    return Stage1Scores(
        problem_reality=assessment(values[0]), frequency_recurrence=assessment(values[1]),
        alternative_gap=assessment(values[2]), meaningful_benefit=assessment(values[3]),
    )


class Planner:
    def __init__(self, proposals: list[Stage1Proposal], *, stage2: list[Stage2Proposal] | None = None) -> None:
        self.proposals = proposals
        self.stage2 = stage2
        self.stage2_calls = 0
        self.stage2_input_problem_ids: list[str] = []

    def propose_stage1(self, research, analysis, registry):
        assert registry == research.evidence_registry
        return Stage1ProposalBatch(proposals=self.proposals)

    def propose_stage2(self, evaluation, team_context):
        self.stage2_calls += 1
        assert "Team strengths" in team_context
        self.stage2_input_problem_ids = [record.problem_id for record in evaluation.evaluations]
        proposals = self.stage2
        if proposals is None:
            proposals = [
                Stage2Proposal(
                    problem_id=record.problem_id,
                    assessments=[{"dimension": "feasibility", "value": "Unknown", "rationale": "No further fit evidence supplied."}],
                )
                for record in evaluation.evaluations
                if record.stage1_status.value in {"Strong", "Promising"} and record.user_benefit
            ]
        return Stage2ProposalBatch(proposals=proposals)

    def write_report(self, report_context):
        problem_ids = [item["problem_id"] for item in report_context["evaluations"]["evaluations"]]
        evidence = report_context["evidence_registry"]["evidence"]
        return "\n".join([
            "## Executive summary", "Coverage limits retained.", "## Examined landscape",
            "Developer Tools & Productivity workflow coverage.", "## Comparison",
            "Deterministic Stage 1 results only.", "## Shortlisted problem cards", *problem_ids,
            "Problem Reality; Frequency / Recurrence; Alternative Gap; Meaningful Benefit.",
            "Alternatives and workarounds; Counterevidence and uncertainty.",
            "Potential measurable outcome; Stage 2: conditional; Next validation step.",
            "## Rejected and inconclusive observations", "Outdated, contradicted, Low priority, and Research needed records remain visible.",
            "## Source appendix", *(f"{item['evidence_id']}: {item['source_url']}" for item in evidence),
            "## Validation questions", "What direct evidence would resolve remaining gaps?",
        ])


@pytest.mark.parametrize(
    ("values", "total", "status"),
    [((0, 0, 0, 0), 0, "Low priority"), ((3, 3, 0, 0), 6, "Low priority"),
     ((2, 2, 2, 1), 7, "Promising"), ((3, 2, 2, 2), 9, "Promising"),
     ((3, 3, 2, 2), 10, "Strong"), ((3, 3, 3, 3), 12, "Strong")],
)
def test_stage1_totals_and_labels_are_deterministic(values, total, status) -> None:
    research, analysis, registry = _chain()
    planner = Planner([Stage1Proposal(problem_id="P-001", stage1_scores=_scores(values), user_benefit="Fewer repeated debugging steps.")])
    result = EvaluationAgent(planner=planner).run(research, analysis, registry)
    record = result.evaluation_output.evaluations[0]
    assert (record.stage1_total, record.stage1_status.value) == (total, status)
    assert planner.stage2_calls == (1 if status in {"Strong", "Promising"} else 0)


def test_partial_scoring_has_no_total_and_no_stage2() -> None:
    research, analysis, registry = _chain()
    planner = Planner([Stage1Proposal(problem_id="P-001", stage1_scores=_scores((3, 2, None, 3)), user_benefit="Clear but incomplete benefit.")])
    result = EvaluationAgent(planner=planner).run(research, analysis, registry)
    record = result.evaluation_output.evaluations[0]
    assert record.stage1_total is None
    assert record.stage1_status.value == "Research needed"
    assert record.stage2_assessment is None
    assert planner.stage2_calls == 0
    assert "Research needed" in result.report_markdown


@pytest.mark.parametrize(
    "proposals, expected",
    [([], "missing Evaluation proposals"),
     ([Stage1Proposal(problem_id="P-001", stage1_scores=_scores((1, 1, 1, 1))), Stage1Proposal(problem_id="P-001", stage1_scores=_scores((1, 1, 1, 1)))], "duplicate Evaluation proposal"),
     ([Stage1Proposal(problem_id="P-999", stage1_scores=_scores((1, 1, 1, 1)))], "unknown Problem")],
)
def test_every_analyzed_problem_must_have_exactly_one_evaluation(proposals, expected) -> None:
    research, analysis, registry = _chain(2)
    with pytest.raises(ContractValidationError, match=expected):
        EvaluationAgent(planner=Planner(proposals)).run(research, analysis, registry)


def test_stage2_is_only_attached_for_eligible_records() -> None:
    research, analysis, registry = _chain()
    stage1 = Stage1Proposal(problem_id="P-001", stage1_scores=_scores((3, 3, 2, 2)), user_benefit="Fewer repeated debugging steps.")
    planner = Planner([stage1], stage2=[Stage2Proposal(problem_id="P-001", assessments=[{"dimension": "feasibility", "value": "Partial", "rationale": "Needs a small maintenance validation."}])])
    result = EvaluationAgent(planner=planner).run(research, analysis, registry)
    assert result.evaluation_output.evaluations[0].stage2_assessment is not None
    assert planner.stage2_input_problem_ids == ["P-001"]

    low = Planner([Stage1Proposal(problem_id="P-001", stage1_scores=_scores((1, 1, 1, 1)), user_benefit="Some benefit.")], stage2=[Stage2Proposal(problem_id="P-001", assessments=[{"dimension": "fit", "value": "Strong", "rationale": "Should not be requested."}])])
    EvaluationAgent(planner=low).run(research, analysis, registry)
    assert low.stage2_calls == 0


def test_stage2_prompt_receives_only_deterministically_eligible_records() -> None:
    research, analysis, registry = _chain(2)
    planner = Planner([
        Stage1Proposal(problem_id="P-001", stage1_scores=_scores((3, 3, 2, 2)), user_benefit="Clear benefit."),
        Stage1Proposal(problem_id="P-002", stage1_scores=_scores((1, 1, 1, 1)), user_benefit="Limited benefit."),
    ])
    result = EvaluationAgent(planner=planner).run(research, analysis, registry)
    assert planner.stage2_input_problem_ids == ["P-001"]
    assert result.evaluation_output.evaluations[1].stage2_assessment is None


def test_registry_mismatch_and_invalid_report_citations_fail() -> None:
    research, analysis, registry = _chain()
    proposal = Stage1Proposal(problem_id="P-001", stage1_scores=_scores((1, 1, 1, 1)))
    with pytest.raises(ContractValidationError, match="exact merged authoritative"):
        EvaluationAgent(planner=Planner([proposal])).run(research, analysis, EvidenceRegistry())

    class BadReportPlanner(Planner):
        def write_report(self, report_context):
            return super().write_report(report_context).replace("EV-001", "EV-999")
    with pytest.raises(ValueError, match="unknown Evidence IDs"):
        EvaluationAgent(planner=BadReportPlanner([proposal])).run(research, analysis, registry)


def test_report_requires_problem_card_content_beyond_headings() -> None:
    research, analysis, registry = _chain()
    proposal = Stage1Proposal(problem_id="P-001", stage1_scores=_scores((1, 1, 1, 1)))

    class SparseReportPlanner(Planner):
        def write_report(self, report_context):
            return "\n".join([
                "## Executive summary", "## Examined landscape", "## Comparison",
                "## Shortlisted problem cards", "P-001", "## Rejected and inconclusive observations",
                "## Source appendix", "EV-001: https://example.test/source-1", "## Validation questions",
            ])
    with pytest.raises(ValueError, match="missing required report content"):
        EvaluationAgent(planner=SparseReportPlanner([proposal])).run(research, analysis, registry)


def test_outdated_and_contradicted_records_are_passed_to_report_context() -> None:
    research, analysis, registry = _chain(status=ProblemStatus.OUTDATED)
    planner = Planner([Stage1Proposal(problem_id="P-001", stage1_scores=_scores((0, 0, 0, 0)))])
    result = EvaluationAgent(planner=planner).run(research, analysis, registry)
    assert "Outdated" in result.report_markdown
    assert result.evaluation_output.evaluations[0].stage1_status.value == "Low priority"


def test_proposals_forbid_derived_or_fifth_score_fields_and_prompts_keep_guards() -> None:
    with pytest.raises(ValidationError):
        Stage1Proposal.model_validate({"problem_id": "P-001", "stage1_scores": _scores((1, 1, 1, 1)), "stage1_total": 4})
    for text in (STAGE1_INSTRUCTIONS, STAGE2_INSTRUCTIONS, REPORT_INSTRUCTIONS):
        assert "product" in text.lower()
    assert "technical verification" in STAGE1_INSTRUCTIONS.lower()
    assert "measurable outcome" in STAGE1_INSTRUCTIONS.lower()
    assert "source appendix must state" in REPORT_INSTRUCTIONS.lower()


def test_crewai_boundary_uses_one_agent_and_structured_formats() -> None:
    class Output:
        def __init__(self, value): self.pydantic = value
    class Agent:
        def __init__(self): self.calls = []
        def kickoff(self, instructions, **kwargs):
            self.calls.append((instructions, kwargs))
            response_format = kwargs.get("response_format")
            if response_format is not None:
                return Output(response_format(proposals=[]))
            return type("Report", (), {"raw": "report"})()
    agent = Agent()
    planner = CrewAIEvaluationPlanner(agent)
    research, analysis, registry = _chain()
    assert planner.propose_stage1(research, analysis, registry).proposals == []
    assert planner.propose_stage2(type("Evaluation", (), {"model_dump": lambda self, **_: {}})(), "team").proposals == []
    assert planner.write_report({}) == "report"
    assert len(agent.calls) == 3

    received = {}
    created = create_evaluation_crew_agent(
        Settings(PDA_GITHUB_TOKEN="github", PDA_TAVILY_API_KEY="tavily", PDA_LLM_API_KEY="llm"),
        llm_factory=lambda **kwargs: received.setdefault("llm", kwargs), agent_factory=lambda **kwargs: kwargs,
    )
    assert created["allow_delegation"] is False
    assert received["llm"]["model"] == "openai/gpt-5.4-mini"


# --- Report Stage 1 labels: regression for run-20261016T163719Z-e8b53313 ---------------
# The real model mirrored the snake_case keys it was shown (problem_reality: ...), so the
# validator never found "Problem Reality". These tests exercise the context the model sees.

STAGE1_DISPLAY_LABELS = ("Problem Reality", "Frequency / Recurrence", "Alternative Gap", "Meaningful Benefit")
STAGE1_FIELD_NAMES = ("problem_reality", "frequency_recurrence", "alternative_gap", "meaningful_benefit")


def _evaluated():
    research, analysis, registry = _chain()
    proposal = Stage1Proposal(problem_id="P-001", stage1_scores=_scores((2, 2, 2, 1)))
    result = EvaluationAgent(planner=Planner([proposal])).run(research, analysis, registry)
    return research, analysis, registry, result


def test_report_context_presents_stage1_scores_with_display_labels() -> None:
    from problem_discovery_agents.evaluation_agent.report import build_report_context

    research, analysis, registry, result = _evaluated()
    context = build_report_context(research, analysis, result.evaluation_output, registry)
    scores = context["evaluations"]["evaluations"][0]["stage1_scores"]
    assert tuple(scores) == STAGE1_DISPLAY_LABELS
    assert not set(STAGE1_FIELD_NAMES) & set(scores)
    assert scores["Problem Reality"]["score"] == 2 and scores["Meaningful Benefit"]["score"] == 1


def test_building_report_context_does_not_change_the_evaluation_contract() -> None:
    from problem_discovery_agents.evaluation_agent.report import build_report_context

    research, analysis, registry, result = _evaluated()
    build_report_context(research, analysis, result.evaluation_output, registry)
    dumped = result.evaluation_output.model_dump(mode="json")["evaluations"][0]["stage1_scores"]
    assert tuple(dumped) == STAGE1_FIELD_NAMES


def test_report_instructions_name_the_four_stage1_labels() -> None:
    for label in STAGE1_DISPLAY_LABELS:
        assert label in REPORT_INSTRUCTIONS


def test_report_written_from_the_received_context_passes_validation() -> None:
    research, analysis, registry = _chain()
    proposal = Stage1Proposal(problem_id="P-001", stage1_scores=_scores((2, 2, 2, 1)))

    class ContextMirroringPlanner(Planner):
        """Mirrors the keys of the context it receives, like the real model did."""

        def write_report(self, report_context):
            cards = [
                f"{label}: {assessment['score']}"
                for record in report_context["evaluations"]["evaluations"]
                for label, assessment in record["stage1_scores"].items()
            ]
            evidence = report_context["evidence_registry"]["evidence"]
            return "\n".join([
                "## Executive summary", "## Examined landscape", "## Comparison",
                "## Shortlisted problem cards", "P-001", *cards,
                "Alternatives; Counterevidence; Potential measurable outcome; Stage 2; Next validation.",
                "## Rejected and inconclusive observations", "## Source appendix",
                *(f"{item['evidence_id']}: {item['source_url']}" for item in evidence),
                "## Validation questions",
            ])

    result = EvaluationAgent(planner=ContextMirroringPlanner([proposal])).run(research, analysis, registry)
    assert all(label in result.report_markdown for label in STAGE1_DISPLAY_LABELS)


def test_report_using_only_field_names_is_still_rejected() -> None:
    from problem_discovery_agents.evaluation_agent.report import validate_report_markdown

    _, _, registry, result = _evaluated()
    report = "\n".join([
        "## Executive summary", "## Examined landscape", "## Comparison",
        "## Shortlisted problem cards", "P-001", *(f"{name}: Partial" for name in STAGE1_FIELD_NAMES),
        "Alternatives; Counterevidence; Potential measurable outcome; Stage 2; Next validation.",
        "## Rejected and inconclusive observations", "## Source appendix", "EV-001: https://example.test/source-1",
        "## Validation questions",
    ])
    with pytest.raises(ValueError, match="missing required report content: Problem Reality"):
        validate_report_markdown(report, result.evaluation_output, registry)


# --- Stage 2 proposal list shape: regression for run-20261016T172923Z-2eed52c6 ----------


def _stage2_item(dimension: str, value: str = "Partial") -> dict:
    return {"dimension": dimension, "value": value, "rationale": f"Rationale for {dimension}."}


def _eligible_run(items: list[dict]):
    from problem_discovery_agents.evaluation_agent import Stage2Proposal

    research, analysis, registry = _chain()
    stage1 = Stage1Proposal(problem_id="P-001", stage1_scores=_scores((3, 3, 2, 2)), user_benefit="Fewer repeated debugging steps.")
    planner = Planner([stage1], stage2=[Stage2Proposal(problem_id="P-001", assessments=items)])
    return EvaluationAgent(planner=planner).run(research, analysis, registry)


def test_stage2_items_become_the_existing_assessment_mapping() -> None:
    result = _eligible_run([_stage2_item("capability", "Strong"), _stage2_item("maintainability")])
    assessments = result.evaluation_output.evaluations[0].stage2_assessment.assessments
    assert list(assessments) == ["capability", "maintainability"]
    assert assessments["capability"].value.value == "Strong"
    assert assessments["maintainability"].rationale == "Rationale for maintainability."


@pytest.mark.parametrize(
    ("items", "message"),
    [
        ([], "no assessments"),
        ([_stage2_item("capability"), _stage2_item("Capability")], "duplicate"),
    ],
)
def test_stage2_proposal_shape_errors_fail_fast(items: list[dict], message: str) -> None:
    with pytest.raises(ContractValidationError, match=message):
        _eligible_run(items)


def test_stage2_item_rejects_blank_dimension() -> None:
    from problem_discovery_agents.evaluation_agent import Stage2Proposal

    with pytest.raises(ValidationError, match="must not be blank"):
        Stage2Proposal(problem_id="P-001", assessments=[_stage2_item("  ")])


def test_stage2_instructions_describe_the_item_shape() -> None:
    assert "dimension, value and rationale" in STAGE2_INSTRUCTIONS
