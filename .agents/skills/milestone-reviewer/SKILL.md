---
name: milestone-reviewer
description: Review a specified milestone's implementation plan or completed implementation against its brief, approved project decisions, scope, and verifiable acceptance criteria. Use for M1–M8 before approval or milestone sign-off.
---

# Milestone Reviewer

## Invocation

Use `$milestone-reviewer M1 plan` to review a proposed implementation plan, or `$milestone-reviewer M1 implementation` to review completed code. Replace `M1` with any of `M1`–`M8`. If the review mode is omitted, ask whether to review the **plan** or **implementation**; never assume approval.

## Context and authority

1. Read repository-root `AGENTS.md` and `docs/milestones/README.md` if available.
2. Locate exactly one `docs/milestones/<MILESTONE_ID>_*.md` brief, and read its referenced documents under `docs/`.
3. Read the Research Agent Guide, Workflow Architecture, and relevant Step 1–4 decisions as needed to check cross-milestone contracts. In particular, preserve the Step 3 four-dimension `/12` Stage 1 rubric and Step 4 implementation contracts. Follow the authority/precedence rules stated in the project documents; do not treat historical language as permission to override later reconciled decisions.
4. For **plan** review, read `docs/plans/<MILESTONE_ID>_IMPLEMENTATION_PLAN.md` and inspect existing repository code when relevant. For **implementation** review, read the approved plan, inspect actual changed code, and examine available test output or run appropriate local checks.
5. If a required file or evidence is missing, report the limitation rather than guessing.

## Review criteria (all milestones)

- **Requirements & traceability:** Does the work satisfy the brief, relevant authoritative decisions, and inherited contracts? Are acceptance checks explicitly mapped to evidence or tests?
- **Scope discipline:** Is anything missing, premature, or overbuilt? Challenge unnecessary abstractions, adapters, infrastructure, frameworks, optional scaffolding, and premature observability. Prefer the smallest maintainable implementation; do not reject a necessary seam solely because it anticipates a documented downstream interface.
- **Technical correctness & integration:** Are data interfaces, configuration, dependencies, sequencing, and compatibility with previous/next milestones credible? Distinguish documented assumptions from verified behavior.
- **Quality & security:** Are tests meaningful (including errors/edge cases), credentials protected, failures actionable, and provenance/uncertainty preserved where applicable? Do not mistake mocked success for verified live integration.
- **Milestone-specific essentials:** Apply the brief's own checks. Pay particular attention to evidence integrity and deterministic validation (M2), tool/source reliability (M3), firsthand/independent research and two-pass boundaries (M4), alternatives/counterevidence (M5), `/12` scoring and reporting gates (M6), one minimal Flow and artifact traceability (M7), and manual five-criterion pilot audit (M8).

## Review behavior

- Be **critical but proportional**: identify material defects, genuine risks, and useful simplifications; avoid style-only nitpicks and speculative redesign.
- Separate **blocking** problems from **non-blocking** improvements. State where an issue occurs (path/section or file/line when available), why it matters, and a minimal actionable fix.
- In **plan** mode, assess whether the plan is safe and sufficiently specific to implement; do **not** demand implementation evidence that cannot exist yet.
- In **implementation** mode, verify against actual code and available executed checks; mark unrun or credential-dependent checks **Not verified**, never **Pass**.
- Do not edit files, write code, rewrite the plan, install dependencies, or approve on the user's behalf. End with a recommendation; the human makes the approval decision.

## Output (concise)

1. **Verdict:** `Ready for approval` / `Revise before approval` (plan); `Ready for sign-off` / `Fix before sign-off` (implementation).
2. **Findings:** Only meaningful issues, ordered `Blocking` then `Non-blocking`, each with location → impact → smallest fix. Say `No material findings` if none.
3. **Acceptance coverage:** Brief criterion → `Covered` / `Gap` / `Unclear` (plan) or `Pass` / `Fail` / `Not verified` (implementation), with concise evidence.
4. **Next action:** One short recommendation. Explicitly note any blockers or verification limitations.

Stop after the review. Do not start implementation or the next milestone.
