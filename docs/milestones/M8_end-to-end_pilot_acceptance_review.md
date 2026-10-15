# M8 — End-to-End Pilot & Acceptance Review

**Type:** Milestone PRD-like brief | **Status:** Planning input (not implementation approval)

## Objective
Run the **first real Developer Tools & Productivity pilot**, review **every generated problem record** against its original evidence, and use findings for targeted correction—not feature expansion.

## In scope
- Execute a real, manually invoked pilot when authorized credentials are available; retain source links, intermediate JSON and final Markdown.
- Human audit of **all** problem records, their referenced source excerpts/content, independence, clustering, alternatives/workarounds, fixes, counterevidence, scoring justifications and report statements.
- Record exactly five **Pass/Fail + brief rationale** verdicts: (1) Evidence Integrity, (2) Research Quality, (3) Analysis Quality, (4) Evaluation Consistency, (5) Report Usability.
- Note source inaccessibility, coverage gaps and unscoreable dimensions transparently. **No minimum of Strong problems** and no invented findings/score improvements.
- For failures, document specific examples, fix only the responsible prompt/tool/schema/validator/agent behavior, rerun and compare for both resolved and newly introduced issues.

## Out of scope
Launching research across remaining categories before review, validating demand solely by scores, introducing new agents/infrastructure, or selecting/building the eventual OSS product.

## Proposed deliverables to plan
Pilot run checklist, captured artifacts, structured manual review record and focused fix/rerun log as necessary. Decide pragmatic review-file structure during planning.

## Acceptance checks
Each record is auditable back to original direct URLs; five acceptance criteria each have an explicit verdict/rationale; unsolved uncertainties are named; failing outcomes trigger targeted fixes rather than an automatic scope increase.

## Primary references
- Step 4 §4 (M6 acceptance and failure policy).
- Research Guide §8–9 (report/quality).
- Architecture v1 §6.
- Step 3 §6 (rubric review).

## Reference files (read alongside AGENTS.md)
- `docs/Problem_Discovery_Step4_Implementation_Contracts_Decisions.md`
- `docs/Problem_Discovery_Research_Agent_Guide.md`
- `docs/Problem_Discovery_Workflow_Architecture_v1.md`
- `docs/Problem_Discovery_Step3_Evaluation_Rubric_Decisions.md`

## Shared instructions for Codex
- Read repository `AGENTS.md`, the Research Agent Guide, Architecture v1, and **all Step 1–4 decision records** before planning; use the references below for deeper work on this milestone.
- This brief is a **planning input, not an implementation plan**. First propose a scoped implementation plan with files, dependencies, risks, tests, and acceptance checks. **Do not write production code until the plan is approved.**
- Follow the approved three-agent, manually run CrewAI Flow. No new agents, dashboards, databases, automatic Analysis → Research loops, or speculative product design.
- Preserve evidence provenance and uncertainty. Do not silently override approved policies or fill undefined low-level decisions with assumed requirements; propose the smallest practical choices for approval.
- Scope is the **research pilot**, not the eventual open-source product. Initial category: **Developer Tools & Productivity**.
