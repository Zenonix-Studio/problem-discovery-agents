# M9 Implementation Plan — Research: Lead-Grounded Candidate Selection

## 1. Milestone goal and source references

Correct the Research Agent's candidate-selection boundary so a source URL is
selected only *after* the current pass's discovery search returns its leads.
This is a targeted correction to the M8 pilot failure recorded in
[`docs/milestones/M9_research_lead_grounded_candidate_selection.md`](../milestones/M9_research_lead_grounded_candidate_selection.md): the current planner proposes URLs before it has seen search output, then the valid lead-membership guard rejects all of them.

Authoritative sources, applied in precedence order, are:

- `AGENTS.md`, especially **Configuration and tools**, **Research and analysis rules**, and **Deterministic checks and error behavior**.
- `docs/Problem_Discovery_Research_Agent_Guide.md` §§2–3 and §7: start with workflow/friction, preserve failed searches, and treat snippets as leads rather than evidence.
- `docs/Problem_Discovery_Workflow_Architecture_v1.md` §§3–5: one Research Agent with two passes and inspectable JSON handoffs.
- `docs/Problem_Discovery_Step1_Research_Tools_Evidence_Quality_Decisions.md` §§2–5 (R1/R2/R4/R6): Tavily results are discovery leads; original sources require inspection; Pass 2 deepens only researchable Pass 1 signals.
- `docs/Problem_Discovery_Step4_Implementation_Contracts_Decisions.md` §§3.1–3.3 and §4.3: preserve the authoritative registry/ResearchOutput and fix the responsible boundary without scope expansion.
- M4's brief and its implemented two-pass service are the compatible predecessor; M8's failure policy and M9 brief define this correction's scope.

## 2. Scope and non-goals

### Included

- Split both Research passes into `plan → search → select → accept → extract`.
- Make plan outputs contain workflow coverage and friction-oriented queries only; they must not contain candidate source URLs.
- Give the same Research Agent a selection call that receives the returned `SearchLead` data limited to `original_url`, `title`, `snippet`, and `published_at`, then produces `CandidateSignal` objects.
- Retain deterministic acceptance: a selected `source_url` must exactly match a lead from that pass. Keep rejected selections in diagnostics.
- Preserve Pass 2's existing input constraint: it is planned only from inspected, researchable Pass 1 signals; if that list is empty, do not search/select/extract in Pass 2.
- Preserve source inspection, registry assembly, verification status, research gaps, and the rule that snippets do not become observations or evidence.
- Make the existing safe research diagnostics — Pass 1/Pass 2 queries, unsuccessful searches, and rejected candidate URLs — **survive to the final `run_manifest.json`**. Today they do not (see §3): the artifact writer replaces manifest diagnostics at each stage and failure paths write empty diagnostics. This needs a small `artifacts.py`/`flow.py` change so diagnostics accumulate across stages and are kept on failure.
- Add the specified offline regression and boundary tests; perform the described live probe/full-run steps only after separate explicit authorization.

### Explicit non-goals

- No new agent, provider, search vendor, database, dashboard, scheduler, generic harness, or Analysis → Research loop.
- No changes to `ResearchOutput`, evidence contracts, Analysis, Evaluation, Stage 1 scoring, quotas, or the known zero-problem report-validator defect. The latter remains a separate follow-up exactly as stated in the M9 brief.
- No live credential check, network call, paid probe, or full rerun in this milestone implementation unless separately authorized by a human.

## 3. Current repository state and dependencies

Verified current state (2026-10-16):

