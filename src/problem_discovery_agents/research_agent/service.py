"""Two-pass, fixture-testable Research Agent service for M4."""

from __future__ import annotations

from typing import Protocol
from ..contracts import (
    EvidenceItem,
    EvidenceRegistry,
    Finding,
    Independence,
    ResearchCoverage,
    ResearchOutput,
    VerificationStatus,
)
from ..research_tools.models import RetrievalState, SearchLead, SearchResult, SourceRecord
from ..validation import validate_research_output
from .models import (
    CandidateSignal,
    InspectedSignal,
    PassPlan,
    ResearchDiagnostics,
    ResearchRequest,
    ResearchRunResult,
)
from .tools import ResearchTools


class ResearchPlanner(Protocol):
    """Structured-decision boundary; a CrewAI adapter can implement this later."""

    def plan_pass_one(self, request: ResearchRequest) -> PassPlan: ...

    def plan_pass_two(
        self, request: ResearchRequest, pass_one_candidates: list[InspectedSignal]
    ) -> PassPlan: ...

    def select_candidates(
        self,
        request: ResearchRequest,
        plan: PassPlan,
        leads: list[SearchLead],
        *,
        pass_name: str,
        pass_one_candidates: list[InspectedSignal],
    ) -> list[CandidateSignal]: ...


