# CLAUDE.md — Problem Discovery Agents

Internal research pilot (not the eventual OSS product): a **minimal, manually invoked CrewAI Flow** that finds evidence-grounded, underserved developer problems. First pilot covers **Developer Tools & Productivity** only. Optimize for trustworthy, inspectable outputs and small code — not features, infrastructure, agent count, or UI.

`AGENTS.md` is the full project instruction file and stays authoritative; this file is the Claude Code summary. If they disagree, report it rather than guessing.

## Read before writing code (in order)

1. `docs/Problem_Discovery_Research_Agent_Guide.md` — research policy baseline
2. `docs/Problem_Discovery_Workflow_Architecture_v1.md` — Flow sequence, handoffs, scope
3. `docs/Problem_Discovery_Step1_Research_Tools_Evidence_Quality_Decisions.md`
4. `docs/Problem_Discovery_Step2_Analysis_Rules_Decisions.md`
5. `docs/Problem_Discovery_Step3_Evaluation_Rubric_Decisions.md` — Stage 1 rubric (**four dimensions, /12**, not five/15)
6. `docs/Problem_Discovery_Step4_Implementation_Contracts_Decisions.md` — contracts, validations, pilot acceptance

Later explicit amendments win for their own topic. Milestone briefs live in `docs/milestones/` (M1–M8), plans in `docs/plans/`; project-local milestone skills are in `.agents/skills/`.

## Workflow (single execution path)

```text
Research Agent (Pass 1 broad -> Pass 2 deepen) -> ResearchOutput JSON
 -> Analysis Agent (single pass)               -> AnalysisOutput JSON
 -> Evaluation Agent + deterministic Python    -> EvaluationOutput JSON + one report.md
 -> human review
```

Exactly three agents. The Evaluation Agent writes the report. No report-writer/controller/verifier agent, no Analysis→Research auto-rerun.

## Commands

```bash
uv sync --all-groups          # install (Python 3.11–3.13, dev baseline 3.12)
uv run pytest                 # all tests; offline, fakes only, no credentials
uv run pytest tests/test_flow.py   # single file
cp .env.example .env          # then fill PDA_* values for a live run only
uv run python -m problem_discovery_agents.run \
  --category 'Developer Tools & Productivity' --focus 'CI/CD troubleshooting'   # --focus optional
```

Run output goes to a unique dir under `artifacts/`: `research_output.json`, `analysis_output.json`, `evaluation_output.json`, `evidence_registry.json`, `report.md`, `run_manifest.json`.

## Code layout (`src/problem_discovery_agents/`)

- `contracts.py`, `validation.py` — Pydantic contracts, evidence registry, deterministic integrity/Stage 1/Stage 2 checks
- `research_tools/` — GitHub REST + Discussions GraphQL, Tavily Search/Extract (injected `httpx.Client`)
- `research_agent/`, `analysis_agent/`, `evaluation_agent/` — each: `models`, `prompts`, `service` (injected planner), `crew`; evaluation also has `report.py`
- `flow.py`, `run.py`, `artifacts.py` — Flow orchestration, CLI, persistence
- `settings.py`, `model_config.py`, `config_check.py`, `observability.py` — env config, model config, usage/cost recording

Status: M1–M7 committed; M8 (end-to-end pilot acceptance review, `docs/M8_PILOT_RUNBOOK.md`, `docs/templates/`) in progress.

## Configuration and tools

- Shared model default: `gpt-5.4-mini`, reasoning effort `medium` — a *starting config*, not a verified capability. Keep provider/model configurable via settings (`PDA_LLM_*`), one model for all agents. Fail with an actionable error if unsupported.
- Read env **only** through `problem_discovery_agents.settings`. Never commit secrets (`.env`, tokens, keys).
- Search snippets are **leads, not evidence**; never present retrieved/inaccessible content as fully inspected firsthand evidence.
- Record token usage/cost only when provider metadata provides it; state unknown parts explicitly.

## Research and analysis rules