- `research_agent/models.py` defines `PassPlan` with both `queries` and `candidates`; `CandidateSignal` includes a source URL plus solution-neutral workflow/friction metadata.
- `ResearchPlanner` in `research_agent/service.py` has only `plan_pass_one` and `plan_pass_two`. `ResearchAgent.run()` plans candidates, calls `_discover()` to reduce leads to a bare URL set, accepts matching candidate URLs, then extracts originals. This is the proven root-cause boundary.
- `CrewAIResearchPlanner` in `research_agent/crew.py` requests `PassPlan` from one CrewAI agent. `PASS_ONE_INSTRUCTIONS` explicitly asks for “candidate source URLs,” which must be removed.
- `SearchLead` already provides the required selection fields. `M3ResearchTools` already extracts direct GitHub issue/discussion URLs through the approved GitHub adapters and other URLs through Tavily.
- `ResearchDiagnostics` already has `pass_one_queries`, `pass_two_queries`, `unsuccessful_searches`, and `rejected_candidate_urls`, and `ProblemDiscoveryFlow.research()` passes them to `ArtifactWriter.write_research()`. **However they do not persist to the final manifest** (verified in code and in run `run-20261016T141330Z-a71fe082`, whose manifest `diagnostics` held only `usage`):
  - `ArtifactWriter._advance()` and `write_final()` *assign* `self._manifest.diagnostics = diagnostics`, replacing rather than merging.
  - `flow._diagnostics(**stages)` returns only the current stage's key (`research=` or `analysis=` or `evaluation=`) plus `usage`, so writing Analysis drops the `research` key.
  - Failure paths call `self._writer.fail("research"|"analysis", error, {})` with empty diagnostics; the Evaluation failure path passes only `usage`.
  
  So brief item "persist research diagnostics" is **not** satisfied by existing behavior and requires a production change in `artifacts.py` and `flow.py`.
- `tests/test_research_agent.py`, `tests/test_flow.py`, and `tests/test_artifacts.py` are offline, injectable test boundaries. Existing planner fakes currently return candidate URLs from planning and will need migration.
- `docs/plans/M4_IMPLEMENTATION_PLAN.md` is implemented; `docs/plans/M8_IMPLEMENTATION_PLAN.md` and `docs/M8_PILOT_RUNBOOK.md` require targeted-fix comparison after separately authorized reruns. `docs/plans/M9_IMPLEMENTATION_PLAN.md` does not yet exist before this plan is saved.

Dependencies are existing Pydantic models, existing M3 search/extract adapters, the established Flow manifest persistence, and the installed CrewAI structured-output boundary. No dependency installation is proposed.

## 4. Proposed technical approach

### Plan, search, then select

Keep `PassPlan` as the planning contract, but remove its candidate URL collection (or replace it with a plan-only model if that produces the clearer smallest migration). It contains only workflows and `Query` records. The two existing planning calls remain responsible for scope/query construction, not for selecting sources they cannot see.

Add one reusable `ResearchPlanner.select_candidates(...) -> list[CandidateSignal]` protocol method. Its input should identify the pass and carry: the `ResearchRequest` (category/focus), the pass's `PassPlan.workflows` and query purposes, the approved lead projection, and — for Pass 2 — the inspected Pass 1 signal context. The precise argument model/name is delegated; it must make it impossible for the planner adapter to send retrieved original text as if it were a search lead.

**No conversational memory between calls.** `CrewAIResearchPlanner._plan()` issues a fresh `kickoff` per call, so "the same Research Agent" means the same configured agent, not shared context. The selection call therefore must be self-sufficient: it receives the workflows/purposes it needs to fill `user_segment`/`workflow`/`friction_hypothesis` from the supplied leads rather than inventing them. The selection prompt also carries the M4 provisional, non-binding caps (about 8–10 Pass 1 signals and 4–5 Pass 2 deepened signals; "not a quota", fewer or none is acceptable) so selection does not default to extracting every returned lead and inflating retrieval cost.

`CrewAIResearchPlanner` will serialize only the lead projection (`original_url`, nullable `title`, nullable `snippet`, nullable `published_at`) into a new selection prompt and parse `list[CandidateSignal]` via a small strict selection response wrapper. The prompt must say:

- select only supplied `original_url` values verbatim; never invent, normalize, substitute, or alter URLs;
- select based on workflow/friction relevance, while remaining solution-neutral and unscored;
- snippets are discovery leads, not source evidence; do not turn them into quotes, observations, or verification claims;
- do not propose solutions, assert demand/current resolution, or fill a quota.

Pass-planning prompts will instead request workflows and queries only. Pass 2's planning prompt retains its inspected, researchable Pass 1 signal context, but does not request candidate URLs.

### Service sequencing and guardrails

Refactor `ResearchAgent.run()` around a small per-pass helper or explicit similarly ordered code:

1. Request plan-only workflows/queries.
2. Search every planned query, append query diagnostics, preserve failed/empty search diagnostics, and retain an insertion-stable/deduplicated collection of full `SearchLead` values rather than only a set of URLs.
3. If the pass has leads, invoke selection with those leads. If it has no leads, skip selection and extraction. For Pass 2, also skip all pass work when there are no inspected researchable Pass 1 signals.
4. Apply the existing membership check using the full leads' `original_url` values. Append every rejected selected URL to `rejected_candidate_urls`; accepted candidates alone reach extraction.
5. Extract originals and retain the existing evidence/finding assembly semantics.

