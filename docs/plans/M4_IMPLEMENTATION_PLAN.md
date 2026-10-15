# M4 Implementation Plan — Research Agent Implementation

## 1. Milestone goal and source references

**Goal:** implement the two-pass Research Agent for the manually invoked Developer Tools & Productivity pilot. It must convert inspected retrieval material into an initial authoritative `ResearchOutput`: source-backed evidence registry entries, solution-neutral findings, and honest coverage/gap records. It is not a demand-validation, scoring, analysis, or product-design milestone.

This plan implements only [M4 — Research Agent Implementation](../milestones/M4_research_agent_implementation.md), especially its **Objective**, **In scope**, **Out of scope**, and **Acceptance checks**. Primary authorities are:

- `AGENTS.md` — **Required v1 workflow**, **Research and analysis rules**, **Data contracts and provenance**, and **Configuration and tools**.
- `docs/Problem_Discovery_Research_Agent_Guide.md` — §§2–4 and 7 (problem-first policy, source quality, candidate information, and workflow).
- `docs/Problem_Discovery_Workflow_Architecture_v1.md` — §§3–5 (three-agent sequence, Research Agent contract, and traceability).
- `docs/Problem_Discovery_Step1_Research_Tools_Evidence_Quality_Decisions.md` — §§2–6, especially R2/R4/R6 (approved tool roles, two-pass behavior, independence, and fail-transparent verification).
- `docs/Problem_Discovery_Step4_Implementation_Contracts_Decisions.md` — §§2–3.3 and 5 (shared configurable model, one registry, `ResearchOutput`, and delegated low-level wiring).

Steps 2 and 3 are governing cross-milestone context only: M4 must preserve evidence needed for later alternatives/counterevidence and evaluation, but must not perform Analysis or Stage 1/2 work.

## 2. Scope and non-goals

### Included

- A required category input and optional workflow focus, with the implementation enforcing the initial pilot category `Developer Tools & Productivity` at the M4 boundary. With no focus, Pass 1 samples several relevant workflows and records examined/unexamined coverage.
- Pass 1 broad discovery: workflow/user mapping, friction-oriented and adaptively varied query planning, approved GitHub/Tavily retrieval, source inspection, and visible failed-search records. The approximate 8–10 signal cap is a stop/budget guard, never a quota.
- Pass 2 deepening: select only researchable Pass 1 signals (user/workflow, direct source, concrete investigable friction); seek independent firsthand evidence and source context. The approximate 4–5 selection cap and two-report target are nonbinding.
- Prompt/instruction templates that explicitly prohibit solutions, scores, demand claims, fabricated evidence, and treating search snippets as evidence.
- A narrow conversion boundary from M3 `SearchLead`/`SourceRecord` objects to M2 `EvidenceItem`, `Finding`, `ResearchCoverage`, and `ResearchOutput`, including stable run-local `EV-###`/`F-###` allocation.
- Offline mocked tests and source-context fixtures for normal, inaccessible, duplicate/dependent, single-source, and failed-search paths.

### Explicitly excluded

- Analysis clustering, alternative/workaround research, resolution/fix conclusions, problem statuses, Stage 1 scoring, Stage 2 assessment, or report generation.
- New agents, a verifier/report-writer agent, an Analysis-to-Research loop, a database, dashboard, scheduler, browser automation, new search vendors, or an eventual OSS product proposal.
- M7 Flow orchestration, run-directory JSON persistence, and live credential/provider smoke tests as a condition of unit-test success.

## 3. Current repository state and dependencies

Verified current state (2026-10-15): M1–M3 implementation is present, with a clean working tree.

- M1 provides `Settings`, a configurable shared LLM construction boundary, safe configuration validation, and `RunUsage`. `pyproject.toml` already declares CrewAI, Pydantic, HTTPX, and Tavily dependencies.
- M2 provides strict `EvidenceItem`, `EvidenceRegistry`, `ResearchCoverage`, `Finding`, and `ResearchOutput` models plus handoff validation. A `Finding` must reference registry IDs; downstream records must not copy evidence objects.
- M3 provides injected, offline-testable GitHub REST/Discussions and Tavily adapters. `SearchLead` is expressly discovery-only; `SourceRecord` carries retrieved text, dates, retrieval state, limitations, and safe errors, but is not evidence by itself.
- There is no Research Agent module, prompt template, query planner, evidence/finding ID allocator, CrewAI task/agent definition, Flow, runtime artifact persistence, or M4-specific fixture/test.

M4 depends on these interfaces and should add no changes to their established semantics unless a proven contract defect requires a separately reviewed change. M5 consumes `ResearchOutput`; M7 later owns Flow sequencing and persistence.

## 4. Proposed technical approach

