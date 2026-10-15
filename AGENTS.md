# AGENTS.md — Problem Discovery Agents

## Purpose

This repository implements a **minimal, manually invoked CrewAI Flow** for evidence-grounded discovery of underserved developer problems. It is an **internal research pilot**, **not** the eventual open-source product to be selected from the research. Optimize for trustworthy, inspectable research outputs and small, maintainable code—not features, infrastructure, agent count, or polished UI.

The first pilot researches **Developer Tools & Productivity** only. Other categories may be considered **after human review** of the first pilot, not automatically.

## Read before writing code

Read the documents below **in this order**, assuming the decision records are placed in `docs/` at the repository root. If files are stored elsewhere, locate the same exact filenames; **do not silently proceed without the relevant source**.

1. [`docs/Problem_Discovery_Research_Agent_Guide.md`](docs/Problem_Discovery_Research_Agent_Guide.md) — authoritative research policy, evidence quality, user-value-first prioritization, report structure.
2. [`docs/Problem_Discovery_Workflow_Architecture_v1.md`](docs/Problem_Discovery_Workflow_Architecture_v1.md) — approved Flow sequence, responsibilities, handoffs, pilot scope, exclusions.
3. [`docs/Problem_Discovery_Step1_Research_Tools_Evidence_Quality_Decisions.md`](docs/Problem_Discovery_Step1_Research_Tools_Evidence_Quality_Decisions.md) — source selection, GitHub/Tavily tools, two-pass search, independence, verification.
4. [`docs/Problem_Discovery_Step2_Analysis_Rules_Decisions.md`](docs/Problem_Discovery_Step2_Analysis_Rules_Decisions.md) — clustering, alternatives, counterevidence, problem status classification.
5. [`docs/Problem_Discovery_Step3_Evaluation_Rubric_Decisions.md`](docs/Problem_Discovery_Step3_Evaluation_Rubric_Decisions.md) — authoritative Stage 1 **four-dimension /12** rubric, evidence-linked rationale, missing-evidence rules.
6. [`docs/Problem_Discovery_Step4_Implementation_Contracts_Decisions.md`](docs/Problem_Discovery_Step4_Implementation_Contracts_Decisions.md) — model configuration, evidence registry and output contracts, deterministic validations, pilot acceptance.

**Precedence:** Respect the research guide as baseline policy, the architecture as the orchestration specification, and each step decision as the authority for its named subject. Later explicit amendments win *for their specific topic*. In particular, Stage 1 is **four dimensions, /12** (not five dimensions, /15); the guide and architecture were reconciled on 2026-10-15. Do not infer that historical roadmap questions in older decision records are still open when later records resolve them. If a material conflict remains, report it before guessing.

## Required v1 workflow

```text
Manual invocation: category = Developer Tools & Productivity
  -> Research Agent, Pass 1: broad workflow/friction discovery
  -> Research Agent, Pass 2: deepen selected signals and seek independent evidence
  -> ResearchOutput (structured, inspectable JSON)
  -> Analysis Agent, single pass: cluster, check alternatives/fixes/counterevidence
  -> AnalysisOutput (structured, inspectable JSON)
  -> Evaluation Agent: evidence-based judgments
  -> deterministic Python validation/scoring/gating
  -> EvaluationOutput (structured, inspectable JSON) + one Markdown report
  -> human review against the agreed acceptance criteria
```

Use **CrewAI Flow** to coordinate the three specialized agents, with one straightforward execution path. The Evaluation Agent also writes the final report; **do not add a report-writing agent**. No Analysis-to-Research auto-rerun. Intermediate records and final report must remain auditable.

## Configuration and tools

