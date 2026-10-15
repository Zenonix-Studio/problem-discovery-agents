# M6 — Evaluation Agent & Report Generation

**Type:** Milestone PRD-like brief | **Status:** Planning input (not implementation approval)

## Objective
Convert analyzed problems into justified Stage 1 priority assessments, conditional Stage 2 team-fit assessments, and **one** human-readable Markdown report, retaining structured evaluation JSON.

## In scope
- Evaluation Agent proposes evidence-linked **four-dimension** Stage 1 judgments: Problem Reality, Frequency/Recurrence, Alternative Gap, Meaningful Benefit. Each dimension is defensible `0–3` **or** unscoreable, with rationale, linked evidence, counterevidence and gaps.
- Exact Step 3 anchors: Problem Reality 3 needs independent firsthand reports **plus technical verification**; Alternative Gap 3 needs strong firsthand evidence of recurring unmet needs; Meaningful Benefit 3 needs direct concrete impact **and a measurable outcome**, without inventing numerical improvements.
- Reuse M2 Python total/status/Stage 2 gate; **no LLM-authored totals or bypasses**. Stage 2 qualitative Strong/Partial/Weak/Unknown only for eligible Strong/Promising problems with clear user benefit, using documented team skills/CVs as applicable.
- Track non-scored User Access/Validation as a gap/next-step when useful.
- The **same Evaluation Agent** writes one guide-compliant Markdown report: executive summary, examined landscape, comparison, shortlisted problem cards, rejected/inconclusive findings, sources and validation questions.

## Out of scope
A fourth report agent, separate ranking engine, demand/star predictions or full product ideation.

## Proposed deliverables to plan
Evaluation prompts/instructions, JSON contracts connection, deterministic score and gate invocation, Markdown formatting and representative tests.

## Acceptance checks
Mocked scenarios cover fully scored thresholds, partial score with no total, disallowed Stage 2, contrary/outdated evidence, resolvable source refs and report inclusion of inconclusive observations.

## Primary references
- Step 3 §2–5 (authoritative rubric).
- Research Guide §5–8 (gates and report sections).
- Step 4 §3.5–3.6.

## Reference files (read alongside AGENTS.md)
- `docs/Problem_Discovery_Step3_Evaluation_Rubric_Decisions.md`
- `docs/Problem_Discovery_Research_Agent_Guide.md`
- `docs/Problem_Discovery_Step4_Implementation_Contracts_Decisions.md`

## Shared instructions for Codex
- Read repository `AGENTS.md`, the Research Agent Guide, Architecture v1, and **all Step 1–4 decision records** before planning; use the references below for deeper work on this milestone.
- This brief is a **planning input, not an implementation plan**. First propose a scoped implementation plan with files, dependencies, risks, tests, and acceptance checks. **Do not write production code until the plan is approved.**
- Follow the approved three-agent, manually run CrewAI Flow. No new agents, dashboards, databases, automatic Analysis → Research loops, or speculative product design.
- Preserve evidence provenance and uncertainty. Do not silently override approved policies or fill undefined low-level decisions with assumed requirements; propose the smallest practical choices for approval.
- Scope is the **research pilot**, not the eventual open-source product. Initial category: **Developer Tools & Productivity**.
