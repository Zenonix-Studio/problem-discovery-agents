from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from problem_discovery_agents.contracts import Independence, VerificationStatus
from problem_discovery_agents.research_agent import (
    CandidateSignal,
    CrewAIResearchPlanner,
    InspectedSignal,
    M3ResearchTools,
    PassPlan,
    Query,
    ResearchAgent,
    ResearchRequest,
    create_research_crew_agent,
)
from problem_discovery_agents.research_agent.prompts import PASS_ONE_INSTRUCTIONS, PASS_TWO_INSTRUCTIONS
from problem_discovery_agents.research_tools.models import (
    RetrievalState,
    SearchLead,
    SearchResult,
    SourceRecord,
)
from problem_discovery_agents.settings import Settings


NOW = datetime(2026, 10, 15, tzinfo=UTC)


class FakePlanner:
    def plan_pass_one(self, request: ResearchRequest) -> PassPlan:
        return PassPlan(
            workflows=["CI troubleshooting", "dependency updates"],
            queries=[Query(query="site:github.com CI debugging manual logs", purpose="broad friction discovery")],
            candidates=[
                CandidateSignal(source_url="https://example.test/a", user_segment="backend developers", workflow="CI troubleshooting", friction_hypothesis="Developers struggle to locate the cause of CI failures in long logs.", observation="A developer describes manually tracing a failure through CI logs."),
                CandidateSignal(source_url="https://example.test/inaccessible", user_segment="backend developers", workflow="CI troubleshooting", friction_hypothesis="Developers cannot inspect a referenced CI failure report.", observation="A search lead identifies a report but its original content could not be retrieved."),
            ],
        )

    def plan_pass_two(self, request: ResearchRequest, pass_one_candidates: list[InspectedSignal]) -> PassPlan:
        assert [candidate.source_url for candidate in pass_one_candidates] == [
            "https://example.test/a"
        ]
        assert pass_one_candidates[0].source_excerpt == "Firsthand source text for https://example.test/a."
        assert pass_one_candidates[0].author == "alex"
        return PassPlan(
            workflows=["CI troubleshooting"],
            queries=[Query(query="CI debugging repeated manual logs firsthand", purpose="deepen independent evidence")],
            candidates=[
                CandidateSignal(source_url="https://example.test/b", user_segment="backend developers", workflow="CI troubleshooting", friction_hypothesis="Developers struggle to locate the cause of CI failures in long logs.", observation="A separate developer reports repeatedly reading long CI logs to identify the failure."),
                CandidateSignal(source_url="https://example.test/c", user_segment="backend developers", workflow="CI troubleshooting", friction_hypothesis="Developers struggle to locate the cause of CI failures in long logs.", observation="A same-author cross-post describes the same CI log investigation."),
            ],
        )


class FakeTools:
    def search(self, query: str) -> SearchResult:
        if query.startswith("site:github"):
            urls = ["https://example.test/a", "https://example.test/inaccessible"]
            return SearchResult(query=query, leads=[SearchLead(original_url=url, retrieved_at=NOW) for url in urls], retrieved_at=NOW, retrieval_state=RetrievalState.COMPLETE)
        return SearchResult(query=query, leads=[SearchLead(original_url=url, retrieved_at=NOW) for url in ["https://example.test/b", "https://example.test/c"]], retrieved_at=NOW, retrieval_state=RetrievalState.COMPLETE)

    def extract(self, urls: list[str]) -> list[SourceRecord]:
        authors = {"https://example.test/a": "alex", "https://example.test/b": "bea", "https://example.test/c": "alex"}
        records: list[SourceRecord] = []
        for url in urls:
            if url.endswith("inaccessible"):
                records.append(SourceRecord(provider="tavily", request_kind="extract", requested_url=url, canonical_url=url, source_type="forum", retrieved_at=NOW, retrieval_state=RetrievalState.INACCESSIBLE, limitations=["Original page was unavailable."]))
            else:
                records.append(SourceRecord(provider="tavily", request_kind="extract", requested_url=url, canonical_url=url, source_type="forum", text=f"Firsthand source text for {url}.", author=authors[url], created_at=NOW, retrieved_at=NOW, retrieval_state=RetrievalState.COMPLETE))
        return records


