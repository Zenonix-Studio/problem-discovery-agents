"""Non-running CrewAI construction and structured-plan boundary for M5."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..model_config import LLMFactory, build_shared_llm
from ..settings import Settings
from ..contracts import ResearchOutput
from .models import AnalysisPlan, SourceSelection
from .prompts import ANALYSIS_INSTRUCTIONS, PLAN_URL_RULE, SELECTION_INSTRUCTIONS

AgentFactory = Callable[..., Any]


class CrewAIAnalysisPlanner:
    def __init__(self, agent: Any) -> None:
        self._agent = agent

    def plan(self, research: ResearchOutput) -> AnalysisPlan:
        result = self._agent.kickoff(
            f"{ANALYSIS_INSTRUCTIONS}\n{PLAN_URL_RULE}\nResearch handoff: {research.model_dump(mode='json')}",
            response_format=AnalysisPlan,
        )
        value = getattr(result, "pydantic", result)
        if isinstance(value, AnalysisPlan):
            return value
        if isinstance(value, str):
            return AnalysisPlan.model_validate_json(value)
        return AnalysisPlan.model_validate(value)

    def select_sources(
        self, research: ResearchOutput, investigation: AnalysisPlan, leads: list[dict[str, object]],
    ) -> SourceSelection:
        result = self._agent.kickoff(
            f"{SELECTION_INSTRUCTIONS}\nInitial investigation: {investigation.model_dump(mode='json')}\n"
            f"Search leads: {leads}",
            response_format=SourceSelection,
        )
        value = getattr(result, "pydantic", result)
        if isinstance(value, SourceSelection):
            return value
        if isinstance(value, str):
            return SourceSelection.model_validate_json(value)
        return SourceSelection.model_validate(value)

    def finalize(
        self, research: ResearchOutput, investigation: AnalysisPlan,
        inspected_sources: list[dict[str, object]], context_sources: list[dict[str, object]],
    ) -> AnalysisPlan:
        result = self._agent.kickoff(
            f"{ANALYSIS_INSTRUCTIONS}\nResearch handoff: {research.model_dump(mode='json')}\n"
            f"Initial investigation: {investigation.model_dump(mode='json')}\n"
            f"Inspected source records: {inspected_sources}\n"
            f"Fuller text of existing evidence (cite by evidence_id in evidence_ids): {context_sources}\n"
            "Now produce the final AnalysisPlan. Classify alternatives, resolution, and status "
            "only from the supplied inspected records, existing-evidence text and linked prior evidence; "
            "retain gaps otherwise. Comments, when present, are under 'comments' (or 'comments_text') "
            "with each comment's URL; when a resolution or workaround comes from a comment, name that "
            "comment URL in the text and claim nothing the supplied comments do not show. Put source_urls and counterevidence_sources only for inspected source "
            "records, never for existing evidence.",
            response_format=AnalysisPlan,
        )
        value = getattr(result, "pydantic", result)
        if isinstance(value, AnalysisPlan):
            return value
        if isinstance(value, str):
            return AnalysisPlan.model_validate_json(value)
        return AnalysisPlan.model_validate(value)


def create_analysis_crew_agent(
    settings: Settings, *, llm_factory: LLMFactory | None = None,
    agent_factory: AgentFactory | None = None,
) -> Any:
    if agent_factory is None:
        from crewai import Agent
        agent_factory = Agent
    return agent_factory(
        role="Evidence-grounded developer-problem analyst",
        goal="Produce inspectable, solution-neutral analysis with uncertainty retained.",
        backstory=ANALYSIS_INSTRUCTIONS,
        allow_delegation=False,
        llm=build_shared_llm(settings, llm_factory=llm_factory),
    )
