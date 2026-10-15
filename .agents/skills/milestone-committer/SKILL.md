---
name: milestone-committer
description: Review, group, and commit verified changes for a specified milestone with scoped commits, milestone-prefixed messages, and agent co-authorship. Use after implementation review and human authorization to commit.
---

# Milestone Committer

Use when the user requests committing completed work for a milestone (`M1`–`M8`), e.g. `$milestone-committer M1`.

## Preconditions

1. Read `AGENTS.md`, the relevant `docs/milestones/M*_*.md`, and the approved `docs/plans/M*_IMPLEMENTATION_PLAN.md` where available.
2. Check `git status --short`, `git diff`, `git diff --cached`, and the untracked-file list. Inspect contents before staging untracked files.
3. Confirm the milestone identifier is unambiguous and the user has authorized commits. If not, ask. Do not assume all untracked or modified files belong to this milestone.
4. Check whether the milestone's implementation/review and required tests have been completed. If not, report the gap and request explicit direction before committing unverified work.

## Commit discipline

- Group changes by coherent, independently understandable purpose (e.g. packaging, settings, tests, documentation). Prefer several focused commits over one large commit **when the changes genuinely form distinct logical units**. Avoid arbitrary file-by-file fragmentation.
- Each commit should ideally leave the repository in a coherent state; when feasible run relevant checks before committing each group. Never claim tests passed unless executed.
- Stage **explicit paths or patch hunks** (`git add <paths>` / `git add -p`); never use `git add .` or `git add -A` by default. Respect unrelated changes and pre-existing staged content: inspect and obtain clarification if attribution is ambiguous.
- Never stage secrets, `.env`, credentials, tokens, virtual environments, caches, generated local artifacts, or large irrelevant binaries. Respect `.gitignore` and inspect potentially sensitive files before staging. Do not use `git add -f` to override ignores without specific approval.
- Do not alter code merely to improve commit grouping. If separation would require unsafe rearrangement, make a coherent combined commit and explain why.
- Before each commit review `git diff --cached --stat` and `git diff --cached`; ensure only intended changes are staged.

## Commit format and attribution

- Every subject starts with the selected milestone and a hyphen: `M1- <imperative, concise description>` (e.g. `M1- Add typed environment configuration`). Keep the subject descriptive and preferably <=72 characters.
- Include an agent co-author trailer on **every** commit, using the actual coding agent's recognized name and attributable email, e.g. `Co-authored-by: Codex <codex@openai.com>` **only if that identity is known to be correct**. Do not invent an email or impersonate a person. If a verified co-author identity is unavailable, ask the user before committing; do not silently omit the requested trailer.
- Preserve the repository's configured human Git author; do not overwrite `user.name`/`user.email`, rewrite history, or amend existing commits without explicit permission.
- Use `git commit -m "M1- ..." -m "Co-authored-by: <verified agent name> <verified email>"` or equivalent so the trailer appears in the commit body.

## Safety and completion

- Do not `push`, force-push, rebase, reset, stash, clean, or delete files unless separately requested. Never bypass hooks with `--no-verify` by default.
- If a hook or check fails, stop, report the failure, and only fix issues within the authorized milestone scope; do not hide the failure.
- After committing, inspect `git log -n <N> --format=full` and `git status --short`. Confirm milestone prefixes, co-author trailers, and any changes left uncommitted.
- Report commits in order (short SHA + subject + scope), tests/checks actually run, and remaining staged/unstaged/untracked files. Never state the working tree is clean unless verified.
- Stop after local commits. Wait for explicit instruction before pushing or starting another milestone.
