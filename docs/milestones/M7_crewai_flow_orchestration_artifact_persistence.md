# M7 — CrewAI Flow Orchestration & Artifact Persistence

**Type:** Milestone PRD-like brief | **Status:** Planning input (not implementation approval)

## Objective
Connect already-tested components into **one manually runnable CrewAI Flow**, persisting inspectable handoffs and a consistent shared evidence registry.

## In scope
- Straight-line Research Agent (Pass 1 → Pass 2) → Analysis Agent (one pass) → Evaluation Agent → report/human review handoff.
- Validate contracts and references at each transition; preserve stable IDs and merge Analysis evidence into one authoritative JSON registry without conflicting overwrites.
- Save intermediate structured `ResearchOutput`, `AnalysisOutput`, `EvaluationOutput`, evidence registry and **one** Markdown report per run. Exact layout/naming and how partial failures are preserved are delegated implementation choices.
- Provide minimal manual CLI or command entry with category and optional focus as allowed, while initial pilot remains Developer Tools & Productivity.
- Provide actionable failures, minimal bounded retries, and run-level available token/estimated model costs while identifying unknown or separate search costs.

## Out of scope
Additional controller agents, queues, background scheduling, database, dashboard, Analysis → Research feedback, automatic pilot grading or generalized harnesses.

## Proposed deliverables to plan
Flow wiring, entrypoint, artifact writer/readers, smoke/integration tests with mocked providers and short manual run instructions.

## Acceptance checks
A mocked end-to-end run writes consistent inspectable artifacts; all Evidence/Finding/Problem links resolve; deliberate schema violations fail clearly; no keys needed for automated tests; no extra agents or hidden rerun paths.

## Primary references
- Architecture v1 §3–5.
- Step 4 §1, §3, §5.
- Step 1 §3 (category and optional focus).

## Reference files (read alongside AGENTS.md)
- `docs/Problem_Discovery_Workflow_Architecture_v1.md`
- `docs/Problem_Discovery_Step4_Implementation_Contracts_Decisions.md`
- `docs/Problem_Discovery_Step1_Research_Tools_Evidence_Quality_Decisions.md`

## Shared instructions for Codex
- Read repository `AGENTS.md`, the Research Agent Guide, Architecture v1, and **all Step 1–4 decision records** before planning; use the references below for deeper work on this milestone.
- This brief is a **planning input, not an implementation plan**. First propose a scoped implementation plan with files, dependencies, risks, tests, and acceptance checks. **Do not write production code until the plan is approved.**
- Follow the approved three-agent, manually run CrewAI Flow. No new agents, dashboards, databases, automatic Analysis → Research loops, or speculative product design.
- Preserve evidence provenance and uncertainty. Do not silently override approved policies or fill undefined low-level decisions with assumed requirements; propose the smallest practical choices for approval.
- Scope is the **research pilot**, not the eventual open-source product. Initial category: **Developer Tools & Productivity**.
