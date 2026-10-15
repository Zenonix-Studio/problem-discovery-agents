---
name: milestone-planner
description: Plan one specified M1–M8 milestone in the problem-discovery-agents repository from its milestone brief and governing decision documents. Use when asked to prepare, revise, or review a milestone implementation plan; never implement code.
---

# Milestone Planner

Create an **implementation plan for exactly one milestone**, then stop for human approval. This is a planning-only skill, not an implementation trigger.

## Invocation

The user specifies a milestone identifier in their request, e.g. `$milestone-planner M1` or `$milestone-planner M4`. Treat `MILESTONE_ID` as a **value read from the user request**, not an automatically substituted template variable.

- Accepted identifiers: `M1` through `M8`, case-insensitive; normalize to uppercase.
- If no milestone or more than one milestone is specified, ask for **one** identifier before proceeding.
- Resolve the brief by finding exactly one file matching `docs/milestones/${MILESTONE_ID}_*.md`. Do not assume a filename beyond this convention. If zero or multiple files match, explain the issue and stop.
- Plan output: `docs/plans/${MILESTONE_ID}_IMPLEMENTATION_PLAN.md`. Create `docs/plans/` if necessary.
- If that plan already exists, inspect it and the user's request: revise it when revision is requested; otherwise warn before replacing substantial previously approved content. Never silently erase approved decisions.

## Read and establish context

1. Read the repository-root `AGENTS.md` in full.
2. Read the selected milestone brief in full; take its scope, exclusions, acceptance checks and referenced documents seriously.
3. Read `docs/Problem_Discovery_Research_Agent_Guide.md`, `docs/Problem_Discovery_Workflow_Architecture_v1.md`, and all four `docs/Problem_Discovery_Step{1,2,3,4}_*_Decisions.md` files. Pay extra attention to the selected brief's primary references. If any required file is missing, report the missing path and stop; do not quietly substitute assumptions.
4. Inspect the current repository structure, relevant source files, tests, configuration and completed milestone plans. Distinguish what **actually exists** from what is merely proposed.
5. Apply the decision precedence in `AGENTS.md`. In particular, Stage 1 has four scored dimensions with a maximum of 12 and `User Access / Validation` is non-scored. Avoid reopening settled decisions.

## Planning constraints

- Plan **only** the selected milestone, keeping interfaces compatible with approved architecture and earlier implemented milestones.
- Keep to a minimal, manually invoked **three-agent CrewAI Flow research pilot**; no extra agents, database, dashboard, generic harness, automated feedback loop, or product ideation.
- Do not confuse the historic Step 1–4 **decision records** with the M1–M8 **implementation milestones**.
- Respect the milestone brief's `In scope`, `Out of scope` and acceptance checks. Cite file paths and relevant section headings in the plan when interpreting an important requirement.
- Distinguish **approved decisions**, **delegated implementation choices** (offer a simple recommendation and why), and **unresolved blockers** (request a human decision). Do not treat a reasonable coding choice as a blocker, and do not silently decide true policy conflicts.
- Do not assume unverified external API capabilities, model availability, dependency compatibility, credentials, or live integration success. Identify verification steps instead.
- Consider relevant failure modes, test fixtures/mocks, privacy/secrets, and source/ID traceability as appropriate to the milestone.
- Do **not** write production code, tests, scaffolding, install packages, run migrations, call paid APIs, or progress to the next milestone. Reading files and creating/updating the planning document are permitted.

## Required plan structure

Write a Markdown document at `docs/plans/${MILESTONE_ID}_IMPLEMENTATION_PLAN.md` containing:

1. **Milestone goal and source references** — objective and authoritative documents/sections.
2. **Scope and non-goals** — included work and explicit exclusions from the brief.
3. **Current repository state and dependencies** — verified existing artifacts vs missing prerequisites; previous milestone reuse.
4. **Proposed technical approach** — modules, boundaries, data flow, key interfaces/contracts and selected low-level choices; no unnecessary premature detail.
5. **File change map** — files to create/update and why; mark file paths as proposals where appropriate.
6. **Ordered implementation tasks** — small, independently verifiable steps and dependencies.
7. **Test and verification plan** — unit/integration tests, failure cases, test commands or commands to establish later, external-service checks where applicable.
8. **Acceptance matrix** — **every** acceptance check from the milestone brief mapped to an observable verification action and expected result. Do not assert any test is already passing unless it truly was executed and observed.
9. **Risks, assumptions and decision requests** — explicitly separate blockers from delegated choices, plus cross-milestone impacts.
10. **Approval boundary** — state that the plan is **proposed, not yet approved**, and implementation must wait.

Make the plan detailed enough that a coding agent can implement it without redesigning the milestone, but short enough to review. For M8, explicitly plan human inspection of **every problem record** and the five Pass/Fail pilot criteria; do not substitute unit tests for evidence-quality review.

## Response and stopping rule

Once the plan is saved, provide a concise summary with:

- Milestone and plan path
- Recommended approach and main file/module changes
- Genuine unresolved questions, or state that none remain
- A clear request for approval

**Stop. Do not implement the plan or invoke another skill without explicit user approval.**