def test_two_pass_research_preserves_provenance_and_independence() -> None:
    result = ResearchAgent(planner=FakePlanner(), tools=FakeTools()).run(
        ResearchRequest(category="Developer Tools & Productivity")
    )

    output = result.research_output
    assert [finding.finding_id for finding in output.findings] == ["F-001", "F-002", "F-003"]
    assert [item.evidence_id for item in output.evidence_registry.evidence] == ["EV-001", "EV-002", "EV-003", "EV-004"]
    assert output.evidence_registry.evidence[1].verification_status is VerificationStatus.UNVERIFIED
    assert output.evidence_registry.evidence[1].source_excerpt is None
    assert output.evidence_registry.evidence[1].evidence_class == "unverified_source_lead"
    assert all("EV-002" not in finding.evidence_ids for finding in output.findings)
    assert output.evidence_registry.evidence[0].observation == "Firsthand source text for https://example.test/a."
    assert output.evidence_registry.evidence[2].independence is Independence.INDEPENDENT
    assert output.evidence_registry.evidence[3].independence is Independence.DEPENDENT
    assert output.research_coverage.unexamined_workflows


def test_empty_search_is_valid_and_visible_as_a_gap() -> None:
    class EmptyPlanner:
        def plan_pass_one(self, request: ResearchRequest) -> PassPlan:
            return PassPlan(workflows=["CI"], queries=[Query(query="empty", purpose="broad")])

        def plan_pass_two(self, request: ResearchRequest, pass_one_candidates: list[InspectedSignal]) -> PassPlan:
            return PassPlan(queries=[Query(query="empty again", purpose="deepen")])

    class EmptyTools:
        def search(self, query: str) -> SearchResult:
            state = RetrievalState.FAILED if query == "empty" else RetrievalState.COMPLETE
            return SearchResult(query=query, retrieved_at=NOW, retrieval_state=state, limitations=["Simulated failed search."] if state is RetrievalState.FAILED else [])

        def extract(self, urls: list[str]) -> list[SourceRecord]:
            raise AssertionError("empty discovery must not retrieve")

    output = ResearchAgent(planner=EmptyPlanner(), tools=EmptyTools()).run(
        ResearchRequest(category="Developer Tools & Productivity", workflow_focus="CI")
    ).research_output
    assert output.findings == []
    assert len(output.research_coverage.unsuccessful_searches) == 2
    assert "Simulated failed search." in output.research_coverage.unsuccessful_searches[0]
    assert output.research_coverage.research_gaps


def test_scope_and_solution_language_are_rejected() -> None:
    with pytest.raises(ValidationError, match="only supports the pilot category"):
        ResearchRequest(category="Mobile SDKs & AI Tooling")
    with pytest.raises(ValidationError, match="solution-neutral"):
        CandidateSignal(source_url="https://example.test/source", user_segment="developers", workflow="CI", friction_hypothesis="The solution is a product.", observation="A bounded observation.")


def test_research_prompts_keep_required_scope_guards_visible() -> None:
    combined = f"{PASS_ONE_INSTRUCTIONS}\n{PASS_TWO_INSTRUCTIONS}".lower()
    for required in ("search snippets are leads", "solution", "score", "validated", "invent", "resolved"):
        assert required in combined


def test_m3_bridge_prefers_github_for_github_object_urls() -> None:
    class Tavily:
        def search(self, query: str) -> SearchResult:
            raise AssertionError("not used by this test")

        def extract(self, urls: list[str]) -> list[SourceRecord]:
            return [SourceRecord(provider="tavily", request_kind="extract", requested_url=url, retrieved_at=NOW, retrieval_state=RetrievalState.INACCESSIBLE, limitations=["No content."]) for url in urls]

    class GitHubRest:
        def get_issue_or_pull_request(self, owner: str, repository: str, number: int) -> SourceRecord:
            assert (owner, repository, number) == ("owner", "repo", 7)
            return SourceRecord(provider="github", request_kind="issue", requested_url="https://api.github.test/issue/7", canonical_url="https://github.com/owner/repo/issues/7", source_type="issue", text="Reported friction.", author="dev", retrieved_at=NOW, retrieval_state=RetrievalState.COMPLETE)

    tools = M3ResearchTools(tavily=Tavily(), github_rest=GitHubRest())  # type: ignore[arg-type]
    records = tools.extract(["https://github.com/owner/repo/issues/7", "https://example.test/page"])

    assert records[0].requested_url == "https://github.com/owner/repo/issues/7"
    assert records[0].provider == "github"
    assert records[1].provider == "tavily"


