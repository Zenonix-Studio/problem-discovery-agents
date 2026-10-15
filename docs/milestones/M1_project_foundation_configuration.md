# M1 — Project Foundation & Configuration

**Type:** Milestone PRD-like brief | **Status:** Planning input (not implementation approval)

## Objective
Create the smallest reproducible Python project foundation and external configuration for the manually invoked research pilot, **without implementing agents**.

## In scope
- Python packaging and environment/dependency setup sufficient for planned CrewAI Flow, GitHub access, Tavily access, Pydantic and tests. Exact tooling/version choices are delegated; verify compatibility instead of guessing.
- Environment-based credentials: GitHub authenticated access, Tavily key, LLM provider credentials; document safe local setup and `.env.example` without secrets.
- A single configurable initial shared model: `gpt-5.4-mini`, reasoning effort `medium`. Provider/model are externally configurable; verify that provider/model/parameters actually exist and work, do not treat starting selection as a guarantee.
- Minimal application settings, developer commands and predictable failure messages for missing configuration.
- Decide minimal logging policy; plan run-level tokens and estimated model costs when metadata is available, and distinguish unknown/search costs.

## Out of scope
Agent prompts, research logic, scoring, external search calls, persistence beyond minimal project scaffolding, and generic frameworks.

## Proposed deliverables to plan
Project metadata and dependency lock strategy; settings module; example env config; minimal README run/setup instructions; config tests.

## Acceptance checks
A fresh developer can install and run the test suite; secrets are not committed; config overrides work; missing/unsupported config is surfaced clearly; no live API keys required for tests.

## Primary references
- Architecture v1 §3, §7–8.
- Step 4 §2 (M1), §5.
- Step 1 §2 (credentials and tool providers).

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