### Boundary, inputs, and dependencies

**Delegated choice, recommended:** add a small `research_agent` package with an explicit `ResearchRequest(category, workflow_focus=None)` and a `ResearchAgent` service/factory. It receives the shared LLM boundary and narrowly typed M3 tool callables/adapters through constructor injection. This permits fixture-driven tests without credentials or a remote model and avoids direct environment reads in agent code.

The request validation rejects blank fields and categories other than the pilot category with an actionable scope message. A workflow focus narrows query planning but never embeds an assumed problem. Agent construction must use the M1 configurable shared-model factory; if the installed CrewAI/model wrapper rejects the configured settings, surface its existing actionable error rather than silently changing provider/model/arguments.

M4 should expose one synchronous method returning a validated `ResearchOutput` and lightweight run diagnostics (for example, query/failure decisions) in memory. It must neither serialize artifacts nor run the future Flow. M7 can invoke this method directly.

### Two-pass execution and prompts

Use one Research Agent, with two explicit prompt/task phases rather than two agents:

1. **Pass 1 — broad discovery.** Seed a small workflow map from the category/focus. Generate workflow + friction/failure + source queries; vary wording based on observed source language and failed searches. Use GitHub-first discovery where appropriate and Tavily Search for non-GitHub leads. Inspect originals via GitHub adapters or Tavily Extract before treating any material as source evidence. Preserve searches that return no usable sources, inaccessible results, and coverage limits.
2. **Pass 2 — evidence deepening.** Select researchable signals only, then seek distinct firsthand accounts and missing source context. Compare author/source/context information available in retrieved records to classify each report as independent, dependent, or uncertain with a plain rationale. Do not manufacture a second report or drop a credible singleton; retain it as a finding with a precise research gap.

The prompts should request structured candidate/evidence decisions matching M2 contracts, but a deterministic mapper validates all output. The instructions must require short faithful excerpts only from inspected content, distinguish `observation`, optional `interpretation`, and unknowns, preserve direct original URLs/dates/access dates, and record limitations. Search snippets may generate a retrieval request or failed-search note only; they cannot supply `source_excerpt`, a verified firsthand observation, or independent corroboration.

The prompt contract must state: no solution/product language, no scores, no “validated demand” claims, no issue-resolution conclusion, no inference from `open`/`closed`, no fabricated IDs/URLs/dates/quotes, and no quota filling. A tool/retrieval error is research uncertainty, not a run-wide schema failure.

### Evidence and finding assembly

**Delegated choice, recommended:** keep ID allocation deterministic within the run after ordered accepted candidates: `EV-001…` and `F-001…`. Before accepting model-proposed records, the assembler must:

- accept only a direct original/canonical URL with inspected `SourceRecord` content for `verified` or `partial` evidence; represent inaccessible/unavailable originals as `unverified`, with null excerpt and explicit limitations;
- create a short source-faithful observation and nullable excerpt only from retrieved content, preserving provider dates when known and the retrieval date as `accessed_at`;
- require an independence rationale for every registry entry and never elevate same-author reports, cross-posts, quotations, reactions, or snippets solely by count;
- retain every linked evidence ID in a solution-neutral finding with category, user segment, workflow, and friction hypothesis; and
- build `ResearchCoverage` from examined/unexamined workflows, failed searches, limitations, and targeted research gaps.

**Required M4 integration choice:** extend the existing M2 validation module with a focused public `validate_research_output(research: ResearchOutput) -> None` helper. It must reject duplicate Finding IDs and any Finding → Evidence ID that is absent from `research.evidence_registry`; Pydantic and `EvidenceRegistry` continue to reject blank required fields, invalid enums, and duplicate Evidence IDs. `validate_handoffs` remains the later cross-stage validator and is not called with invented empty Analysis/Evaluation objects. The Research Agent calls `validate_research_output` before returning its handoff. A lack of usable sources, fewer findings, contradiction, inaccessible content, or inability to establish independence remains valid output uncertainty, not a structural error.

### Tool use, errors, and auditability

Wrap M3 adapters behind a minimal research-tool protocol so tests can supply fixed source contexts. Preserve M3 retrieval limitations/errors in coverage or evidence limitations, without leaking tokens, complete remote pages, or provider secrets. Use bounded retries already provided by M3; M4 must not add unbounded query loops or hard per-query/per-workflow quotas. Record query purpose and failure reason in human-readable coverage fields; do not treat an empty result as proof the category lacks problems.

## 5. File change map

All paths below are proposals for implementation after approval.

