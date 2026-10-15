from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from problem_discovery_agents.analysis_agent import (
    AnalysisAgent, AnalysisPlan, AlternativeProposal, CrewAIAnalysisPlanner,
    ProblemProposal, RetrievalIntent, SourceRequest, create_analysis_crew_agent,
)
from problem_discovery_agents.analysis_agent.prompts import ANALYSIS_INSTRUCTIONS
from problem_discovery_agents.contracts import (
    EvidenceItem, EvidenceRegistry, Finding, GapOutcome, Independence, ProblemStatus,
    ResearchCoverage, ResearchOutput, VerificationStatus,
)
from problem_discovery_agents.research_tools.models import RetrievalState, SearchLead, SearchResult, SourceRecord
from problem_discovery_agents.settings import Settings
from problem_discovery_agents.validation import ContractValidationError, validate_analysis_output

NOW = datetime(2026, 10, 15, tzinfo=UTC)


def _research() -> ResearchOutput:
    return ResearchOutput(
        findings=[
            Finding(finding_id="F-001", category="Developer Tools & Productivity", user_segment="backend developers", workflow="CI debugging", friction_hypothesis="Developers struggle to locate CI failures in long logs.", evidence_ids=["EV-001"]),
            Finding(finding_id="F-002", category="Developer Tools & Productivity", user_segment="backend developers", workflow="CI debugging", friction_hypothesis="Developers struggle to locate CI failures in long logs.", evidence_ids=["EV-002"]),
            Finding(finding_id="F-003", category="Developer Tools & Productivity", user_segment="backend developers", workflow="CI caching", friction_hypothesis="Developers struggle with slow dependency restores.", evidence_ids=["EV-003"]),
        ],
        evidence_registry=EvidenceRegistry(evidence=[
            EvidenceItem(evidence_id=f"EV-{i:03d}", source_url=f"https://example.test/{i}", source_type="forum", accessed_at=date(2026, 10, 15), observation="A firsthand report describes the workflow friction.", evidence_class="firsthand", independence=Independence.INDEPENDENT if i < 3 else Independence.UNCERTAIN, independence_rationale="Distinct author." if i < 3 else "Relationship unknown.", verification_status=VerificationStatus.VERIFIED, limitations="Small sample.")
            for i in range(1, 4)
        ]),
        research_coverage=ResearchCoverage(),
    )


class Planner:
    def plan(self, research: ResearchOutput) -> AnalysisPlan:
        assert [item.finding_id for item in research.findings] == ["F-001", "F-002", "F-003"]
        return AnalysisPlan(
            retrieval_intents=[RetrievalIntent(query="CI log viewer workaround current version", purpose="alternatives and current status")],
            problems=[
                ProblemProposal(finding_ids=["F-001", "F-002"], statement="Backend developers struggle to diagnose CI failures because long logs obscure the failing step, causing repeated manual investigation.", user_segment="backend developers", workflow="CI debugging", clustering_rationale="Both findings share the debugging task, log-obscuring mechanism, and manual-investigation consequence.", status_rationale="Two independent firsthand reports support the same friction, while current resolution remains uncertain.", evidence_ids=["EV-001", "EV-002"], independence_context="Two distinct authors are marked independent.", alternatives=[AlternativeProposal(name="CI log viewer", kind="existing tool", what_it_solves="Filters and searches CI logs.", gap_outcome="unknown_gap", source_urls=["https://example.test/alternative"])], counterevidence_intents=[RetrievalIntent(query="CI log viewer contrary current fix", purpose="counterevidence and resolution")], counterevidence_sources=[SourceRequest(source_url="https://example.test/contrary", evidence_class="firsthand")], current_resolution_uncertainty="No retrieved release or fix evidence establishes whether all contexts are resolved.", research_gaps=["Need current-version confirmation."], status="corroborated"),
                ProblemProposal(finding_ids=["F-003"], statement="Backend developers struggle to restore CI dependencies because ineffective caching causes slow builds.", user_segment="backend developers", workflow="CI caching", clustering_rationale="This remains separate: it shares the CI stack but has a caching mechanism and slow-build consequence.", status_rationale="Only one report is available and current scope is uncertain.", evidence_ids=["EV-003"], independence_context="One report has uncertain corroboration.", counterevidence_intents=[RetrievalIntent(query="CI caching contrary current fix", purpose="counterevidence and resolution")], current_resolution_uncertainty="No current-version fix evidence was retrieved.", research_gaps=["Need contrary configuration evidence."], status="needs_validation"),
            ],
        )

    def finalize(
        self, research: ResearchOutput, investigation: AnalysisPlan,
        inspected_sources: list[dict[str, object]],
    ) -> AnalysisPlan:
        assert research.findings
        assert {source["requested_url"] for source in inspected_sources} <= {
            "https://example.test/alternative", "https://example.test/contrary"
        }
        return investigation