The membership guard stays deterministic and exact; it is defense in depth against malformed model output, not a substitute for showing leads to the selector. Preserve deterministic ordering for fixture stability and avoid accepting a URL merely because a canonical extracted URL later resembles a lead.

### Diagnostics accumulation (small production change)

Keep the existing `ResearchDiagnostics` model; do not add a parallel mechanism. Change only how the manifest holds it:

- `ArtifactWriter` merges each stage's diagnostics into the manifest's existing `diagnostics` mapping (per-stage keys `research`, `analysis`, `evaluation`, plus `usage` always the latest) instead of assigning.
- `ProblemDiscoveryFlow` failure paths pass the diagnostics accumulated so far (not `{}`), so a failed Analysis or Evaluation run still shows the Research query/rejection diagnostics and usage. A Research-stage failure has no result to report and stays empty apart from `usage` if available.
- Keep the shape JSON-safe. Do not place raw model responses, snippets, headers, settings, errors, API keys, or tokens into the manifest. Existing `safe_error_message` behavior remains authoritative for failures.

### Compatibility and scarcity behavior

Do not alter `_researchable`: only complete/partial originals with nonblank inspected text can seed Pass 2. An inaccessible/empty original still becomes unverified registry evidence and a research gap where it was an accepted selected lead; it cannot become an inspected Pass 1 seed. A zero-finding result remains valid research output with explainable diagnostics. The later Evaluation report failure for a zero-problem run is deliberately not touched.

## 5. File change map

All implementation paths below are proposals, except this plan itself.

| Path | Change | Purpose |
| --- | --- | --- |
| `src/problem_discovery_agents/research_agent/models.py` | Update | Make planning plan-only; add a strict selection response/input projection if needed; retain safe diagnostics. |
| `src/problem_discovery_agents/research_agent/service.py` | Update | Extend planner protocol; retain full search leads; sequence each pass through plan/search/select/accept/extract; skip empty/non-researchable Pass 2 correctly. |
| `src/problem_discovery_agents/research_agent/crew.py` | Update | Implement the one CrewAI selection adapter call and parse its structured candidate response. |
| `src/problem_discovery_agents/research_agent/prompts.py` | Update | Remove candidate URLs from pass-plan instructions and add lead-grounded selection instructions. |
| `src/problem_discovery_agents/research_agent/__init__.py` | Update if public types change | Keep narrow public exports aligned with the revised planner boundary. |
| `tests/test_research_agent.py` | Update | Migrate fakes; add regression-first, rejection, Pass 2 gating, prompt, and adapter tests. |
| `src/problem_discovery_agents/artifacts.py` | Update | Merge per-stage diagnostics into the manifest instead of replacing them. |
| `src/problem_discovery_agents/flow.py` | Update | Pass accumulated diagnostics on failure paths instead of `{}`; keep per-stage keys. |
| `tests/test_flow.py` | Update | Assert research diagnostics, including rejected URLs, remain in the final manifest alongside analysis/evaluation/usage, and survive an Analysis or Evaluation failure. |
| `tests/test_artifacts.py` | Update | Assert merge (not replace) behavior, and that no sentinel secrets appear in the manifest. |
| `README.md` | Update only if the documented research-agent interaction materially changes | Keep documentation truthful; no new run workflow is needed merely for M9. |
| `docs/M8_PILOT_RUNBOOK.md` / `docs/templates/M8_FIX_RERUN_LOG_TEMPLATE.md` | No behavioral change expected; use during authorized rerun | Record the required M8 comparison instead of creating a second review system. |
| `docs/plans/M9_IMPLEMENTATION_PLAN.md` | Create | This proposed plan. |

## 6. Ordered implementation tasks