| Path | Change | Purpose |
|---|---|---|
| `src/problem_discovery_agents/research_agent/__init__.py` | Create | Narrow public exports for request, service/factory, and run result. |
| `src/problem_discovery_agents/research_agent/models.py` | Create | Strict request, internal signal/query/inspection records, and diagnostics types distinct from the authoritative M2 handoff contracts. |
| `src/problem_discovery_agents/research_agent/prompts.py` | Create | Versioned Pass 1/Pass 2 instructions encoding approved evidence, uncertainty, and scope rules. |
| `src/problem_discovery_agents/research_agent/tools.py` | Create | Small injectable protocol/adapters over M3 GitHub/Tavily retrieval; no new vendor or direct environment access. |
| `src/problem_discovery_agents/research_agent/service.py` | Create | Two-pass sequencing, selection, source inspection, deterministic ID allocation, contract assembly, and M2 handoff validation. |
| `src/problem_discovery_agents/research_agent/crew.py` | Create only if CrewAI needs an isolated factory | Builds the one configured Research Agent/task boundary without Flow orchestration; omit if `service.py` remains clearer. |
| `src/problem_discovery_agents/validation.py` | Update | Add the narrow, M4-owned `validate_research_output` ID-reference check while preserving the existing full-handoff validator. |
| `tests/test_research_agent.py` | Create | Fixture-driven two-pass behavior, provenance, scope, prompt guardrails, and handoff validation tests. |
| `tests/test_validation.py` | Update | Cover valid and dangling Finding → Evidence references through the new research-only validator. |
| `tests/fixtures/research_agent/…` | Create | Redacted source/lead/failure and expected structured-decision fixtures; no real credentials or fabricated research claims. |
| `README.md` | Update | Brief manual-development/test guidance and explicit M4 limits, if the public invocation surface is introduced. |
| `docs/plans/M4_IMPLEMENTATION_PLAN.md` | Create | This approved planning artifact; no runtime behavior. |

## 6. Ordered implementation tasks

1. Re-read M2 contracts/validators and M3 normalized retrieval semantics. Confirm the installed CrewAI API can construct the one configured agent/task boundary without a Flow or remote request; otherwise retain an injectable model-facing boundary and report compatibility failure actionably.
2. Define validated request/internal models and the injectable research-tool protocol. Add unit tests for pilot-category enforcement, optional focus, and no direct environment/credential dependency.
3. Write Pass 1 and Pass 2 prompt templates with explicit structured-output expectations and negative constraints (no solutions, scores, demand claims, snippets-as-evidence, or invented provenance).
4. Implement bounded Pass 1 planning/discovery and its audit trail: workflow mapping, adaptive friction-oriented query variation, original-source retrieval requests, failed-search capture, and coverage bookkeeping.
5. Implement Pass 2 candidate selection/deepening. Make independent/dependent/uncertain decisions traceable to retrieved author/context data; preserve credible singletons and failed deepening attempts as gaps.
6. Add `validate_research_output` to the existing M2 validation module and its focused tests. It must check only the M4-available Finding/Evidence namespace and must not require dummy Analysis/Evaluation data.
7. Implement deterministic evidence/finding assembly, ID allocation, source-state-to-verification mapping, and the new research-only validation call. Ensure unverified inaccessible material cannot get a fabricated excerpt or verified firsthand presentation.
8. Add redacted fixtures and mocked tests for both passes, duplicates, inaccessible originals, missing dates, empty/failed searches, fewer-than-cap findings, and dangling/duplicate contract prevention.
9. Run focused and full offline test suites. Fix M4-only defects; do not add Flow persistence, Analysis behavior, external services, or live calls to make a test pass.

## 7. Test and verification plan

All tests will inject a fake LLM/structured-decision provider and M3-shaped tool fakes or `httpx.MockTransport`; they must make no network, provider, or credential request.

- **Request/scope:** blank inputs fail; a non-pilot category fails actionably; optional focus constrains workflow/query inputs without asserting a problem.
- **Pass 1:** fixtures demonstrate several workflow candidates when unfocused, friction-oriented query variation, original-source inspection before evidence creation, and visible unsuccessful-search/coverage records.
- **Pass 2:** fixtures demonstrate deepening a researchable signal, two distinct firsthand accounts marked independent with rationale, same-author/cross-post/reaction material marked dependent, and uncertain identity/context kept uncertain.
- **Verification/provenance:** extracted source text supports the observation/excerpt; search-only snippets never become evidence; unknown dates remain null; failed/inaccessible originals yield `unverified`, null excerpt, source URL, and limitations.
- **Output integrity:** `validate_research_output` accepts a valid `ResearchOutput` and rejects duplicate Finding IDs or every intentionally dangling Finding → Evidence reference; generated IDs are stable for a fixed fixture order. Existing Pydantic/registry validation continues to reject duplicate Evidence IDs and blank/invalid evidence records.
- **Honest scarcity:** zero, one, or fewer-than-provisional-cap usable signals/finding(s) returns valid coverage/gaps rather than an error or filler evidence.
- **Scope guards:** assert prompt/structured output rejects or sanitizes solution/product language, score fields, demand-validation declarations, and resolution conclusions.
- **Regression:** run `uv run pytest tests/test_research_agent.py` then `uv run pytest`. Unit tests remain offline and do not require `.env`.

