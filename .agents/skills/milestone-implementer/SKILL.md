---
name: milestone-implementer
description: Implement and verify exactly one approved M1–M9 milestone in the problem-discovery-agents repository. Use only when the user explicitly authorizes implementation of a specific milestone and its reviewed plan; do not plan or implement other milestones.
---

# Milestone Implementer

Implement **one explicitly approved milestone plan**, verify its acceptance criteria, report results, and stop for human review. This skill does **not** imply approval of a plan merely because the plan file exists.

## Invocation and approval gate

The user invokes this skill with exactly one milestone identifier, for example `$milestone-implementer M1` or `$milestone-implementer M6`.

- Accept `M1` through `M9` (case-insensitive); normalize to uppercase. Treat the identifier as a **value extracted from the user request**, not as a templating variable that Codex substitutes automatically.
- Require **explicit user authorization to implement the identified milestone's plan**. A direct request to implement that reviewed plan qualifies; if approval is unclear, ask before changing code.
- Find **exactly one** matching brief: `docs/milestones/${MILESTONE_ID}_*.md`. If none or several match, report the ambiguity and stop.
- Require `docs/plans/${MILESTONE_ID}_IMPLEMENTATION_PLAN.md` and inspect its contents. If missing, incomplete, still awaiting resolution of blocking decisions, or inconsistent with the user's stated approval, **stop and request clarification**; do not silently create a plan or treat an unreviewed draft as approved.
- Do not infer that approvals for other milestones authorize this one. Do not proceed to the next milestone under any circumstances without a new user request.

## Establish context before editing

1. Read repository-root `AGENTS.md` in full.
2. Read the selected milestone brief and the approved milestone implementation plan in full.
3. Read the research-policy guide, architecture and all four Step 1–4 decision records in `docs/`; prioritize the selected brief's primary references. If required authoritative files are absent, stop and report the missing files rather than guessing.
4. Inspect the **actual** repository state, relevant code and tests, configuration, earlier completed milestones, and uncommitted changes. Never overwrite unrelated user work.
5. Check for discrepancies between the plan and current code. Classify them as either a minor delegated implementation choice (resolve narrowly and explain) or a material scope/contract/architecture conflict (pause affected work and ask).
6. Apply `AGENTS.md` document precedence. The currently agreed Stage 1 rubric has **four scored dimensions, /12**, and User Access / Validation is non-scored; historical Step 1–4 decision documents are not implementation milestone numbers.

## Implementation contract

- Work **only within the selected milestone's approved scope**. Implement its plan in small steps, preserving compatibility with prior milestones and the authoritative research/architecture decisions.
- Prefer readable, maintainable Python and minimal dependencies, interfaces, and abstractions. Reuse existing code when sound; avoid unrelated refactors.
- Follow the approved architecture: minimal manually invoked CrewAI Flow with Research (two passes), Analysis (one pass), Evaluation (and report), deterministic Python validation, one authoritative JSON evidence registry, intermediate JSON artifacts and a Markdown report. Introduce these parts **only when included in the current milestone**, not prematurely.
- Never add a database, dashboard, extra agent, automatic research feedback loop, generalized harness or product design unless an explicit new decision authorizes it.
- Preserve provenance, truthful source verification, observed/inferred/unknown distinctions, evidence-ID referential integrity, deterministic score/eligibility rules, and documented uncertainty wherever this milestone touches them.
- Keep secrets out of source and logs. Use documented environment/configuration mechanisms. Do not invent external provider success, model availability, API costs or research evidence.
- If a significant issue invalidates the approved plan, **stop the affected work** and communicate the conflict, its impact, and a minimal proposed adjustment. Do not quietly rewrite authoritative documents or widen scope to make an implementation work.
- Treat external calls that could incur charges, mutate external state, or consume live credentials as separate from local implementation. Obtain authorization where not already granted; use mocks/fixtures for automated tests. In M8, real pilot execution is permitted only when the user has authorized it and credentials are available.

## Verification requirements

1. Implement the milestone's appropriate unit tests and targeted failure-path coverage. Use mocked external services for deterministic tests.
2. Run relevant tests and existing repository checks (format, lint, type-check, as configured and feasible). Run integration tests when prerequisites/credentials are available and appropriately authorized.
3. Compare **every acceptance check** in the milestone brief *and* the approved plan with a concrete observable result. Classify each as `Pass`, `Fail`, or `Not verified`, with evidence (command/output, file, or human-review status).
4. Fix regressions introduced by this milestone where practical. For blocked verification, report the exact dependency or limitation; a mocked test is **not** evidence of successful live integration.
5. Do not treat green tests as proof that retrieved sources, LLM judgments, clustering, source independence or market demand are correct. Especially for **M8**, the first pilot must include human inspection of **every** generated problem record and five independent **Pass/Fail + rationale** evaluations: Evidence Integrity, Research Quality, Analysis Quality, Evaluation Consistency, and Report Usability. Never mark a human-review criterion passed on the coding agent's assertion alone.
6. No arbitrary quota of Strong candidates; honest unknowns and `Research needed` outcomes are not automatic failures.

## Documentation and change discipline

- Update relevant usage/setup/configuration documentation to reflect **implemented reality**, not future work.
- Keep the selected milestone brief and approved implementation plan as traceable requirements. Record minor justified deviations in the final report; request fresh human approval for material changes before implementing them.
- Do not rewrite governing Step 1–4 decisions or the Research Guide to rationalize code.
- Preserve existing unrelated modifications; avoid destructive cleanup, blanket formatting and broad dependency upgrades outside the milestone.
- Do not commit, push, create a PR, or start another milestone unless separately requested.

## Final completion report

After implementation and verification, report:

1. **Milestone and scope** — ID, brief and approved plan paths.
2. **Implemented** — concise summary of delivered behavior.
3. **Files changed** — new/modified files and their roles.
4. **Verification performed** — exact commands run and observed results; distinguish mocks from real integrations.
5. **Acceptance matrix** — one row per brief/plan acceptance check with `Pass`, `Fail`, or `Not verified` and supporting evidence.
6. **Deviations and unresolved issues** — any changes from the plan, risks, missing credentials, incomplete checks or decisions needing review.
7. **Status** — `Complete` only if **all mandatory checks have been verified** (including required human review); otherwise `Partially Complete` or `Blocked`, with the next necessary action.

**Stop after the report. Do not start M{next}, self-approve outstanding criteria, or broaden the research scope. Wait for human review.**
