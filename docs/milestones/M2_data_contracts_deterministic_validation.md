# M2 — Data Contracts & Deterministic Validation

**Type:** Milestone PRD-like brief | **Status:** Planning input (not implementation approval)

## Objective
Define the typed contracts and **deterministic** integrity/score rules used consistently by all future milestones. Keep schemas pragmatic and preserve the conceptual contracts in Step 4.

## In scope
- Pydantic models for `EvidenceItem`, authoritative JSON evidence registry, stable unique Evidence/Finding/Problem IDs, `ResearchOutput`, `AnalysisOutput`, `EvaluationOutput`, supporting records and research gaps.
- Evidence fields: direct URL/source type, nullable published date, access date, nullable short verbatim excerpt, supported observation, optional interpretation, evidence class, independence (`independent`/`dependent`/`uncertain`) and rationale, verification (`verified`/`partial`/`unverified`), limitations.
- Downstream IDs reference—not duplicate—the same registry. Research may create evidence; Analysis can append/merge into that registry; conflicts must not silently overwrite entries.
- Referential integrity: Evaluation → Problem → Finding/Evidence → source URL; required fields/enums, unique IDs, missing references, score rationales and evidence links.
- Exactly four Stage 1 dimensions, each `0..3` or unscoreable. Compute totals and labels in Python only: 10–12 Strong, 7–9 Promising, 0–6 Low priority; **any unscoreable → `Research needed` with no total**. Stage 2 only for fully scored Strong/Promising with a clearly articulable user benefit. User Access/Validation is non-scored.
- Distinguish invalid contract data (fail fast) from missing/weak or contradictory real-world evidence (preserve uncertainty).

## Out of scope
LLM prompting, tool integration, actual agent behavior or semantic proof that an evidence claim is true.

## Proposed deliverables to plan
Schema/validator modules; registry merge/serialization interfaces; focused unit tests and representative JSON fixtures. Exact file layout/class naming is delegated.

## Acceptance checks
Tests cover duplicated/conflicting IDs, dangling refs, nullable dates/excerpts, invalid enums/scores, boundary totals, partial scoring, Stage 2 gating and safe registry merging. Validators never mistake a lack of evidence for a score of zero.

## Primary references
- Step 4 §3 (M3), §3.6.
- Step 3 §2–5 (scoring anchors and uncertainty).
- Step 2 §5–6 (problem statuses and provenance).

## Reference files (read alongside AGENTS.md)
- `docs/Problem_Discovery_Step4_Implementation_Contracts_Decisions.md`
- `docs/Problem_Discovery_Step3_Evaluation_Rubric_Decisions.md`
- `docs/Problem_Discovery_Step2_Analysis_Rules_Decisions.md`

## Shared instructions for Codex
- Read repository `AGENTS.md`, the Research Agent Guide, Architecture v1, and **all Step 1–4 decision records** before planning; use the references below for deeper work on this milestone.
- This brief is a **planning input, not an implementation plan**. First propose a scoped implementation plan with files, dependencies, risks, tests, and acceptance checks. **Do not write production code until the plan is approved.**
- Follow the approved three-agent, manually run CrewAI Flow. No new agents, dashboards, databases, automatic Analysis → Research loops, or speculative product design.
- Preserve evidence provenance and uncertainty. Do not silently override approved policies or fill undefined low-level decisions with assumed requirements; propose the smallest practical choices for approval.
- Scope is the **research pilot**, not the eventual open-source product. Initial category: **Developer Tools & Productivity**.
