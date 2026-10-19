# Direction Amendment — Research-and-Summarize Pilot (DRAFT)

**Status: draft for discussion, not approved.** Nothing here changes code, contracts or the agreed docs until each item in §6 is decided. Per the project rule, a later explicit amendment wins for its own topic, so this document is the place where decisions are recorded once made. Written after the first M8 live run (`artifacts/run-20261016T174447Z-b2adce4a`); the M8 human review is still pending and feeds §4.

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

## 4. What is proposed to change (needs a decision each)

| Today | Proposed | Note |
| --- | --- | --- |
| Stage 1 four-dimension score /12, Python labels | Removed from the main path; replaced by a coarse keep/drop filter | Decide whether the rubric code stays dormant or is deleted. |
| Stage 2 feasibility / career fit | Removed from the main path | Matches "no direct recommendations". |
| Shortlist cards, "Rejected and inconclusive" sections | One section per kept signal plus a "Dropped signals" appendix with reasons | Recommended: show drops so the human can disagree. |
| Analysis statuses (`corroborated`, `needs_validation`, ...) | Keep as descriptive tags, no ranking meaning | Cheap to keep; they say how much the evidence supports the claim. |
| Evaluation Agent writes the report | Same agent slot writes the summary report (no new agent) | Exactly three agents is unchanged unless you decide otherwise. |
| Input `--category` + optional `--focus` | One topic string, category optional | Small CLI change. |

## 5. "Very weak signal" — draft definition (to confirm)

Candidate drop reasons, deterministic where possible, otherwise a short model reason that is always written down:

1. No verified or partial source behind it (only snippet leads).
2. Off-topic for the stated topic.
3. No observable user friction (marketing, announcement, generic advice).
4. Exact duplicate of another kept signal (merge rather than drop).

Everything else is kept, including single-source and resolved-in-thread items, labeled as such (a resolved thread is still a useful signal for the later discussion). **This list is provisional until the six-source check in `m8_review.md` is filled in**: the real sources decide whether, for example, "resolved by maintainer" belongs under drop or keep.

## 6. Open decisions

1. Approve the core logic in §2 as the main path, with the old plan as a possible later layer.
2. Confirm §5 drop reasons after the six-source check.
3. Show dropped signals in the report with reasons (recommended) or omit them.
4. Output: `report.md` only, or `report.md` plus a structured JSON of kept signals for pasting into an LLM (recommended: keep the existing registry JSON, add nothing else).
5. Stage 1/2 code: leave dormant behind the old path, or remove.
6. How much source text the report may quote. Excerpts stay faithful and short; if the LLM discussion needs the page text, point to the URL and the registry rather than copying pages.
7. Fetch issue comments in `extract`. This matters more now: summaries are only as good as the thread content (EV-006's workarounds sit in comments).

## 7. Effects on existing work

- **M8 acceptance:** the five criteria (Evidence Integrity, Research Quality, Analysis Quality, Evaluation Consistency, Report Usability) still apply to the first run of the new path; Evaluation Consistency becomes "filter reasons are consistent".
- **Zero-problem report fix (`ZERO_PROBLEM_REPORT_FIX_PLAN.md`):** mostly moot under a summary report that has no per-card labels; keep on hold and drop it if §6.1 is approved.
- **Report wording/placement issues** (Low priority under "Shortlisted", "validated" wording): disappear with the scoring layer.
- **Docs to amend once decided:** Step 3 (rubric), Step 4 (pilot acceptance), the Workflow Architecture's Evaluation stage, `AGENTS.md` and `CLAUDE.md` (workflow, Stage 1/2 sections, status).

## 8. Proposed order after approval

1. Decide §6 items 1–5 (this document becomes the approved amendment).
2. Milestone brief for the new report path (filter + summary), with plan doc and tests first.
3. Comment-fetching in `extract` as its own small fix plan.
4. One authorized live run on a topic; human review as the acceptance gate.