If implementation exposes a local manual invocation, test it only through injected mocks. A separately authorized live tool/model run may be useful after M7, but is not M4 acceptance evidence and must preserve actual availability/limitations.

## 8. Acceptance matrix

| M4 acceptance check | Observable verification action | Expected result |
|---|---|---|
| Pass 1 and Pass 2 can run against fixtures | Execute the research service with deterministic fake structured decisions and M3-shaped retrieval fixtures. | Both ordered passes run; Pass 2 receives only selected researchable signals; no Flow, live credential, or network dependency is needed. |
| Findings cite real registry IDs | Run the new M2 `validate_research_output` helper against fixture-produced valid and dangling `ResearchOutput` instances. | Every finding ID is stable and every `evidence_id` resolves to its one authoritative registry entry; dangling Finding → Evidence references fail without requiring Analysis/Evaluation placeholders. |
| Inaccessible material remains unverified | Supply a lead whose Extract/GitHub original is inaccessible or has no inspected text. | Output retains URL/failure limitation, has `unverified` verification status and no invented excerpt/verified firsthand claim. |
| Duplicates do not count as independent | Feed same-author comments/cross-post/rebroadcast fixtures beside a distinct firsthand account. | Duplicates are `dependent` (or `uncertain` where context is insufficient) with rationale; only defensibly distinct experience is `independent`. |
| Research gaps and failed searches remain visible | Supply empty, partial, and exhausted/failed query fixtures, including an unproductive Pass 2 query. | `research_coverage` records failed searches, limitations, examined/unexamined workflow coverage, and targeted gaps; the result does not assert no category-wide problem exists. |
| Fewer findings are acceptable | Run with no usable evidence and with one credible signal. | Valid `ResearchOutput` preserves zero/one finding(s) plus coverage/gaps; it neither fabricates evidence nor fails solely due to a provisional cap. |

## 9. Risks, assumptions and decision requests

### Risks and mitigations

- **LLM structured-output or CrewAI API mismatch:** isolate the factory/parser behind injected interfaces and verify installed constructor/output compatibility locally. Fail actionably rather than silently changing model/provider or accepting malformed output.
- **Prompt overclaiming:** combine explicit instructions with deterministic assembly that requires inspected source records and M2 validation; human M8 review still assesses semantic faithfulness.
- **Identity/independence ambiguity:** use only non-intrusive available source context, classify as `uncertain` when not defensible, and explain the rationale rather than deduplicating aggressively.
- **Source access/rate limits:** retain M3 partial/error records as limitations and gaps; stop unproductive variation and do not introduce new tools or browser automation.
- **Scope creep into M5/M7:** keep resolution, alternatives, statuses, scoring, Flow, JSON persistence, and reporting out of M4 modules/tests.

### Assumptions and delegated choices

- A `ResearchAgent` service with injected structured-decision and tool boundaries is the smallest testable bridge to the future CrewAI Flow. Exact class/function names, prompt serialization format, selection heuristic, query cap implementation, and private diagnostics shape remain delegated.
- `EV-###`/`F-###` IDs are recommended only as deterministic run-local allocation; M7 will decide artifact/run lifecycle, and no global database sequence is introduced.
- M3 provider records contain sufficient content/date/context to support M4 conversion when accessible. The agent must report what is absent rather than infer it.

### Unresolved blockers / decision requests

None. The following are implementation verification tasks, not policy choices: confirm the installed CrewAI version's structured-output/task invocation mechanics with a no-network fake, and ensure the configured model wrapper can be injected through that boundary. If either is incompatible, report the concrete package/API limitation and propose the smallest compatible adapter; do not add an agent, vendor, or generic framework.

### Cross-milestone impact

M5 receives validated `ResearchOutput` and must perform the separate single-pass clustering/alternatives/counterevidence work; it may append new evidence to the same registry. M6 consumes analysis output for scoring/reporting. M7 invokes this service inside the approved Flow and persists intermediate JSON; it must not reinterpret M4 source verification as resolution/current-status proof. M8 manually reviews the source context, excerpts, independence, coverage, and gaps produced here.

## 10. Approval boundary

**Status: approved for M4 implementation (2026-10-15).** Human authorization was recorded before implementation. Stop before work on M5–M8.
