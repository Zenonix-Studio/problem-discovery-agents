# M4 — Research Agent Implementation

**Type:** Milestone PRD-like brief | **Status:** Planning input (not implementation approval)

## Objective
Implement the **two-pass Research Agent** that produces `ResearchOutput` and initial authoritative evidence entries. Keep research focused on observed user friction, not product proposals.

## In scope
- Required category input, optional workflow focus. Pilot uses Developer Tools & Productivity; without focus, sample multiple relevant workflows and record coverage limits.
- **Pass 1 — Broad Discovery:** workflow/user mapping; pain-oriented, adaptively varied searches; gather direct firsthand friction signals and failed-search records. Approx. 8–10 signals is a provisional cap **not quota**.
- **Pass 2 — Evidence Deepening:** revisit researchable signals; seek independent firsthand accounts where possible (2 is a target, not acceptance cutoff), check originals, dates, duplicates/cross-posts and contextual limitations. Approx. 4–5 deepened signals is also nonbinding.
- Register source-backed evidence with stable IDs and distinguish `observation`, `interpretation`, unknowns, source accessibility, verification and independence rationale.
- Emit findings with stable Finding IDs, solution-neutral friction hypothesis, user/workflow/category, evidence references and researched/unresearched coverage.

## Out of scope
Solutions, product ideas, Stage 1 scoring, demand validation claims, analysis clustering, additional agents.

## Proposed deliverables to plan
Research instructions/prompt(s), pass orchestration inside the existing Research Agent, typed output integration, tests using mocked retrieval and example source contexts.

## Acceptance checks
Pass 1 and 2 can run against fixtures; findings cite real registry IDs; inaccessible material remains unverified; duplicates do not count as independent; research gaps and failed searches remain visible. Fewer findings is acceptable.

## Primary references
- Research Guide §2–4, §7.
- Step 1 §3–5 (R2, R4, R6).
- Architecture v1 §4 (Research Agent).
- Step 4 §3.2–3.3.

## Reference files (read alongside AGENTS.md)
- `docs/Problem_Discovery_Research_Agent_Guide.md`
- `docs/Problem_Discovery_Step1_Research_Tools_Evidence_Quality_Decisions.md`
- `docs/Problem_Discovery_Workflow_Architecture_v1.md`
- `docs/Problem_Discovery_Step4_Implementation_Contracts_Decisions.md`

## Shared instructions for Codex
- Read repository `AGENTS.md`, the Research Agent Guide, Architecture v1, and **all Step 1–4 decision records** before planning; use the references below for deeper work on this milestone.
- This brief is a **planning input, not an implementation plan**. First propose a scoped implementation plan with files, dependencies, risks, tests, and acceptance checks. **Do not write production code until the plan is approved.**
- Follow the approved three-agent, manually run CrewAI Flow. No new agents, dashboards, databases, automatic Analysis → Research loops, or speculative product design.
- Preserve evidence provenance and uncertainty. Do not silently override approved policies or fill undefined low-level decisions with assumed requirements; propose the smallest practical choices for approval.
- Scope is the **research pilot**, not the eventual open-source product. Initial category: **Developer Tools & Productivity**.