1. Write the offline failing regression first: a plan-only fake emits a query, fake search returns a direct issue-like `SearchLead`, and fake selection chooses that exact URL. **Run it against the unchanged code and record the actual failure output** (including a protocol/attribute error if that is how it fails) so the red state is demonstrated, not assumed; then use it as the primary success condition. Do the same for the diagnostics-persistence test (current code drops `research` diagnostics after Analysis).
2. Introduce the smallest strict plan-only and selection-response model changes. Update the `ResearchPlanner` protocol and all offline fakes at one time so type/contract failures identify stale callers.
3. Update pass prompts and `CrewAIResearchPlanner`: planning requests no candidate URLs; selection receives the allowed lead projection and returns candidates. Add a fake-agent test proving the selection call contains a returned lead and the pass-plan call does not solicit candidates.
4. Refactor the service to preserve full `SearchLead` records and run the new sequence for Pass 1. Keep exact URL membership rejection and deterministic candidate/extraction ordering.
5. Apply the same helper/sequence to Pass 2, preserving the stricter precondition: no inspected, researchable Pass 1 signals means no Pass 2 search, selection, or extraction.
6. Verify assembly behavior remains unchanged for accessible, inaccessible, partial, duplicate, and same-author records; ensure only accepted selected candidates can produce evidence/findings.
7. Fix diagnostics persistence as its own single change, after the red test from step 1: make `ArtifactWriter` merge stage diagnostics and have Flow failure paths pass accumulated diagnostics. Test through the actual injected Flow/`ArtifactWriter` path: the final manifest contains `research` (queries, unsuccessful searches, rejected URLs), `analysis`, `evaluation` and `usage`; a forced Analysis or Evaluation failure keeps `research`; sentinel values that resemble credentials never appear.
8. Run focused offline tests, then the complete suite. Fix only M9-boundary failures; do not repair the separately identified zero-problem report validator in this change.
9. After implementation approval and separate live authorization, follow the M8 runbook for exactly one Research-only probe and one full run with the same debugging-GitHub-Actions focus. **Note:** the runbook and CLI have no Research-only mode; the Phase 1 probe was an ad hoc script (kept outside the repo). Either (a) the human accepts a throwaway probe script outside the repo for this step, or (b) skip the probe and run the full Flow once, relying on the now-persisted research diagnostics. Decide before live authorization; adding a CLI flag is out of scope. Use the existing M8 fix/rerun log to compare against `run-20261016T141330Z-a71fe082`, recording resolved and newly introduced issues. Stop if authorization is absent.

## 7. Test and verification plan

All automated checks use fake planners, agents, tool adapters, and temporary artifact directories. They require no credentials, network, paid model call, or real search result.

- **Regression-first:** before service changes, add the specified fake plan/query → returned direct issue URL → selection exact-match scenario. After the change, it produces at least one finding and calls `extract()` with that URL.
- **Lead membership:** a selector returns a URL absent from the supplied pass leads. It is rejected, listed in `rejected_candidate_urls`, never extracted, and produces no finding/evidence from that URL.
- **Selector grounding:** capture CrewAI fake-agent instructions and assert selection receives exact lead URLs/title/snippet/date; plan instructions no longer ask for candidate URLs; selection instructions forbid alteration/invention and snippets-as-evidence.
- **Pass 2 gate:** with no inspected researchable Pass 1 signal, record no Pass 2 search, selection, or extraction. With a valid inspected signal, Pass 2 may plan/search/select only against its returned leads.
- **Preserved evidence behavior:** accessible original text alone supplies excerpts/observations; inaccessible or empty originals remain `unverified` with gaps; search snippet text never appears as evidence; duplicate/same-author independence behavior remains covered.
- **Diagnostics/manifest:** run the injected Flow, parse `run_manifest.json`, and assert `diagnostics.research` includes Pass 1/Pass 2 queries, unsuccessful searches where applicable, and rejected candidate URLs **and is still present after Analysis and Evaluation write their stages**. Force an Analysis failure and an Evaluation failure and assert `research` diagnostics are retained. Seed fake secret-like strings in raw failure/provider paths and assert they are absent from the manifest.
- **Selection bounds:** assert the selection prompt carries the non-binding caps and workflow/purpose context, and that selection input never contains retrieved original text.
- **Compatibility:** run `uv run pytest tests/test_research_agent.py tests/test_flow.py tests/test_artifacts.py`, then `uv run pytest`. Do not assert a test is passing until it has been run during implementation.
- **Authorized live validation:** first run an explicitly authorized Research-only probe with the same focus and inspect its `research_output.json`/manifest. Then run one separately authorized full Flow and compare it with the failed M8 run. The outcome may validly have zero findings, but diagnostics must explain why; any finding's registry URL must be a direct issue/discussion URL and evidence must be source-backed.

## 8. Acceptance matrix