- Start from user workflows and friction, not product ideas. Research does not propose solutions, score, or claim validated demand; one credible observation may be a hypothesis. No manufactured corroboration or rigid quotas.
- Preserve direct URLs, source/access dates, faithful excerpts, limitations; separate **observed / inferred / unknown**.
- Independence is `independent` / `dependent` / `uncertain` with rationale; reposts/upvotes/quotes are not automatically independent.
- Analysis clusters by task/workflow, friction, consequences; documents merge/split rationale; checks built-ins, tools, workarounds, fixes, counterevidence. `open` ≠ unresolved, `closed` ≠ fixed. Statuses: `corroborated`, `needs_validation`, `outdated`, `contradicted` (even `corroborated` ≠ validated demand). Analysis assigns no scores.

## Contracts and provenance

- One authoritative JSON evidence registry with stable IDs (`EV-001`…). Research creates; Analysis appends/merges into the same registry. Never silently overwrite ID conflicts or duplicate evidence downstream.
- Evidence minimum: ID, URL, source type, nullable publication date, access date, nullable verbatim excerpt, supported observation, optional interpretation, evidence class, independence + rationale, verification status (`verified`/`partial`/`unverified`), limitations.
- Traceability: **Evaluation → Problem → Finding/Evidence → original URL**; every citation ID must resolve upstream. Source verification status ≠ actual issue resolution.

## Stage 1 / Stage 2

Four dimensions scored `0–3` or null (`Research needed`), each with evidence-linked rationale, using the exact Step 3 anchors: **Problem Reality, Frequency/Recurrence, Alternative Gap, Meaningful Benefit**. Missing support is not zero. **Python, not the model,** derives totals/labels:

| Condition | Result |
| --- | --- |
| All four scored, 10–12 | `Strong` |
| All four scored, 7–9 | `Promising` |
| All four scored, 0–6 | `Low priority` |
| Any unscoreable | `Research needed`, no total |

Only fully scored `Strong`/`Promising` with a clear user benefit get Stage 2 (qualitative `Strong`/`Partial`/`Weak`/`Unknown`; feasibility and career fit; never alters Stage 1). User Access / Validation is follow-up context, not a fifth score.

## Errors and tests

- Fail fast on **broken contracts**: duplicate/dangling/conflicting IDs or refs, missing required fields, invalid enums/scores, inconsistent totals/labels, Stage 2 gate violations, missing rationales.
- Do **not** fail a run because real-world facts are weak, missing, contradictory, or inaccessible — record as uncertainty, `needs_validation`, `Research needed`, partial/unverified evidence, or gaps.
- Add focused tests for behavior changes (contracts, ID/ref integrity, score boundaries, `Research needed`, Stage 2 gating, report/JSON output). Mock all external APIs; unit tests need no live credentials. Report what passed, failed, or couldn't run.

## Pilot acceptance

First Developer Tools & Productivity run requires human review of every problem record, sources/excerpts, independence, clustering, alternatives/counterevidence, rationales, and report. Record Pass/Fail + rationale for: Evidence Integrity, Research Quality, Analysis Quality, Evaluation Consistency, Report Usability. No quota of Strong candidates. On failure: capture examples, fix the responsible behavior/validator/tool, rerun, compare — don't expand architecture.

## Non-goals (need a new explicit decision)

No proposed OSS product/pitch; no extra agents, debate, or Analysis→Research loops; no database, dashboard, web UI, scheduler, or queue; no new search vendors, popularity metrics, fabricated sources, hard research quotas, or complex cost/score engines.

## Working agreement

1. Read the relevant source docs first; flag ambiguity before changing agreed semantics.
2. Thin end-to-end path first, then contracts, failure-path tests, prompt/tool refinement.
3. Don't silently change research policy, thresholds, agent count, or workflow sequence; document implementation-only choices and deviations.
4. Don't overwrite unrelated uncommitted work (M8 docs/templates/tests are currently untracked). Commit only when asked.
5. After the pilot, report coverage and limitations plainly; human validation is mandatory before extending scope.
