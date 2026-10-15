"""Non-running CrewAI construction boundary for the single M4 Research Agent."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..model_config import LLMFactory, build_shared_llm
from ..settings import Settings
from .models import InspectedSignal, PassPlan, ResearchRequest
from .prompts import PASS_ONE_INSTRUCTIONS, PASS_TWO_INSTRUCTIONS


AgentFactory = Callable[..., Any]


class CrewAIResearchPlanner:
    """Adapt one CrewAI Research Agent's structured responses to M4 plans."""

    def __init__(self, agent: Any) -> None:
        self._agent = agent

    def plan_pass_one(self, request: ResearchRequest) -> PassPlan:
        return self._plan(
            f"{PASS_ONE_INSTRUCTIONS}\nCategory: {request.category}\n"
            f"Workflow focus: {request.workflow_focus or 'none; sample several workflows.'}"
        )

    def plan_pass_two(
        self, request: ResearchRequest, pass_one_candidates: list[InspectedSignal]
    ) -> PassPlan:
        candidates = [candidate.model_dump(mode="json") for candidate in pass_one_candidates]
        return self._plan(
            f"{PASS_TWO_INSTRUCTIONS}\nCategory: {request.category}\n"
            f"Inspected, researchable Pass 1 signals: {candidates}"
        )

    def _plan(self, instructions: str) -> PassPlan:
        result = self._agent.kickoff(instructions, response_format=PassPlan)
        value = getattr(result, "pydantic", result)
        if isinstance(value, PassPlan):
            return value
        if isinstance(value, str):
            return PassPlan.model_validate_json(value)
        return PassPlan.model_validate(value)


def create_research_crew_agent(
    settings: Settings,
    *,
    llm_factory: LLMFactory | None = None,
    agent_factory: AgentFactory | None = None,
) -> Any:
    """Construct one configured Research Agent without creating a Flow or run.

    M7 owns task/Flow sequencing and M4's ``ResearchAgent`` service owns the
    testable pass assembly. Keeping construction here makes the shared M1 model
    configuration explicit while retaining offline unit-test injection.
    """

    if agent_factory is None:
        from crewai import Agent

        agent_factory = Agent
    return agent_factory(
        role="Evidence-grounded developer-workflow researcher",
        goal="Collect inspectable, solution-neutral developer friction evidence.",
        backstory=f"{PASS_ONE_INSTRUCTIONS}\n{PASS_TWO_INSTRUCTIONS}",
        allow_delegation=False,
        llm=build_shared_llm(settings, llm_factory=llm_factory),
    )