class Tools:
    def search(self, query: str) -> SearchResult:
        return SearchResult(query=query, leads=[SearchLead(original_url="https://example.test/alternative", retrieved_at=NOW), SearchLead(original_url="https://example.test/contrary", retrieved_at=NOW)], retrieved_at=NOW, retrieval_state=RetrievalState.COMPLETE)

    def extract(self, urls: list[str]) -> list[SourceRecord]:
        return [SourceRecord(provider="tavily", request_kind="extract", requested_url=url, canonical_url=url, source_type="documentation" if url.endswith("alternative") else "forum", text="Retrieved source confirms only the bounded claim for this context.", author="another-dev", created_at=NOW, retrieved_at=NOW, retrieval_state=RetrievalState.COMPLETE) for url in urls]


def test_analysis_clusters_related_findings_and_preserves_distinct_friction() -> None:
    result = AnalysisAgent(planner=Planner(), tools=Tools()).run(_research())
    output = result.analysis_output
    assert [problem.problem_id for problem in output.problems] == ["P-001", "P-002"]
    assert output.problems[0].finding_ids == ["F-001", "F-002"]
    assert output.problems[1].finding_ids == ["F-003"]
    assert output.problems[0].alternatives[0].gap_outcome.value == "unknown_gap"
    assert output.problems[0].counterevidence_ids == ["EV-004"]
    assert [item.evidence_id for item in output.evidence_registry_delta.evidence] == ["EV-004", "EV-005"]
    assert set(result.evidence_registry.by_id()) == {"EV-001", "EV-002", "EV-003", "EV-004", "EV-005"}


def test_closed_metadata_does_not_make_a_problem_outdated() -> None:
    class ClosedTools(Tools):
        def extract(self, urls: list[str]) -> list[SourceRecord]:
            return [SourceRecord(provider="github", request_kind="issue", requested_url=url, source_type="issue", text="Closed as duplicate without a linked fix.", retrieved_at=NOW, retrieval_state=RetrievalState.COMPLETE, github_state="closed", limitations=["No linked release."]) for url in urls]

    result = AnalysisAgent(planner=Planner(), tools=ClosedTools()).run(_research())
    assert result.analysis_output.problems[0].status is ProblemStatus.CORROBORATED
    assert "release or fix evidence" in result.analysis_output.problems[0].current_resolution_uncertainty


def test_failed_counterevidence_search_remains_an_explicit_gap() -> None:
    class FailedTools(Tools):
        def search(self, query: str) -> SearchResult:
            return SearchResult(query=query, retrieved_at=NOW, retrieval_state=RetrievalState.FAILED, limitations=["Simulated unavailable current-version search."])

        def extract(self, urls: list[str]) -> list[SourceRecord]:
            raise AssertionError("failed discovery must not extract sources")

    result = AnalysisAgent(planner=Planner(), tools=FailedTools()).run(_research())
    first = result.analysis_output.problems[0]
    assert first.status is ProblemStatus.CORROBORATED
    assert first.counterevidence_ids == []
    assert any("Simulated unavailable current-version search." in gap for gap in first.research_gaps)


