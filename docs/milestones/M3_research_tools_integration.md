# M3 — Research Tools Integration

**Type:** Milestone PRD-like brief | **Status:** Planning input (not implementation approval)

## Objective
Expose a small reliable tool surface for gathering and verifying original research evidence. Do not do full agent reasoning here.

## In scope
- GitHub **REST-first** access to issues, PRs, comments and metadata; selective GitHub **GraphQL** access to Discussions.
- Tavily **Search** for non-GitHub discovery and **Extract** for obtaining original page content; treat snippets as leads, not verified facts.
- Small normalized tool return types or adapters that retain URL, retrieved content/context, date metadata where available, access limits and retrieval errors.
- Authentication, pagination/limits only where needed, bounded retries for transient failures and explicit incomplete/inaccessible-source status. Avoid implying retrieved snippets establish firsthand evidence.
- Surface API errors and unknown source dates explicitly; do not treat a GitHub issue's open/closed flag as authoritative proof of unresolved/resolved friction.

## Out of scope
Deduplicating research hypotheses, EvidenceItem judgments, agent prompts, extra search vendors, direct Reddit/Stack Overflow APIs, browser automation and specialized monitoring.

## Proposed deliverables to plan
Minimal GitHub REST/GraphQL and Tavily adapters; test mocks/fixtures; configuration/error interfaces usable by Research and Analysis agents.

## Acceptance checks
Mocked tests verify request/response normalization, missing source content, partial retrieval, 401/403/429/5xx responses and source metadata handling. Unit tests work offline.

## Primary references
- Step 1 §2 (R1), §5 (R6).
- Step 4 §2 (tools unchanged).
- Research Guide §3 (source priorities).

## Reference files (read alongside AGENTS.md)
- `docs/Problem_Discovery_Step1_Research_Tools_Evidence_Quality_Decisions.md`
- `docs/Problem_Discovery_Step4_Implementation_Contracts_Decisions.md`
- `docs/Problem_Discovery_Research_Agent_Guide.md`

## Shared instructions for Codex
- Read repository `AGENTS.md`, the Research Agent Guide, Architecture v1, and **all Step 1–4 decision records** before planning; use the references below for deeper work on this milestone.
- This brief is a **planning input, not an implementation plan**. First propose a scoped implementation plan with files, dependencies, risks, tests, and acceptance checks. **Do not write production code until the plan is approved.**
- Follow the approved three-agent, manually run CrewAI Flow. No new agents, dashboards, databases, automatic Analysis → Research loops, or speculative product design.
- Preserve evidence provenance and uncertainty. Do not silently override approved policies or fill undefined low-level decisions with assumed requirements; propose the smallest practical choices for approval.
- Scope is the **research pilot**, not the eventual open-source product. Initial category: **Developer Tools & Productivity**.