- Initial shared model configuration: **`gpt-5.4-mini`**, reasoning effort **`medium`**. This is a *starting configuration*, not a verified provider capability or performance claim. Check actual availability and argument compatibility during implementation; fail with an actionable error if unsupported. Keep **provider/model configurable** outside agent code; do not introduce different models per agent unless later directed.
- Research tools: **GitHub REST API** for Issues, PRs, comments and metadata; **GitHub GraphQL API** selectively for Discussions; **Tavily Search** for non-GitHub discovery; **Tavily Extract** for original-page retrieval. Use authenticated GitHub access and Tavily API credentials via environment/configuration; never commit secrets.
- Search discovery snippets are **leads, not verified evidence**. Retrieved or inaccessible content must never be misrepresented as fully inspected firsthand evidence.
- Record token usage and estimated model API costs **only when provider metadata makes them available**; state unknown components explicitly. Treat search/retrieval expenses separately when relevant.
- Keep tool wiring, prompt templates, bounded retries and errors simple; exact implementation mechanics are delegated to coding agent subject to these decisions.

## Research and analysis rules

- Begin with **user workflows and friction**, not product ideas or favored technologies. Research may report a single credible observation as a hypothesis needing validation; do not manufacture corroboration or rigidly fill workload caps.
- Preserve **direct source URLs**, source/post dates when known, access dates, short faithful excerpts if verifiable, limitations, and separation of **observed**, **inferred**, **unknown**.
- Seek independent firsthand reports. Distinct posts, comments, upvotes or quoted reposts are **not automatically independent**. Track evidence relationship as `independent`, `dependent`, or `uncertain`, with rationale.
- Research Agent **does not** propose solutions, score candidates, or assert validated demand.
- Analysis Agent groups by common **task/workflow, underlying friction, and consequences**; document merge/split rationale and preserve uncertain distinctions.
- For each candidate, examine relevant platform built-ins, existing tools, actual workarounds, and evidence-backed gaps. Deliberately check fixes, version/context changes, opposing experiences and scope. `open` does not prove unresolved; `closed` does not prove fixed.
- Analysis statuses are precisely `corroborated`, `needs_validation`, `outdated`, `contradicted`. Even `corroborated` does **not** mean product demand is validated. Analysis **does not** assign evaluation scores.

## Data contracts and provenance

Define focused Pydantic models reflecting **Step 4's conceptual contracts**; exact Python class names, enum spellings beyond agreed status values, directory organization, JSON filenames and persistence details are implementation choices.

- Keep **one authoritative JSON evidence registry** containing stable unique Evidence IDs (for example `EV-001`). Research creates entries; Analysis can append/merge new evidence into the **same** registry. Do not silently overwrite ID conflicts or duplicate copied evidence within downstream records.
- Each evidence item must preserve the Step 4 minimum: ID, original URL, source type, nullable publication date, access date, nullable verbatim excerpt, supported observation, optional interpretation, evidence class, independence and rationale, verification status (`verified`, `partial`, `unverified`), and limitations.
- `ResearchOutput`: stable Finding IDs, solution-neutral friction hypotheses, user segment and workflow/category, referenced evidence IDs, and honest research coverage/gaps.
- `AnalysisOutput`: stable Problem IDs, linked Finding/Evidence IDs, statement, user/workflow, clustering rationale, independence, alternatives/workarounds and supported/unknown gaps, counterevidence, current-resolution uncertainty, status and research gaps. New evidence links to the shared registry.
- `EvaluationOutput`: per-Problem four Stage 1 assessments, optional /12 total and Stage 1 label, eligible Stage 2 assessment, and validation gaps. Produce a **single final Markdown report** following the research guide; use intermediate JSON.
- Maintain end-to-end traceability: **Evaluation → Problem → Finding/Evidence → original URL**. Citation IDs in downstream objects must resolve against their authoritative upstream record. Source verification status and actual issue resolution are different concepts.

## Stage 1: mandatory user-value gate

Score exactly **four** dimensions from `0` to `3` **or null/Research needed**, with brief evidence-linked rationale and relevant uncertainty/counterevidence:

1. **Problem Reality**
2. **Frequency / Recurrence**
3. **Alternative Gap**
4. **Meaningful Benefit**