class ResearchAgent:
    """Run exactly the approved broad-discovery then evidence-deepening passes."""

    def __init__(self, *, planner: ResearchPlanner, tools: ResearchTools) -> None:
        self._planner = planner
        self._tools = tools

    def run(self, request: ResearchRequest) -> ResearchRunResult:
        pass_one = self._planner.plan_pass_one(request)
        diagnostics = ResearchDiagnostics()
        leads_one = self._discover(pass_one, diagnostics.pass_one_queries, diagnostics)
        selected_one = self._select(request, pass_one, leads_one, "Pass 1", [])
        accepted_one = self._accepted(selected_one, leads_one, diagnostics)
        records_one = self._inspect(accepted_one)
        researchable_one = self._researchable(accepted_one, records_one)

        pass_two = PassPlan()
        accepted_two: list[CandidateSignal] = []
        records_two: dict[str, SourceRecord] = {}
        if researchable_one:
            pass_two = self._planner.plan_pass_two(request, researchable_one)
            leads_two = self._discover(pass_two, diagnostics.pass_two_queries, diagnostics)
            selected_two = self._select(request, pass_two, leads_two, "Pass 2", researchable_one)
            accepted_two = self._accepted(selected_two, leads_two, diagnostics)
            records_two = self._inspect(accepted_two)

        all_candidates = [*accepted_one, *accepted_two]
        records = {**records_one, **records_two}
        output = self._assemble(
            request, pass_one, pass_two, all_candidates, records, accepted_two, diagnostics
        )
        validate_research_output(output)
        return ResearchRunResult(research_output=output, diagnostics=diagnostics)

    def _discover(
        self, plan: PassPlan, query_log: list[str], diagnostics: ResearchDiagnostics
    ) -> list[SearchLead]:
        leads_by_url: dict[str, SearchLead] = {}
        for item in plan.queries:
            query_log.append(f"{item.purpose}: {item.query}")
            result = self._tools.search(item.query)
            if result.retrieval_state in {RetrievalState.FAILED, RetrievalState.INACCESSIBLE}:
                diagnostics.unsuccessful_searches.append(
                    f"{item.query}: {'; '.join(result.limitations) or result.retrieval_state.value}"
                )
                continue
            if not result.leads:
                diagnostics.unsuccessful_searches.append(f"{item.query}: no discovery leads returned")
            for lead in result.leads:
                leads_by_url.setdefault(lead.original_url, lead)
        return list(leads_by_url.values())

    def _select(
        self,
        request: ResearchRequest,
        plan: PassPlan,
        leads: list[SearchLead],
        pass_name: str,
        pass_one_candidates: list[InspectedSignal],
    ) -> list[CandidateSignal]:
        if not leads:
            return []
        return self._planner.select_candidates(
            request,
            plan,
            leads,
            pass_name=pass_name,
            pass_one_candidates=pass_one_candidates,
        )

    @staticmethod
    def _accepted(
        candidates: list[CandidateSignal], leads: list[SearchLead], diagnostics: ResearchDiagnostics
    ) -> list[CandidateSignal]:
        lead_urls = {lead.original_url for lead in leads}
        accepted: list[CandidateSignal] = []
        for candidate in candidates:
            if candidate.source_url in lead_urls:
                accepted.append(candidate)
            else:
                diagnostics.rejected_candidate_urls.append(candidate.source_url)
        return accepted

    def _inspect(self, candidates: list[CandidateSignal]) -> dict[str, SourceRecord]:
        urls = list(dict.fromkeys(candidate.source_url for candidate in candidates))
        if not urls:
            return {}
        return {record.requested_url: record for record in self._tools.extract(urls)}

    @staticmethod
    def _researchable(
        candidates: list[CandidateSignal], records: dict[str, SourceRecord]
    ) -> list[CandidateSignal]:
        """Keep Pass 2 grounded in an inspected, source-backed Pass 1 signal."""

        return [
            InspectedSignal(
                source_url=candidate.source_url,
                user_segment=candidate.user_segment,
                workflow=candidate.workflow,
                friction_hypothesis=candidate.friction_hypothesis,
                source_excerpt=_excerpt(record.text or ""),
                source_type=record.source_type or record.request_kind,
                author=record.author,
                published_at=record.created_at.date() if record.created_at else None,
                limitations=record.limitations,
            )
            for candidate in candidates
            if (record := records.get(candidate.source_url)) is not None
            and record.retrieval_state in {RetrievalState.COMPLETE, RetrievalState.PARTIAL}
            and bool(record.text and record.text.strip())
        ]

    def _assemble(
        self,
        request: ResearchRequest,
        pass_one: PassPlan,
        pass_two: PassPlan,
        candidates: list[CandidateSignal],
        records: dict[str, SourceRecord],
        accepted_two: list[CandidateSignal],
        diagnostics: ResearchDiagnostics,
    ) -> ResearchOutput:
        evidence: list[EvidenceItem] = []
        findings: list[Finding] = []
        authors: set[str] = set()
        evidence_by_url: dict[str, str] = {}
        limitations: list[str] = []
        gaps: list[str] = []

        for candidate in candidates:
            record = records.get(candidate.source_url)
            if record is None:
                limitations.append(f"No retrieval record returned for {candidate.source_url}.")
                continue
            evidence_id = evidence_by_url.get(record.canonical_url or record.requested_url)
            if evidence_id is None:
                evidence_id = f"EV-{len(evidence) + 1:03d}"
                item = self._evidence(evidence_id, candidate, record, authors)
                evidence.append(item)
                evidence_by_url[record.canonical_url or record.requested_url] = evidence_id
                limitations.extend(item.limitations.split(" | "))
            if not (record.text and record.text.strip()):
                gaps.append(
                    f"Original source {record.canonical_url or record.requested_url} was unavailable; "
                    "it was retained only as an unverified lead."
                )
                continue
            findings.append(
                Finding(
                    finding_id=f"F-{len(findings) + 1:03d}",
                    category=request.category,
                    user_segment=candidate.user_segment,
                    workflow=candidate.workflow,
                    friction_hypothesis=candidate.friction_hypothesis,
                    evidence_ids=[evidence_id],
                )
            )

        if not findings:
            gaps.append("No inspected source produced a usable research finding; this does not establish absence of friction.")
        if diagnostics.rejected_candidate_urls:
            gaps.append("Some proposed candidates lacked a matching discovery lead and were excluded from evidence assembly.")
        if diagnostics.pass_two_queries and not accepted_two:
            gaps.append("Pass 2 did not yield an accepted deepening candidate.")

        examined = list(dict.fromkeys([*pass_one.workflows, *pass_two.workflows]))
        unexamined = [] if request.workflow_focus else ["Other Developer Tools & Productivity workflows were not sampled."]
        return ResearchOutput(
            findings=findings,
            evidence_registry=EvidenceRegistry(evidence=evidence),
            research_coverage=ResearchCoverage(
                examined_workflows=examined,
                unexamined_workflows=unexamined,
                unsuccessful_searches=diagnostics.unsuccessful_searches,
                limitations=list(dict.fromkeys(filter(None, limitations))),
                research_gaps=gaps,
            ),
        )

    def _evidence(
        self, evidence_id: str, candidate: CandidateSignal, record: SourceRecord, authors: set[str]
    ) -> EvidenceItem:
        has_text = bool(record.text and record.text.strip())
        if record.retrieval_state is RetrievalState.COMPLETE and has_text:
            verification = VerificationStatus.VERIFIED
        elif has_text:
            verification = VerificationStatus.PARTIAL
        else:
            verification = VerificationStatus.UNVERIFIED
        if not has_text:
            independence = Independence.UNCERTAIN
            independence_rationale = "Original source content was unavailable, so independence cannot be established."
        elif record.author is None:
            independence = Independence.UNCERTAIN
            independence_rationale = "Source author/context is unavailable, so independence cannot be established."
        elif not authors:
            authors.add(record.author)
            independence = Independence.UNCERTAIN
            independence_rationale = "This is the first identified author for this run; no separate report is available for comparison."
        elif record.author in authors:
            independence = Independence.DEPENDENT
            independence_rationale = "The retrieved source has the same author as an earlier accepted report."
        else:
            authors.add(record.author)
            independence = Independence.INDEPENDENT
            independence_rationale = "The retrieved source has a distinct identified author from earlier accepted reports."
        source_url = record.canonical_url or record.requested_url
        source_limitations = list(record.limitations)
        if not has_text:
            source_limitations.append("Original source content was unavailable; no excerpt was recorded.")
        if record.created_at is None:
            source_limitations.append("Publication date is unknown.")
        return EvidenceItem(
            evidence_id=evidence_id,
            source_url=source_url,
            source_type=record.source_type or record.request_kind,
            published_at=record.created_at.date() if record.created_at else None,
            accessed_at=record.retrieved_at.date(),
            source_excerpt=_excerpt(record.text or "") if has_text else None,
            observation=(
                _excerpt(record.text or "")
                if has_text
                else "Original source content could not be inspected; no source-supported observation is available."
            ),
            # Candidate interpretation is proposed before retrieval and must not
            # be promoted into source-backed evidence without a later refinement.
            interpretation=None,
            evidence_class=candidate.evidence_class if has_text else "unverified_source_lead",
            independence=independence,
            independence_rationale=independence_rationale,
            verification_status=verification,
            limitations=" | ".join(dict.fromkeys(source_limitations)) or "No retrieval limitations recorded.",
        )


def _excerpt(text: str) -> str:
    """Keep stored quotes short, verbatim, and bounded before handing them on."""

    return " ".join(text.split()[:25])[:280]