def test_analysis_validator_rejects_conflicts_and_blank_status_rationale() -> None:
    research = _research()
    result = AnalysisAgent(planner=Planner(), tools=Tools()).run(research)
    invalid = result.analysis_output.model_copy(deep=True)
    invalid.evidence_registry_delta = EvidenceRegistry(evidence=[research.evidence_registry.evidence[0]])
    with pytest.raises(ContractValidationError, match="conflicting Evidence IDs"):
        validate_analysis_output(research, invalid)
    with pytest.raises(ValidationError, match="must not be blank"):
        ProblemProposal(finding_ids=["F-001"], statement="Statement.", user_segment="developers", workflow="CI", clustering_rationale="Rationale.", status_rationale=" ", evidence_ids=["EV-001"], independence_context="Unknown.", counterevidence_intents=[RetrievalIntent(query="CI contrary", purpose="counterevidence")], current_resolution_uncertainty="Unknown.", status="needs_validation")


def test_finalization_cannot_claim_unsupported_status_or_alternative_gap() -> None:
    research = _research()
    result = AnalysisAgent(planner=Planner(), tools=Tools()).run(research)
    invalid = result.analysis_output.model_copy(deep=True)
    invalid.problems[0].evidence_ids = ["EV-001"]
    with pytest.raises(ContractValidationError, match="lacks two linked independent firsthand"):
        validate_analysis_output(research, invalid)
    invalid = result.analysis_output.model_copy(deep=True)
    invalid.problems[0].alternatives[0].gap_outcome = GapOutcome.SUPPORTED_GAP
    invalid.problems[0].alternatives[0].evidence_ids = []
    with pytest.raises(ContractValidationError, match="supported_gap without linked Evidence IDs"):
        validate_analysis_output(research, invalid)


@pytest.mark.parametrize(
    ("source_text", "expected_status"),
    [
        ("Fixed in release 3.2; users confirm the earlier failure no longer occurs.", ProblemStatus.OUTDATED),
        ("The documented built-in capability handles this workflow successfully.", ProblemStatus.CONTRADICTED),
    ],
)
def test_final_classification_uses_inspected_source_content(
    source_text: str, expected_status: ProblemStatus,
) -> None:
    class FinalizingPlanner(Planner):
        def finalize(
            self, research: ResearchOutput, investigation: AnalysisPlan,
            inspected_sources: list[dict[str, object]],
        ) -> AnalysisPlan:
            assert all(source_text in str(source["text"]) for source in inspected_sources)
            final = investigation.model_copy(deep=True)
            final.problems[0].status = expected_status
            final.problems[0].status_rationale = "Inspected current source provides linked contrary or resolution evidence."
            return final

    class SourceTools(Tools):
        def extract(self, urls: list[str]) -> list[SourceRecord]:
            return [SourceRecord(provider="tavily", request_kind="extract", requested_url=url, source_type="documentation", text=source_text, retrieved_at=NOW, retrieval_state=RetrievalState.COMPLETE) for url in urls]

    result = AnalysisAgent(planner=FinalizingPlanner(), tools=SourceTools()).run(_research())
    assert result.analysis_output.problems[0].status is expected_status
    assert result.analysis_output.problems[0].counterevidence_ids


def test_prompt_and_crew_boundary_keep_scope_guards() -> None:
    lowered = ANALYSIS_INSTRUCTIONS.lower()
    for required in ("product", "score", "validated demand", "invent", "closed", "rerun"):
        assert required in lowered
    received: dict[str, object] = {}
    agent = create_analysis_crew_agent(
        Settings(PDA_GITHUB_TOKEN="github", PDA_TAVILY_API_KEY="tavily", PDA_LLM_API_KEY="llm"),
        llm_factory=lambda **kwargs: received.setdefault("llm", kwargs),
        agent_factory=lambda **kwargs: kwargs,
    )
    assert agent["allow_delegation"] is False
    assert received["llm"] == {"model": "openai/gpt-5.4-mini", "api_key": "llm", "reasoning_effort": "medium"}


def test_crewai_planner_parses_structured_response() -> None:
    class Output:
        pydantic = AnalysisPlan()
    class Agent:
        calls = 0
        def kickoff(self, instructions: str, *, response_format: object) -> Output:
            self.calls += 1
            assert response_format is AnalysisPlan
            assert "Research handoff" in instructions
            if self.calls == 2:
                assert "Inspected source records" in instructions
            return Output()
    agent = Agent()
    planner = CrewAIAnalysisPlanner(agent)
    research = _research()
    plan = planner.plan(research)
    assert plan == AnalysisPlan()
    assert planner.finalize(research, plan, []) == AnalysisPlan()