def test_crew_factory_uses_the_shared_model_boundary() -> None:
    received: dict[str, object] = {}

    def llm_factory(**kwargs: object) -> object:
        received["llm"] = kwargs
        return "fake-llm"

    def agent_factory(**kwargs: object) -> object:
        received["agent"] = kwargs
        return kwargs

    agent = create_research_crew_agent(
        Settings(
            PDA_GITHUB_TOKEN="github-test-secret",
            PDA_TAVILY_API_KEY="tavily-test-secret",
            PDA_LLM_API_KEY="llm-test-secret",
        ),
        llm_factory=llm_factory,
        agent_factory=agent_factory,
    )

    assert received["llm"] == {
        "model": "openai/gpt-5.4-mini",
        "api_key": "llm-test-secret",
        "reasoning_effort": "medium",
    }
    assert agent["allow_delegation"] is False  # type: ignore[index]
    assert agent["llm"] == "fake-llm"  # type: ignore[index]


def test_crewai_planner_requests_validated_plans_for_both_passes() -> None:
    class Output:
        def __init__(self, plan: PassPlan) -> None:
            self.pydantic = plan

    class Agent:
        def __init__(self) -> None:
            self.calls: list[tuple[str, object]] = []

        def kickoff(self, instructions: str, *, response_format: object) -> Output:
            self.calls.append((instructions, response_format))
            return Output(PassPlan(workflows=["CI"], queries=[Query(query="CI manual logs", purpose="test")]))

    agent = Agent()
    planner = CrewAIResearchPlanner(agent)
    request = ResearchRequest(category="Developer Tools & Productivity")

    assert planner.plan_pass_one(request).workflows == ["CI"]
    signal = InspectedSignal(source_url="https://example.test/a", user_segment="developers", workflow="CI", friction_hypothesis="Developers struggle to inspect CI logs.", source_excerpt="A retrieved source excerpt.", source_type="forum", author="dev")
    assert planner.plan_pass_two(request, [signal]).queries[0].query == "CI manual logs"
    assert len(agent.calls) == 2
    assert all(response_format is PassPlan for _, response_format in agent.calls)
    assert "Inspected, researchable Pass 1 signals" in agent.calls[1][0]
    assert "A retrieved source excerpt." in agent.calls[1][0]


def test_model_proposed_observation_never_overrides_retrieved_source_text() -> None:
    class Planner:
        def plan_pass_one(self, request: ResearchRequest) -> PassPlan:
            return PassPlan(
                workflows=["CI"],
                queries=[Query(query="CI", purpose="broad")],
                candidates=[CandidateSignal(source_url="https://example.test/source", user_segment="developers", workflow="CI", friction_hypothesis="Developers struggle to inspect CI logs.", observation="Unsupported search-snippet claim.", interpretation="Unsupported inferred cause.")],
            )

        def plan_pass_two(self, request: ResearchRequest, pass_one_candidates: list[InspectedSignal]) -> PassPlan:
            assert pass_one_candidates[0].source_excerpt == "Original content says logs were manually inspected."
            return PassPlan()

    class Tools:
        def search(self, query: str) -> SearchResult:
            return SearchResult(query=query, leads=[SearchLead(original_url="https://example.test/source", snippet="Unsupported search-snippet claim.", retrieved_at=NOW)], retrieved_at=NOW, retrieval_state=RetrievalState.COMPLETE)

        def extract(self, urls: list[str]) -> list[SourceRecord]:
            return [SourceRecord(provider="tavily", request_kind="extract", requested_url=urls[0], source_type="forum", text="Original content says logs were manually inspected.", author="dev", retrieved_at=NOW, retrieval_state=RetrievalState.COMPLETE)]

    output = ResearchAgent(planner=Planner(), tools=Tools()).run(
        ResearchRequest(category="Developer Tools & Productivity")
    ).research_output
    evidence = output.evidence_registry.evidence[0]
    assert evidence.observation == "Original content says logs were manually inspected."
    assert evidence.source_excerpt == evidence.observation
    assert "Unsupported search-snippet claim." not in evidence.observation
    assert evidence.interpretation is None
