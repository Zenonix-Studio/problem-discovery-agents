"""M4 two-pass Research Agent public surface."""

from .models import (
    CandidateSignal,
    InspectedSignal,
    PassPlan,
    Query,
    ResearchDiagnostics,
    ResearchRequest,
    ResearchRunResult,
)
from .crew import CrewAIResearchPlanner, create_research_crew_agent
from .service import ResearchAgent, ResearchPlanner
from .tools import M3ResearchTools, ResearchTools

__all__ = [
    "CandidateSignal", "CrewAIResearchPlanner", "InspectedSignal", "PassPlan", "Query", "ResearchAgent", "ResearchDiagnostics",
    "create_research_crew_agent",
    "M3ResearchTools", "ResearchPlanner", "ResearchRequest", "ResearchRunResult", "ResearchTools",
]
