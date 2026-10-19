# Direction Amendment — Research-and-Summarize Pilot

**Status: decisions 1–7 in §6 approved by the owner (2026-10-19); one point stays provisional (§5, resolved threads).** This document records the decisions. It changes no code or contract by itself; each implementation step still needs its own plan and approval (§8). Per the project rule, a later explicit amendment wins for its own topic. Written after the first M8 live run (`artifacts/run-20261016T174447Z-b2adce4a`); the M8 human review is still pending and feeds the §5 provisional point.

## 1. Why the direction changes

The original design makes the pipeline itself judge the problems: Stage 1 scores (/12), Python-derived labels (`Strong` / `Promising` / `Low priority` / `Research needed`), and Stage 2 qualitative fit. In practice (M8 run) this produced a verdict layer that is thin on evidence (25-word excerpts, comments not fetched, Analysis initially never opened a source) and hard to trust or tune.

New intent (owner's words, paraphrased): the user gives a research topic; the agent researches and collects signals; analyzes them simply and verifies the sources; removes only very weak signals; writes a detailed summary of the rest. The user then discusses that report with a large LLM. The workflow does not need to give recommendations.

## 2. New core logic

```text
topic (user input)
 -> Research: collect signals with verified sources         (kept, as today)
 -> Analysis: simple grouping + source verification         (simplified)
 -> Coarse filter: drop only very weak signals, keep reason (replaces scoring)
 -> Detailed summary report (report.md) for human + LLM discussion
```

The report's reader is a person plus a larger LLM, so the report must be **self-contained and inspectable**: every signal carries its URL, evidence IDs, faithful excerpts, what was observed vs inferred vs unknown, source verification status, independence notes, limitations. It does not rank, score, or recommend.

## 3. What stays (integrity layer)

- Exactly the evidence discipline: one registry with stable `EV-xxx` IDs, direct URLs, access dates, faithful excerpts, verification status, limitations; traceability report -> signal -> evidence -> URL; fail fast on broken contracts only.
- Search snippets are leads, not evidence (M9 lead-grounded selection in Research; the same in Analysis since the lead-grounded sources fix).
- Observed / inferred / unknown separation; independence as `independent` / `dependent` / `uncertain`; `open` is not unresolved, `closed` is not fixed.
- Real-world weakness is recorded as uncertainty, never a run failure.
- Offline tests with fakes; no database, UI, scheduler, extra vendors.

## 4. What changes (approved, see §6)

| Today | New | Note |
| --- | --- | --- |
| Stage 1 four-dimension score /12, Python labels | Not on the main path; replaced by a coarse keep/drop filter | Code stays dormant, not deleted (§6.5). |
| Stage 2 feasibility / career fit | Not on the main path | Matches "no direct recommendations". |
| Shortlist cards, "Rejected and inconclusive" sections | One section per kept signal plus a "Dropped signals" appendix with reasons | §6.3. |
| Analysis statuses (`corroborated`, `needs_validation`, ...) | Kept as descriptive tags, no ranking meaning | They say how much the evidence supports the claim. |
| Evaluation Agent writes the report | Same agent slot writes the summary report (no new agent) | Exactly three agents is unchanged. |
| Input `--category` + optional `--focus` | One topic string, category optional | Small CLI change; planned with the report path. |

## 5. "Very weak signal" — approved drop reasons

Only these four, deterministic where possible, otherwise a short model reason that is always written down:

1. No verified or partial source behind it (only snippet leads). Deterministic, from the registry verification status.
2. Off-topic for the stated topic. Model reason.
3. No observable user friction (marketing, announcement, generic advice). Model reason.
4. Exact duplicate of another kept signal: merged, not dropped.

Everything else is kept and labeled, including single-source, tool-specific and resolved-in-thread items. Every dropped signal appears in the report appendix with its reason.

**Still provisional:** whether "resolved in thread / fixed by maintainer" signals stay kept (current rule) or are treated differently. It is settled after the six-source check in `m8_review.md` (EV-002, 005, 006, 008 state causes or fixes on the page).

## 6. Decisions (approved 2026-10-19)

1. **Main path:** the §2 flow is the main logic; the earlier scoring plan can return later as a separate layer.
2. **Drop reasons:** the four in §5 (resolved-thread handling provisional).
3. **Dropped signals** are shown in the report appendix with reasons.
4. **Output:** `report.md` plus the existing `evidence_registry.json`. No new structured file; revisit only if needed.
5. **Stage 1/2 code:** stays in the repo, not called on the new path. Nothing is deleted until the new report has proven useful; deletion or move to a `legacy/` area would be a separate decision and plan.
6. **Source text in the report:** the 25-word / 280-character excerpt policy is unchanged. Each kept signal gets a short source-grounded summary (2–4 sentences). Every summary sentence is tied to an `EV` ID, keeps observed / inferred / unknown separate, and cannot assert anything absent from the registry. For page content beyond that, the report points to the URL and registry and does not copy pages.
7. **Issue comments:** `extract` will also fetch issue comments (first 100, bounded context). Needs its own plan before code. The plan must settle: how a comment is attributed in the registry (comment URL for traceability), the text cap, and whether GitHub Discussions comments already reach the record (read of `research_agent/tools.py` shows `extract` keeps only `primary_source`, so Discussions comments are probably dropped as well; to be verified).

## 7. Effects on existing work

- **M8 acceptance:** the five criteria (Evidence Integrity, Research Quality, Analysis Quality, Evaluation Consistency, Report Usability) still apply to the first run of the new path; Evaluation Consistency becomes "filter reasons are consistent".
- **Zero-problem report fix (`ZERO_PROBLEM_REPORT_FIX_PLAN.md`):** on hold and expected to become moot under a summary report without per-card labels. Revisit when the report milestone is planned; delete the plan if it no longer applies.
- **Report wording/placement issues** (Low priority under "Shortlisted", "validated" wording): disappear with the scoring layer.
- **Docs to amend once the first implementation lands:** Step 3 (rubric), Step 4 (pilot acceptance), the Workflow Architecture's Evaluation stage, `AGENTS.md` and `CLAUDE.md` (workflow, Stage 1/2 sections, status). Until then `AGENTS.md` / `CLAUDE.md` stay as they are and this amendment wins for the topics it covers.

## 8. Order of work (each step needs its own plan and approval before code)

1. Fix plan: fetch issue (and verify Discussions) comments in `extract` (§6.7).
2. Milestone brief for the new report path: topic input, coarse filter with reasons, summary report with dropped-signals appendix, Flow skipping Stage 1/2.
3. One authorized live run on a topic; human review as the acceptance gate.
4. Fill in the six-source check in `m8_review.md` before step 2 closes the resolved-thread rule.
