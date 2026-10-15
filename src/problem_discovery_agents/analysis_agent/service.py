"""Fixture-testable, one-pass Analysis Agent service for M5."""

from __future__ import annotations

import re
from typing import Protocol

from ..contracts import (
    Alternative, AnalysisOutput, EvidenceItem, EvidenceRegistry, Independence,
    Problem, ResearchOutput, VerificationStatus,
)
from ..research_agent.tools import ResearchTools
from ..research_tools.models import RetrievalState, SourceRecord
from ..validation import validate_analysis_output, validate_research_output
from .models import AnalysisDiagnostics, AnalysisPlan, AnalysisRunResult, ProblemProposal


class AnalysisPlanner(Protocol):
    def plan(self, research: ResearchOutput) -> AnalysisPlan: ...

    def finalize(
        self, research: ResearchOutput, investigation: AnalysisPlan,
        inspected_sources: list[dict[str, object]],
    ) -> AnalysisPlan: ...


class AnalysisAgent:
    """Perform exactly one analysis decision pass and bounded source inspection."""

    def __init__(self, *, planner: AnalysisPlanner, tools: ResearchTools) -> None:
        self._planner = planner
        self._tools = tools

    def run(self, research: ResearchOutput) -> AnalysisRunResult:
        validate_research_output(research)
        investigation = self._planner.plan(research)
        diagnostics = AnalysisDiagnostics()
        lead_urls = self._discover(investigation, diagnostics)
        requested = self._requested_urls(investigation)
        accepted = [url for url in requested if url in lead_urls]
        diagnostics.rejected_source_urls.extend(url for url in requested if url not in lead_urls)
        records = self._inspect(accepted)
        plan = self._planner.finalize(
            research,
            investigation,
            [record.model_dump(mode="json") for record in records.values()],
        )
        output = self._assemble(research, plan, records, diagnostics)
        registry = validate_analysis_output(research, output)
        return AnalysisRunResult(analysis_output=output, evidence_registry=registry, diagnostics=diagnostics)

    def _discover(self, plan: AnalysisPlan, diagnostics: AnalysisDiagnostics) -> set[str]:
        urls: set[str] = set()
        intents = [
            *plan.retrieval_intents,
            *(intent for problem in plan.problems for intent in problem.counterevidence_intents),
        ]
        seen_queries: set[str] = set()
        for intent in intents:
            if intent.query in seen_queries:
                continue
            seen_queries.add(intent.query)
            diagnostics.queries.append(f"{intent.purpose}: {intent.query}")
            result = self._tools.search(intent.query)
            if result.retrieval_state in {RetrievalState.FAILED, RetrievalState.INACCESSIBLE}:
                diagnostics.unsuccessful_searches.append(
                    f"{intent.query}: {'; '.join(result.limitations) or result.retrieval_state.value}"
                )
                continue
            if not result.leads:
                diagnostics.unsuccessful_searches.append(f"{intent.query}: no discovery leads returned")
            urls.update(lead.original_url for lead in result.leads)
        return urls

    @staticmethod
    def _requested_urls(plan: AnalysisPlan) -> list[str]:
        urls: list[str] = []
        for problem in plan.problems:
            urls.extend(source.source_url for source in problem.counterevidence_sources)
            for alternative in problem.alternatives:
                urls.extend(alternative.source_urls)
        return list(dict.fromkeys(urls))

    def _inspect(self, urls: list[str]) -> dict[str, SourceRecord]:
        if not urls:
            return {}
        return {record.requested_url: record for record in self._tools.extract(urls)}

    def _assemble(
        self, research: ResearchOutput, plan: AnalysisPlan, records: dict[str, SourceRecord],
        diagnostics: AnalysisDiagnostics,
    ) -> AnalysisOutput:
        delta: list[EvidenceItem] = []
        evidence_by_url: dict[str, str] = {}
        next_id = _next_evidence_number(research.evidence_registry)

        def evidence_id(url: str, evidence_class: str) -> str | None:
            nonlocal next_id
            if url in evidence_by_url:
                return evidence_by_url[url]
            record = records.get(url)
            if record is None:
                return None
            item = _evidence(f"EV-{next_id:03d}", record, evidence_class)
            next_id += 1
            delta.append(item)
            evidence_by_url[url] = item.evidence_id
            return item.evidence_id

        problems: list[Problem] = []
        for index, proposal in enumerate(plan.problems, start=1):
            counter_ids = [
                item_id for source in proposal.counterevidence_sources
                if (item_id := evidence_id(source.source_url, source.evidence_class)) is not None
            ]
            alternatives = [
                Alternative(
                    name=item.name, kind=item.kind, what_it_solves=item.what_it_solves,
                    gap_outcome=item.gap_outcome,
                    evidence_ids=[
                        item_id for url in item.source_urls
                        if (item_id := evidence_id(url, "documentation")) is not None
                    ],
                )
                for item in proposal.alternatives
            ]
            gaps = list(proposal.research_gaps)
            gaps.extend(diagnostics.unsuccessful_searches)
            rejected = [url for url in self._proposal_urls(proposal) if url in diagnostics.rejected_source_urls]
            if rejected:
                gaps.append("Proposed analysis sources were not returned as discovery leads: " + ", ".join(rejected))
            problems.append(Problem(
                problem_id=f"P-{index:03d}", finding_ids=proposal.finding_ids,
                statement=proposal.statement, user_segment=proposal.user_segment, workflow=proposal.workflow,
                clustering_rationale=proposal.clustering_rationale, status_rationale=proposal.status_rationale,
                evidence_ids=proposal.evidence_ids, independence_context=proposal.independence_context,
                alternatives=alternatives, counterevidence_ids=counter_ids,
                current_resolution_uncertainty=proposal.current_resolution_uncertainty,
                research_gaps=gaps, status=proposal.status,
            ))
        return AnalysisOutput(problems=problems, evidence_registry_delta=EvidenceRegistry(evidence=delta))

    @staticmethod
    def _proposal_urls(proposal: ProblemProposal) -> list[str]:
        return [
            *(source.source_url for source in proposal.counterevidence_sources),
            *(url for alternative in proposal.alternatives for url in alternative.source_urls),
        ]


