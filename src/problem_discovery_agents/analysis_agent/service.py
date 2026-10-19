"""Fixture-testable, one-pass Analysis Agent service for M5."""

from __future__ import annotations

import re
from typing import Protocol

from ..contracts import (
    Alternative, AnalysisOutput, EvidenceItem, EvidenceRegistry, GapOutcome, Independence,
    Problem, ProblemStatus, ResearchOutput, VerificationStatus,
)
from ..research_agent.tools import ResearchTools
from ..research_tools.models import RetrievalState, SourceRecord
from ..validation import independent_firsthand_ids, validate_analysis_output, validate_research_output
from .models import AnalysisDiagnostics, AnalysisPlan, AnalysisRunResult, ProblemProposal, SourceSelection

# Provisional per-source text cap for the model's view of a page.
CONTEXT_TEXT_CAP = 4000
# Comments get their own provisional cap so a long body cannot crowd out the thread.
CONTEXT_COMMENTS_CAP = 12000


class AnalysisPlanner(Protocol):
    def plan(self, research: ResearchOutput) -> AnalysisPlan: ...

    def select_sources(
        self, research: ResearchOutput, investigation: AnalysisPlan, leads: list[dict[str, object]],
    ) -> SourceSelection: ...

    def finalize(
        self, research: ResearchOutput, investigation: AnalysisPlan,
        inspected_sources: list[dict[str, object]], context_sources: list[dict[str, object]],
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
        leads = self._discover(investigation, diagnostics)
        selection = (
            self._planner.select_sources(research, investigation, leads) if leads else SourceSelection()
        )
        context_urls = {
            str(item.source_url): item.evidence_id for item in research.evidence_registry.evidence
            if item.verification_status is VerificationStatus.VERIFIED
        }
        lead_urls = {lead["original_url"] for lead in leads}
        selected = list(dict.fromkeys(selection.urls))
        diagnostics.rejected_source_urls.extend(url for url in selected if url not in lead_urls)
        new_urls = [url for url in selected if url in lead_urls and url not in context_urls]
        records = self._inspect([*new_urls, *context_urls])
        new_records = {url: records[url] for url in new_urls if url in records}
        context = [
            {"evidence_id": evidence_id, "requested_url": url, "text": records[url].text[:CONTEXT_TEXT_CAP],
             **({"comments": records[url].comments_text[:CONTEXT_COMMENTS_CAP]} if records[url].comments_text else {})}
            for url, evidence_id in context_urls.items() if url in records and records[url].text
        ]
        plan = self._planner.finalize(
            research,
            investigation,
            [_capped(record) for record in new_records.values()],
            context,
        )
        diagnostics.rejected_source_urls.extend(
            url for proposal in plan.problems for url in self._proposal_urls(proposal)
            if url not in new_records and url not in diagnostics.rejected_source_urls
        )
        records = new_records
        output = self._assemble(research, plan, records, diagnostics)
        registry = validate_analysis_output(research, output)
        return AnalysisRunResult(analysis_output=output, evidence_registry=registry, diagnostics=diagnostics)

    def _discover(self, plan: AnalysisPlan, diagnostics: AnalysisDiagnostics) -> list[dict[str, object]]:
        leads: dict[str, dict[str, object]] = {}
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
            for lead in result.leads:
                leads.setdefault(lead.original_url, {
                    "original_url": lead.original_url, "title": lead.title, "snippet": lead.snippet,
                    "published_at": lead.published_at.isoformat() if lead.published_at else None,
                    "query": intent.query, "purpose": intent.purpose,
                })
        return list(leads.values())

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
            alternatives: list[Alternative] = []
            downgrades: list[str] = []
            for item in proposal.alternatives:
                ids = [
                    item_id for url in item.source_urls
                    if (item_id := evidence_id(url, "documentation")) is not None
                ]
                outcome = item.gap_outcome
                if outcome is not GapOutcome.UNKNOWN_GAP and not ids:
                    # A support claim without an inspected source is uncertainty, not a failed run.
                    downgrades.append(
                        f"Alternative '{item.name}' was proposed as {outcome.value} but no inspected "
                        "source supports it; recorded as unknown_gap."
                    )
                    outcome = GapOutcome.UNKNOWN_GAP
                alternatives.append(Alternative(
                    name=item.name, kind=item.kind, what_it_solves=item.what_it_solves,
                    gap_outcome=outcome, evidence_ids=ids,
                ))
            diagnostics.downgraded_alternatives.extend(f"P-{index:03d}: {note}" for note in downgrades)
            status = proposal.status
            missing = None
            if status is ProblemStatus.CORROBORATED and len(independent_firsthand_ids(
                proposal.evidence_ids, {**research.evidence_registry.by_id(), **{e.evidence_id: e for e in delta}}
            )) < 2:
                missing = "fewer than two linked independent firsthand evidence items exist"
            elif status in {ProblemStatus.OUTDATED, ProblemStatus.CONTRADICTED} and not counter_ids:
                missing = "no linked counterevidence exists"
            if missing:
                # An unsupported status claim is uncertainty, not a failed run.
                downgrades.append(
                    f"Status was proposed as {status.value} but {missing}; recorded as needs_validation."
                )
                diagnostics.downgraded_statuses.append(f"P-{index:03d}: {downgrades[-1]}")
                status = ProblemStatus.NEEDS_VALIDATION
            gaps = [*proposal.research_gaps, *downgrades]
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
                research_gaps=gaps, status=status,
            ))
        return AnalysisOutput(problems=problems, evidence_registry_delta=EvidenceRegistry(evidence=delta))

    @staticmethod
    def _proposal_urls(proposal: ProblemProposal) -> list[str]:
        return [
            *(source.source_url for source in proposal.counterevidence_sources),
            *(url for alternative in proposal.alternatives for url in alternative.source_urls),
        ]


def _capped(record: SourceRecord) -> dict[str, object]:
    data = record.model_dump(mode="json")
    if data.get("text"):
        data["text"] = data["text"][:CONTEXT_TEXT_CAP]
    if data.get("comments_text"):
        data["comments_text"] = data["comments_text"][:CONTEXT_COMMENTS_CAP]
    return data


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
