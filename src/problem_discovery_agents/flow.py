"""The one straight-line CrewAI Flow for the manually invoked pilot."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel, ConfigDict, PrivateAttr

from .artifacts import ArtifactWriter
from .contracts import AnalysisOutput, EvidenceRegistry, ResearchOutput
from .evaluation_agent.models import EvaluationRunResult
from .observability import summarize_usages
from .research_agent.models import ResearchRequest, ResearchRunResult
from .analysis_agent.models import AnalysisRunResult
from .validation import validate_analysis_output, validate_handoffs, validate_research_output


class ResearchService(Protocol):
    def run(self, request: ResearchRequest) -> ResearchRunResult: ...


class AnalysisService(Protocol):
    def run(self, research: ResearchOutput) -> AnalysisRunResult: ...


class EvaluationService(Protocol):
    def run(self, research: ResearchOutput, analysis: AnalysisOutput, evidence_registry: EvidenceRegistry) -> EvaluationRunResult: ...


@dataclass(frozen=True)
class FlowServices:
    research: ResearchService
    analysis: AnalysisService
    evaluation: EvaluationService
    usage_records: list[object] | None = None


class FlowState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    category: str
    workflow_focus: str | None = None


class UsageCapturingAgent:
    """A transparent non-agent proxy that retains only response usage metadata."""

    def __init__(self, agent: Any, usages: list[object]) -> None:
        self._agent = agent
        self._usages = usages

    def kickoff(self, *args: Any, **kwargs: Any) -> Any:
        result = self._agent.kickoff(*args, **kwargs)
        self._usages.append(getattr(result, "usage_metrics", getattr(result, "usage", None)))
        return result

    def __getattr__(self, name: str) -> Any:
        return getattr(self._agent, name)


class ProblemDiscoveryFlow(Flow[FlowState]):
    """Run Research -> Analysis -> Evaluation once, persisting validated handoffs."""

    _services: FlowServices = PrivateAttr()
    _writer: ArtifactWriter = PrivateAttr()
    _research_result: ResearchRunResult = PrivateAttr()
    _analysis_result: AnalysisRunResult = PrivateAttr()
    _evaluation_result: EvaluationRunResult = PrivateAttr()

    def __init__(self, *, services: FlowServices, output_root: Path, category: str, workflow_focus: str | None = None) -> None:
        request = ResearchRequest(category=category, workflow_focus=workflow_focus)
        super().__init__(initial_state=FlowState(category=request.category, workflow_focus=request.workflow_focus), tracing=False)
        self._services = services
        self._writer = ArtifactWriter(output_root, request={"category": request.category, "workflow_focus": request.workflow_focus})

    @property
    def run_dir(self) -> Path:
        return self._writer.run_dir

    def _diagnostics(self, **stages: object) -> dict[str, object]:
        result = dict(stages)
        if self._services.usage_records is not None:
            result["usage"] = summarize_usages(self._services.usage_records)
        return result

    @start()
    def research(self) -> ResearchOutput:
        try:
            self._research_result = self._services.research.run(ResearchRequest(category=self.state.category, workflow_focus=self.state.workflow_focus))
            validate_research_output(self._research_result.research_output)
            self._writer.write_research(self._research_result.research_output, self._diagnostics(research=self._research_result.diagnostics.model_dump(mode="json")))
            return self._research_result.research_output
        except Exception as error:
            self._writer.fail("research", error, self._diagnostics())
            raise

    @listen(research)
    def analysis(self, research: ResearchOutput) -> AnalysisOutput:
        try:
            self._analysis_result = self._services.analysis.run(research)
            registry = validate_analysis_output(research, self._analysis_result.analysis_output)
            if registry.model_dump(mode="json") != self._analysis_result.evidence_registry.model_dump(mode="json"):
                raise ValueError("Analysis returned an EvidenceRegistry that does not match the validated merge")
            self._writer.write_analysis(self._analysis_result.analysis_output, self._diagnostics(analysis=self._analysis_result.diagnostics.model_dump(mode="json")))
            return self._analysis_result.analysis_output
        except Exception as error:
            self._writer.fail("analysis", error, self._diagnostics())
            raise

    @listen(analysis)
    def evaluation(self, analysis: AnalysisOutput) -> EvaluationRunResult:
        try:
            research = self._research_result.research_output
            self._evaluation_result = self._services.evaluation.run(research, analysis, self._analysis_result.evidence_registry)
            validate_handoffs(research, analysis, self._evaluation_result.evaluation_output)
            if (
                self._evaluation_result.evidence_registry.model_dump(mode="json")
                != self._analysis_result.evidence_registry.model_dump(mode="json")
            ):
                raise ValueError(
                    "Evaluation returned an EvidenceRegistry that does not match "
                    "the validated Analysis registry"
                )
            self._writer.write_final(self._evaluation_result.evaluation_output, self._evaluation_result.evidence_registry, self._evaluation_result.report_markdown, self._diagnostics(evaluation=self._evaluation_result.diagnostics.model_dump(mode="json")))
            return self._evaluation_result
        except Exception as error:
            self._writer.fail("evaluation", error, self._diagnostics())
            raise