def _next_evidence_number(registry: EvidenceRegistry) -> int:
    values = [int(match.group(1)) for item in registry.evidence for match in [re.fullmatch(r"EV-(\d+)", item.evidence_id)] if match]
    return max(values, default=0) + 1


def _evidence(evidence_id: str, record: SourceRecord, evidence_class: str) -> EvidenceItem:
    text = record.text.strip() if record.text else ""
    verification = VerificationStatus.VERIFIED if record.retrieval_state is RetrievalState.COMPLETE and text else (VerificationStatus.PARTIAL if text else VerificationStatus.UNVERIFIED)
    limitations = list(record.limitations)
    if not text:
        limitations.append("Original source content was unavailable; no excerpt was recorded.")
    if record.created_at is None:
        limitations.append("Publication date is unknown.")
    return EvidenceItem(
        evidence_id=evidence_id, source_url=record.canonical_url or record.requested_url,
        source_type=record.source_type or record.request_kind,
        published_at=record.created_at.date() if record.created_at else None,
        accessed_at=record.retrieved_at.date(), source_excerpt=_excerpt(text) if text else None,
        observation=_excerpt(text) if text else "Original source content could not be inspected; no source-supported observation is available.",
        interpretation=None, evidence_class=evidence_class if text else "unverified_source_lead",
        independence=Independence.UNCERTAIN,
        independence_rationale="Analysis source relationship to existing reports is not established.",
        verification_status=verification,
        limitations=" | ".join(dict.fromkeys(limitations)) or "No retrieval limitations recorded.",
    )


def _excerpt(text: str) -> str:
    return " ".join(text.split()[:25])[:280]