| M9 acceptance check | Observable verification action | Expected result |
| --- | --- | --- |
| Regression: returned lead can become a finding | Execute the new fake planner/search/selector test after the service change. | Selector chooses the exact returned lead; `extract()` receives it; at least one source-backed finding is produced. |
| Off-lead selection is rejected and recorded | Return a selector candidate URL not present in the same pass's leads. | No extraction/finding from that URL; it appears in `rejected_candidate_urls`. |
| Pass 2 begins only from inspected Pass 1 signals | Exercise no-text/inaccessible Pass 1 and inspect fake call history. | No Pass 2 search, selection, or extraction occurs; no Pass 2 finding is emitted. |
| Inaccessible/empty originals remain honest | Return an accepted lead whose extraction is inaccessible or empty. | It remains `unverified`, has no invented excerpt, and contributes a research gap exactly as before. |
| Diagnostics are persisted safely | Run injected Flow to artifact directory and parse manifest, including a rejected selection and a failed/empty search fixture; repeat with a forced Analysis and Evaluation failure. | Final and failed manifests keep research query, unsuccessful-search, and rejected-URL diagnostics alongside later-stage keys and `usage`; no credential/token/raw provider secret appears. |
| Existing suite remains sound | Run the focused suites and `uv run pytest`. | All tests pass offline after implementation; failures, if any, are reported rather than bypassed. |
| Authorized probe/full-run comparison | Only after separate authorization, run the same focus and complete the M8 rerun comparison record. | Direct issue/discussion evidence URLs back any findings; zero findings is explainable; resolved, remaining, and newly introduced issues are recorded against `run-20261016T141330Z-a71fe082`. |

## 9. Risks, assumptions and decision requests

### Risks and mitigations

- **CrewAI structured parsing may not accept a top-level candidate list.** Use a small strict wrapper model for the selection response if required; validate and unwrap at the adapter boundary rather than weakening parsing or adding another agent.
- **A model could still invent or normalize URLs.** Give it the actual lead values and retain exact deterministic membership checking, rejected-URL diagnostics, and tests.
- **Leads may be duplicated across query results.** Preserve a stable first-seen lead collection keyed by `original_url`, so selection input and tests are deterministic without treating duplicate results as corroboration.
- **Near-duplicate URL variants are separate leads.** The Phase 1 probe returned both `issues/2347` and `issues/2347?timeline_page=1`, and `issues/801?timeline_page=1`. Exact-match keeps them distinct; they must not be treated as independent corroboration (existing independence handling applies). URL canonicalization stays out of scope.
- **Unbounded selection could inflate retrieval cost.** Mitigated by the non-binding caps in the selection prompt; there is deliberately no hard quota (AGENTS.md).
- **Manifest diagnostics could expose data beyond what is needed.** Persist only query text/purpose, failure summaries already considered safe, and rejected URLs; never serialize lead snippets, raw LLM responses, settings, headers, credentials, or exception bodies.
- **The separate zero-problem report defect can obscure live confirmation.** Do not change it in M9. Preserve research artifacts and compare diagnostics; escalate it as the brief's separately scoped follow-up if it blocks the full-run evaluation again.

### Assumptions and delegated choices

- A single `select_candidates` protocol method with a strict wrapper model is the smallest reusable design for both passes. Exact class and argument names are delegated.
- Direct equality of selected `source_url` to a returned `SearchLead.original_url` is the recommended membership rule because the M9 evidence identifies pre-search invention as the defect. Canonicalization remains an extraction concern, not a selection bypass.
- The manifest model can hold these diagnostics, but the writer/flow currently replace them per stage and clear them on failure, so a small `artifacts.py`/`flow.py` change is required (§3, §4).
- The project-local milestone skills must recognize M9: `milestone-planner` already does; `milestone-implementer` and `milestone-reviewer` still accept only M1–M8 and need the same one-line update before they can be used for M9 (not required for manual implementation).

### Unresolved blockers / decision requests

None for offline implementation. Live probe and full-run execution are explicitly blocked pending separate human authorization because they require credentials and may incur provider/search costs.

### Cross-milestone impact

M9 changes only the M4-origin Research boundary. M5/M6 consume the unchanged `ResearchOutput` contract; M7's Flow and artifact file set remain unchanged; only the manifest's `diagnostics` content changes, now accumulating per-stage keys and surviving failures so the rejection path is explainable. M8 remains the human review and targeted rerun process. The known report-validator behavior for an honestly empty run stays outside M9 and requires its own failing test and scoped milestone.

## 10. Approval boundary

**Status: proposed, not yet approved.** This plan creates no implementation authorization. Wait for explicit approval before changing production code/tests or running any live probe/full run.
