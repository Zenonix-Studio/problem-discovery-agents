# M5 — Analysis Agent Implementation

**Type:** Milestone PRD-like brief | **Status:** Planning input (not implementation approval)

## Objective
Implement the **single-pass Analysis Agent**: turn evidence-backed findings into defensible, solution-neutral analyzed problems and check whether friction is actually underserved.

## In scope
- Flexible semantic clustering based on common user task/workflow, underlying friction, and consequences. Preserve separate clusters on uncertainty; record merge/split rationale and constituent Finding IDs.
- Investigate relevant platform built-ins, competing tools, user workarounds and evidence-backed shortcomings, including whether users cannot or do not adopt alternatives.
- For **every** problem, make bounded attempts to find fixes, current-version context, conflicting user accounts and scope limitations; retain relevant supporting and contrary source IDs.
- Classify problems exactly as `corroborated`, `needs_validation`, `outdated`, `contradicted`; include rationale and unknowns. Neither multiple comments nor a closed issue establishes corroboration or a fix automatically.
- Append newly inspected analysis evidence to **the same** evidence registry via safe merge logic; generate `AnalysisOutput` with stable Problem/Finding/Evidence links.
- No automatic request to rerun Research.

## Out of scope
Stage 1 scoring, career fit, product proposals, hard semantic similarity thresholds, verification agent, autonomous feedback loops.

## Proposed deliverables to plan
Analysis agent instructions, evidence-aware alternative/counterevidence retrieval usage, schemas integration and fixture-based tests.

## Acceptance checks
Tests/examples distinguish over-merging from related but distinct frictions, retain uncertainty and counterevidence, handle closed-but-not-fixed, and ensure new evidence IDs resolve through the central registry.

## Primary references
- Step 2 §2–6 (A1, A3, A4, A5).
- Architecture v1 §4 (Analysis Agent).
- Step 1 §5 (current-status semantics).
- Step 4 §3.4.

## Reference files (read alongside AGENTS.md)
- `docs/Problem_Discovery_Step2_Analysis_Rules_Decisions.md`
- `docs/Problem_Discovery_Workflow_Architecture_v1.md`
- `docs/Problem_Discovery_Step1_Research_Tools_Evidence_Quality_Decisions.md`
- `docs/Problem_Discovery_Step4_Implementation_Contracts_Decisions.md`

## Shared instructions for Codex
- Read repository `AGENTS.md`, the Research Agent Guide, Architecture v1, and **all Step 1–4 decision records** before planning; use the references below for deeper work on this milestone.
- This brief is a **planning input, not an implementation plan**. First propose a scoped implementation plan with files, dependencies, risks, tests, and acceptance checks. **Do not write production code until the plan is approved.**
- Follow the approved three-agent, manually run CrewAI Flow. No new agents, dashboards, databases, automatic Analysis → Research loops, or speculative product design.
- Preserve evidence provenance and uncertainty. Do not silently override approved policies or fill undefined low-level decisions with assumed requirements; propose the smallest practical choices for approval.
- Scope is the **research pilot**, not the eventual open-source product. Initial category: **Developer Tools & Productivity**.
