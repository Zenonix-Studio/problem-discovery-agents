# Fix Plan — Analysis: Lead-Grounded Source Selection and Fuller Source Context (targeted M8 correction)

**Status: proposed, not yet approved.** Small, single-boundary correction following the M8 failure policy (fix only the responsible boundary, rerun, compare). Applies the M9 pattern (plan → search → select → accept → extract) to the Analysis Agent. No production code, test or live run until this plan is approved; any live run needs separate explicit authorization because it is paid.

## 1. Problem and evidence

M8 pilot run `artifacts/run-20261016T174447Z-b2adce4a` (focus *debugging failing GitHub Actions workflows*) succeeded technically. The human-review draft (`m8_review.md`, Analysis Quality) found:

- Analysis ran 18 searches, 0 unsuccessful, **0 rejected URLs, 0 new evidence** (`evidence_registry_delta` empty). No source was inspected in Analysis; every alternative is `unknown_gap` with no evidence IDs.
- A read-only comparison of the six verified sources found causes or workarounds **on the same pages** that Analysis recorded as unknown: EV-002 (root cause, fixed by PR #202), EV-005 (reporter's OOM finding), EV-006 (three workarounds in thread), EV-008 (accepted answer). Records said "unidentified" / `unknown_gap`.

Code cause (`analysis_agent/service.py:32-86`, `crew.py`):

1. `planner.plan()` produces the full plan, including `counterevidence_sources` and `alternatives[].source_urls`, **before any search runs**. The model cannot know real URLs, so it supplies none (here) or guesses ones the lead-membership guard rejects. This is the defect M9 fixed for Research.
2. Search leads are used only as a membership filter. `finalize()` receives inspected records only, never the leads.
3. The Analysis model sees each Research evidence item only through its excerpt (first 25 words, ≤280 chars; 130–163 chars here). It never sees the thread bodies where the resolution is stated, and Analysis does not re-open those pages.

**Root cause:** URL choice precedes search results, and the model's only view of existing sources is a 25-word opening. Not a model-capability claim; it is a boundary defect.

Not verified: the investigation plan itself is not persisted, so "no URLs requested" is inferred from `rejected=[]` + `delta=0`.

## 2. Scope

### Included
- **A. Lead-grounded selection.** Flow becomes `plan → search → select → accept → extract → finalize`. A new selection call receives the leads (`original_url`, `title`, `snippet`, `published_at`, grouped by query/purpose) and returns a flat list of `{source_url, evidence_class}` from those leads only. Deterministic acceptance: a selected URL must exactly match a lead URL; mismatches go to `diagnostics.rejected_source_urls` and become a research gap (existing behavior).
- **B. Fuller context for existing evidence (decision 2).** Before `finalize`, re-extract the URLs of Research's *verified* evidence items and pass the page text, truncated to a fixed cap per source, to `finalize` as **context records**. They are not added to the registry delta; `finalize` still cites the existing EV IDs. Without B, EV-002/005/006/008 stay invisible even when A works, because A selects *new* sources.
- `finalize` URLs (`source_urls`, `counterevidence_sources`) that are not among inspected records are recorded in `rejected_source_urls` instead of being silently dropped.
- Prompt changes: plan call must not propose source URLs; selection prompt (verbatim lead URLs, no quotas, "about N" upper guide, evidence_class vocabulary as in Research); finalize sentence that resolution/workaround claims need a supporting inspected record, otherwise `unknown_gap`.
- Tests (§5), written first.

### Non-goals
- No change to `AnalysisOutput`/evidence contracts, statuses, independence rules, Stage 1/2, Research, Evaluation, agent count or Flow order. No Analysis → Research loop. No new search vendor.
- No change to Research's 25-word excerpt policy for registry items (short faithful quotes are intended); B adds context, not longer stored excerpts.
- Not in this fix: zero-problem report failure; report wording/section issues (tracked separately).

## 3. Proposed approach

1. `models.py`: add `SourceSelection(_StrictModel)` with `sources: list[SourceRequest]` (reuses existing `SourceRequest`, `EvidenceClass`; no `minProperties`/dict-valued schema).
2. `service.py`:
   - `_discover` returns leads (url → query/purpose, title, snippet, published_at) instead of a URL set only.
   - New order in `run`: `plan` → `_discover` → `select_sources(research, investigation, leads)` → accept against lead URLs → add B context URLs → `_inspect` (one `extract` call, split into new vs. context records) → `finalize(research, investigation, new_records, context_records)` → `_assemble`.
   - `_assemble` keeps creating delta evidence only for new records; context records are lookup-only.
   - `finalize` URLs not in new records → `rejected_source_urls`.
   - If search returns no leads, skip selection (as Pass 2 skips when empty).
3. `crew.py`: add `select_sources` to the planner protocol/class; `finalize` takes context records separately and truncates each text to the cap.
4. `prompts.py`: as in §2.
5. Provisional constants: selection upper guide ~8 sources (not a quota); per-source context cap ~4,000 characters. Both are starting values, documented as such.

## 4. File change map

| Path | Change |
| --- | --- |
| `src/problem_discovery_agents/analysis_agent/models.py` | Add `SourceSelection`. |
| `src/problem_discovery_agents/analysis_agent/service.py` | New order, lead map, acceptance, context records, rejected finalize URLs. |
| `src/problem_discovery_agents/analysis_agent/crew.py` | `select_sources`; `finalize` with context records and truncation. |
| `src/problem_discovery_agents/analysis_agent/prompts.py` | Plan/selection/finalize wording. |
| `tests/test_analysis_agent.py` | Update fake planner for the new step; add tests below. |
| `tests/test_response_schemas.py` | Add `SourceSelection` to the schema guard. |

## 5. Tests (offline, fakes only; shown failing on current code first)

- **Order/grounding:** the fake planner's `select_sources` receives the leads returned by the fake search; a selected URL that is a lead is extracted and produces delta evidence (`EV-<next>`), linked from the alternative/counterevidence that cites it.
- **Rejection:** a selected non-lead URL is not extracted, appears in `rejected_source_urls`, and becomes a research gap.
- **Finalize drift:** a `finalize` URL absent from inspected records is recorded as rejected, not silently dropped.
- **No leads:** zero leads → selection not called, no extract call, output still valid.
- **Context records (B):** verified Research evidence URLs are extracted and passed to `finalize` truncated to the cap; they add **no** delta evidence and no duplicate IDs; unverified items are not re-extracted.
- **Plan prompt:** contains the no-URL instruction; selection prompt names the vocabulary; no quota wording.
- **Schema guard:** `SourceSelection` passes the OpenAI strict-schema scan.
- Full suite (`uv run pytest`) stays green (133 today).

## 6. Verification

1. Offline: new tests failing first, then the full suite; report results as run.
2. Staged Analysis-only check (needs authorization; Analysis-stage model + Tavily calls only): run Analysis on the saved Research output of `…b2adce4a` via the scratchpad probe. Pass criteria: non-empty `evidence_registry_delta` or an explicit rejected/unsuccessful record; for P-005 (EV-006) alternatives cite inspected evidence rather than `unknown_gap`. Compare P-001/004/005/006 against the current records.
3. Optional authorized full run, same focus, compared against `…b2adce4a` per the M8 fix/rerun log.

## 7. Risks and open decisions

- **Cost/latency:** one more model call plus up to ~8 new and ~6–12 context extractions per run. Search/extract cost remains unrecorded (unknown), as today.
- **Prompt size:** B adds up to cap × sources of text to `finalize`. The cap is a provisional value; revisit if truncation hides the answer.
- **Over-claiming risk:** more inspected text could push the model toward `corroborated`/`outdated` too eagerly. `corroborated` still requires ≥2 independent firsthand linked items (validator unchanged). EV-008 shows self-answers may look independent; independence stays the model's rationale to give and the reviewer's to check.
- **Possible second defect:** even with sources inspected, the model may still pick weak sources. The staged check will show it cheaply.
- **Decisions requested:** (1) approve A (lead-grounded selection). (2) Approve B (context records from verified Research evidence) now, or defer B and fix A only. Recommendation: both; A alone would not recover the four resolved/workaround cases found in review.

## 8. Approval boundary

Wait for explicit approval before any code, test or live run changes.