Use the **exact score anchors** in Step 3; do not replace with a home-grown rubric. `0` means credible negative evidence under the applicable anchor; **missing support is not automatically zero**. Problem Reality `3` requires independent firsthand reports **plus additional direct technical verification**. Alternative Gap `3` requires strong firsthand evidence of recurring unmet need; Meaningful Benefit `3` requires concrete serious impact and a measurable outcome (not fabricated improvements).

Deterministic **Python code**, not the model, computes classification:

| Condition | Result |
| --- | --- |
| All four defensibly scored, total 10–12 | `Strong` |
| All four defensibly scored, total 7–9 | `Promising` |
| All four defensibly scored, total 0–6 | `Low priority` |
| Any dimension unscoreable | `Research needed`, **no total** |

Only fully scored `Strong`/`Promising` candidates **with a clearly articulable user benefit** advance to Stage 2. Stage 2 is qualitative (`Strong` / `Partial` / `Weak` / `Unknown`) for feasibility and career fit, **never** a way to change Stage 1 scores. **User Access / Validation** is useful follow-up planning context, **not** a fifth score. Do not predict stars or equate scoring with validated demand.

## Deterministic checks and error behavior

Fail fast with actionable errors on **broken contracts**, including:

- Duplicate IDs within an ID namespace; missing or dangling Evidence/Finding/Problem references; conflicting registry merges.
- Missing/nonblank-required fields, invalid enums, invalid score values, inconsistent totals/labels or Stage 2 eligibility violations.
- Missing required rationales, evidence references, or structurally inconsistent scored records.

Do **not** fail the entire research run merely because real-world facts are missing, weak, contradictory or inaccessible. Preserve these honestly as uncertainty, `needs_validation`, `Research needed`, partial/unverified evidence, or explicitly reported gaps as appropriate. Schema checks cannot prove evidence truth, source independence, correct clustering, or justified scores.

Add focused automated tests for contracts, ID/ref integrity, score boundaries, `Research needed` behavior, Stage 2 gating and report/JSON production. Mock external APIs in tests; do not require live credentials for unit tests.

## Human pilot acceptance

On the **first** Developer Tools & Productivity run, require human review of **every generated problem record**, original sources and excerpts, independence, clustering, alternatives/fixes/counterevidence, evaluation rationales, and report conclusions. Record **Pass/Fail plus rationale** for each of the five Step 4 criteria:

1. Evidence Integrity
2. Research Quality
3. Analysis Quality
4. Evaluation Consistency
5. Report Usability

There is **no quota of Strong candidates**. If a criterion fails, capture concrete examples, fix the specific responsible behavior/validator/tool, rerun, and compare; do not automatically expand architecture.

## Non-goals / scope guardrails

Do **not** introduce without a new explicit decision:

- An actual proposed OSS product, product pitch, or implementation of a discovered solution.
- Extra agents (controller, verifier, report writer), multi-agent debate or automated Analysis → Research feedback cycles.
- A database, dashboard, web UI, background monitoring/scheduler, distributed queue, or generalized agent-harness framework.
- New search vendors/integrations, speculative popularity metrics, fabricated sources, arbitrary hard research quotas, or complex cost/score engines.

Prefer the smallest credible implementation with clear boundaries and inspectable outputs.

## Coding-agent working agreement

1. **Read the source documents** relevant to a change and explicitly identify any unresolved ambiguity before altering agreed semantics.
2. Implement **one thin end-to-end path first**, then enforce contracts, test failure paths and refine prompts/tools as evidence requires.
3. Keep configuration and credentials separate from source; provide a documented example environment configuration and a short manual run procedure. Never commit tokens, API keys or sensitive material.
4. Write/revise focused tests for behavior changes; run the tests and report what passed, failed or could not be run.
5. Do not silently change research policy, evaluation thresholds, agent count or workflow sequence. Document implementation-only choices and material deviations.
6. After the pilot, report coverage and limitations plainly. **Human validation is mandatory before extending scope.**

