# M9 — Research: Lead-Grounded Candidate Selection (targeted M8 correction)

**Type:** Milestone PRD-like brief | **Status:** Planning input (not implementation approval)

## Objective
Fix the Research Agent so that candidate sources are chosen **from the discovery leads actually returned by search**, not guessed before searching. This is the single targeted correction for the first live M8 pilot run and follows the M8 failure policy: fix only the responsible boundary, rerun, compare; no scope expansion.

## Background and evidence
First live runs (category *Developer Tools & Productivity*, focus *debugging failing GitHub Actions workflows*, 2026-10-16):

- Run `run-20261016T141330Z-a71fe082` failed at the **evaluation** stage with `ValueError`; `research_output.json` contained `findings: []` and `evidence: []`.
- A Research-only probe with boundary logging showed:
  - All 6 Pass 1 Tavily searches returned `complete` with 1–5 real leads each (e.g. `github.com/actions/runner/issues/2679`).
  - `plan_pass_one` produced 5 candidate `source_url`s in the **same** planner call as the queries — all were invented GitHub issue-search pages (`.../issues?q=is%3Aissue+...`), none matched a returned lead.
  - `ResearchAgent._accepted` rejected 5/5; `extract` was called 0 times; Pass 2 received no signals (0 queries, 0 candidates); result: 0 findings.

**Root cause:** the planner must name source URLs before it can see any search result, so candidates cannot match leads. The lead-membership rule is correct; the planner contract that feeds it is not. Prompt wording alone cannot fix this because the model never sees the leads.

## In scope
- Split each research pass into: **plan** (workflows + queries, no candidate URLs) → **search** (Python, existing adapters) → **select** (same Research Agent receives the returned `SearchLead` fields — `original_url`, `title`, `snippet`, `published_at` — and proposes `CandidateSignal`s) → **accept** (existing rule: candidate URL must be one of the returned leads) → **extract** (existing inspection).
- Apply this to both Pass 1 and Pass 2; Pass 2 still starts only from inspected, researchable Pass 1 signals.
- Add one selection method to the research planner protocol and its CrewAI adapter; adjust Research prompts (remove "return candidate source URLs" from plan instructions; add a selection instruction: choose only from provided leads, never invent or alter URLs, stay solution-neutral).
- Preserve existing behavior: snippets remain leads, not evidence; originals must be inspected before becoming findings; inaccessible sources stay `unverified`; rejected candidate URLs remain in diagnostics.
- Persist research diagnostics (rejected candidate URLs, unsuccessful searches, queries) into the run manifest so a zero-finding run is explainable without a probe script.

## Out of scope
New agents, new providers/search vendors, Analysis→Research loops, changes to `ResearchOutput`/evidence contracts, Analysis or Evaluation behavior, scoring, quotas, and the report-validator behavior for zero problems (tracked below as a **separate** follow-up, to be fixed on its own with its own failing test).

## Known follow-up (not part of this milestone)
`evaluation_agent/report.py` (`REQUIRED_REPORT_CONTENT`) requires per-problem labels such as "Problem Reality" and "Next validation" even when there are zero problems, so an honest zero-problem run fails at evaluation. AGENTS.md says missing real-world facts must not fail a run. Handle as a separate, single-cause fix after this milestone's rerun.

## Proposed deliverables to plan
Planner protocol and CrewAI adapter change, prompt revision, `ResearchAgent.run` re-sequencing (leads retained instead of a bare URL set), manifest diagnostics addition, updated fakes in existing tests, new regression tests.

## Acceptance checks
Offline (no credentials, no network):
- **Regression test (written first, must fail before the fix):** fake planner supplies queries only; fake search returns a real-looking issue URL as a lead; fake selection picks it → at least one finding is produced and `extract` is called with that URL.
- A selection that returns a URL not among the returned leads is rejected and recorded in `rejected_candidate_urls`; no finding is created from it.
- Pass 2 receives only inspected Pass 1 signals; with none, it runs no selection and produces none.
- Inaccessible/empty originals stay `unverified` and appear as research gaps (existing behavior unchanged).
- Manifest includes research diagnostics; no secrets or tokens appear in it.
- Full existing test suite still passes.

Live (explicitly authorized, one Research-only probe, then one full run):
- With the same focus, Research yields findings backed by registry evidence whose URLs are direct issue/discussion URLs. Zero findings remains acceptable if honestly reported, but must now be explainable from diagnostics.
- Compare against run `run-20261016T141330Z-a71fe082`: record resolved issues and any newly introduced ones.

## Primary references
- AGENTS.md — Research and analysis rules; Search discovery snippets are leads; Deterministic checks and error behavior.
- Step 1 decision record (two-pass search, tools, verification).
- Step 4 decision record (contracts, acceptance and failure policy).
- M4 brief (Research Agent) and M8 brief (failure policy).

## Reference files (read alongside AGENTS.md)
- `docs/Problem_Discovery_Research_Agent_Guide.md`
- `docs/Problem_Discovery_Step1_Research_Tools_Evidence_Quality_Decisions.md`
- `docs/Problem_Discovery_Workflow_Architecture_v1.md`
- `docs/Problem_Discovery_Step4_Implementation_Contracts_Decisions.md`
- `src/problem_discovery_agents/research_agent/{service,crew,prompts,models}.py`, `tests/test_research_agent.py`

## Shared instructions for the coding agent
- Read repository `AGENTS.md` and the references above before planning. Follow systematic debugging: this brief records Phase 1 evidence; do not alter the root-cause statement without new evidence.
- This brief is a **planning input, not an implementation plan**. Propose a scoped plan (files, risks, tests) first; write the failing regression test before production code; one change at a time.
- Keep the approved three-agent, manually run CrewAI Flow. No new agents, databases, dashboards or automatic Analysis → Research loops.
- Live runs are paid and need explicit human authorization each time. Never place credentials in code, docs or artifacts.
