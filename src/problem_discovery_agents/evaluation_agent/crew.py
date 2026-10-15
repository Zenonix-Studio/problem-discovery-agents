"""Non-running CrewAI adapter for the single M6 Evaluation Agent."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..contracts import AnalysisOutput, EvidenceRegistry, EvaluationOutput, ResearchOutput
from ..model_config import LLMFactory, build_shared_llm
from ..settings import Settings
from .models import Stage1ProposalBatch, Stage2ProposalBatch
from .prompts import REPORT_INSTRUCTIONS, STAGE1_INSTRUCTIONS, STAGE2_INSTRUCTIONS

AgentFactory = Callable[..., Any]


class CrewAIEvaluationPlanner:
    """Adapt one instantiated CrewAI agent to M6's staged local boundary."""

    def __init__(self, agent: Any) -> None:
        self._agent = agent

    def propose_stage1(
        self, research: ResearchOutput, analysis: AnalysisOutput, registry: EvidenceRegistry,
    ) -> Stage1ProposalBatch:
        return self._structured(
            f"{STAGE1_INSTRUCTIONS}\nResearch handoff: {research.model_dump(mode='json')}\n"
            f"Analysis handoff: {analysis.model_dump(mode='json')}\n"
            f"Authoritative evidence registry: {registry.model_dump(mode='json')}",
            Stage1ProposalBatch,
        )

    def propose_stage2(
        self, evaluation: EvaluationOutput, team_context: str,
    ) -> Stage2ProposalBatch:
        return self._structured(
            f"{STAGE2_INSTRUCTIONS}\nEligible validated evaluations: "
            f"{evaluation.model_dump(mode='json')}\nTeam context: {team_context}",
            Stage2ProposalBatch,
        )

    def write_report(self, report_context: dict[str, object]) -> str:
        result = self._agent.kickoff(
            f"{REPORT_INSTRUCTIONS}\nValidated report context: {report_context}"
        )
        value = getattr(result, "raw", getattr(result, "output", result))
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Evaluation report response must be nonblank Markdown text")
        return value.strip()

    def _structured(self, instructions: str, response_format: type[Any]) -> Any:
        result = self._agent.kickoff(instructions, response_format=response_format)
        value = getattr(result, "pydantic", result)
        if isinstance(value, response_format):
            return value
        if isinstance(value, str):
            return response_format.model_validate_json(value)
        return response_format.model_validate(value)


def create_evaluation_crew_agent(
    settings: Settings, *, llm_factory: LLMFactory | None = None,
    agent_factory: AgentFactory | None = None,
) -> Any:
    if agent_factory is None:
        from crewai import Agent
        agent_factory = Agent
    return agent_factory(
        role="Evidence-grounded developer-problem evaluator",
        goal="Produce traceable user-value judgments and an uncertainty-preserving report.",
        backstory=f"{STAGE1_INSTRUCTIONS}\n{STAGE2_INSTRUCTIONS}\n{REPORT_INSTRUCTIONS}",
        allow_delegation=False,
        llm=build_shared_llm(settings, llm_factory=llm_factory),
    )
