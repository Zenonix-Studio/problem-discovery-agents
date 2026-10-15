"""Manual command entry point for the first problem-discovery pilot."""

from __future__ import annotations

import argparse
from pathlib import Path

import httpx

from .artifacts import safe_error_message
from .analysis_agent import AnalysisAgent, CrewAIAnalysisPlanner, create_analysis_crew_agent
from .evaluation_agent import CrewAIEvaluationPlanner, EvaluationAgent, create_evaluation_crew_agent
from .flow import FlowServices, ProblemDiscoveryFlow, UsageCapturingAgent
from .research_agent import CrewAIResearchPlanner, M3ResearchTools, ResearchAgent, create_research_crew_agent
from .research_tools import GitHubDiscussionsAdapter, GitHubRestAdapter, TavilyAdapter
from .research_agent.models import PILOT_CATEGORY
from .settings import ConfigurationError, load_settings


def build_services(settings, client: httpx.Client) -> FlowServices:
    """Compose existing agents/tools; callers own the HTTP client's lifetime."""

    usages: list[object] = []
    tavily = TavilyAdapter(settings, client=client)
    tools = M3ResearchTools(
        tavily=tavily,
        github_rest=GitHubRestAdapter(settings, client=client),
        github_discussions=GitHubDiscussionsAdapter(settings, client=client),
    )
    research_agent = UsageCapturingAgent(create_research_crew_agent(settings), usages)
    analysis_agent = UsageCapturingAgent(create_analysis_crew_agent(settings), usages)
    evaluation_agent = UsageCapturingAgent(create_evaluation_crew_agent(settings), usages)
    return FlowServices(
        research=ResearchAgent(planner=CrewAIResearchPlanner(research_agent), tools=tools),
        analysis=AnalysisAgent(planner=CrewAIAnalysisPlanner(analysis_agent), tools=tools),
        evaluation=EvaluationAgent(planner=CrewAIEvaluationPlanner(evaluation_agent)),
        usage_records=usages,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the manually invoked problem-discovery pilot.")
    parser.add_argument("--category", required=True)
    parser.add_argument("--focus")
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    args = parser.parse_args(argv)
    if args.category != PILOT_CATEGORY:
        parser.error(f"only the pilot category {PILOT_CATEGORY!r} is supported")
    try:
        settings = load_settings()
    except ConfigurationError as error:
        print(error)
        return 2
    try:
        with httpx.Client() as client:
            flow = ProblemDiscoveryFlow(
                services=build_services(settings, client), output_root=args.output_dir,
                category=args.category, workflow_focus=args.focus,
            )
            try:
                flow.kickoff()
            except Exception as error:
                print(f"Run failed; inspect {flow.run_dir}: {safe_error_message(error)}")
                return 1
    except Exception as error:
        print(f"Run setup failed: {safe_error_message(error)}")
        return 2
    print(f"Run succeeded; inspect {flow.run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
