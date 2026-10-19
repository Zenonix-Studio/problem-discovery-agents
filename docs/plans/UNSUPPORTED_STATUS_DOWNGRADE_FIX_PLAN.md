# Fix Plan — Downgrade Unsupported Problem Status Claims Instead of Failing the Run (targeted M8 correction)

**Status: proposed, not yet approved.** Small, single-boundary correction following the M8 failure policy; direct sibling of `UNSUPPORTED_ALTERNATIVE_DOWNGRADE_FIX_PLAN.md` (committed `6c95a11`). No production code, test or live run until approved; a live rerun additionally needs explicit authorization because it is paid.

## 1. Problem and evidence

Live run `artifacts/run-20261019T132632Z-8ae597e2` (category *Developer Tools & Productivity*, focus *slow dependency installs in CI*, 2026-10-19), the first run after the alternative-downgrade fix: Research succeeded (15 findings, 10 evidence) and **Analysis failed on two status claims**:

```text
Problem P-001 is corroborated but lacks two linked independent firsthand Evidence IDs
Problem P-003 is contradicted but lacks linked counterevidence
```

- Manifest: `status: failed`, `completed_stage: research`, `failed_stage: analysis`. Usage: 108,459 input / 39,928 output tokens; dollar and search cost not reported by the provider. As before, the failed Analysis plan is not persisted.
- Rules (`validation.py:114-130`): `corroborated` requires at least two linked evidence items that are `independent` **and** `firsthand` in the merged registry; `outdated` and `contradicted` require at least one linked counterevidence ID.
- Mechanism (`analysis_agent/service.py` `_assemble`): `Problem.evidence_ids` comes straight from the model's `proposal.evidence_ids` (existing Research evidence IDs); `counterevidence_ids` only from `counterevidence_sources` URLs that resolve to newly inspected records. The model's `status` is passed through unchanged. If the model claims a status that these deterministic inputs do not support, the validator aborts the whole run.
- Same defect class as the alternatives: a model claim that the pipeline cannot support becomes a run-ending contract error instead of recorded uncertainty.

**Not verified:** why each claim lacked support (for example Research marked the evidence `uncertain`/`dependent`, or the counterevidence source URL was not an inspected lead). The downgrade covers every cause.

## 2. Scope

### Included
- In `AnalysisAgent._assemble`, after the problem's `evidence_ids` and `counterevidence_ids` are known and before `Problem(...)` is built, compute the status the evidence actually supports:
  - `corroborated` with fewer than two linked independent firsthand evidence items → `needs_validation`.
  - `outdated` or `contradicted` with no `counter_ids` → `needs_validation`.
  - Other statuses unchanged.
- On a downgrade add a note to the problem's `research_gaps` naming the claimed status and the missing support (for example: "Status was proposed as corroborated but fewer than two linked independent firsthand evidence items exist; recorded as needs_validation."), and record it in a new `AnalysisDiagnostics.downgraded_statuses` list as `P-xxx: …` (mirrors `downgraded_alternatives`).
- The independence/firsthand test reuses the same condition as the validator. To avoid two copies drifting apart, factor the condition into one small shared helper in `validation.py` used by both the validator and `_assemble` (reuse over re-implementation). `status_rationale` is not rewritten (the model's text stays as supplied; the gap note and diagnostics carry the correction).
- Tests (§4), written first.

### Non-goals
- The validator is **not** loosened: it still raises for any `corroborated`/`outdated`/`contradicted` claim in a final output that lacks support.
- Dangling references (unknown finding or evidence IDs) stay fail-fast: they are broken contracts, not weak facts.
- No change to prompts, contracts, statuses, Research, Evaluation, agent count or Flow order. No new evidence is fabricated; nothing is promoted, only downgraded.
- Not persisting the failed Analysis plan; not adding model-citable evidence IDs for alternatives (see the alternatives plan §6).

## 3. Proposed approach

1. `validation.py`: extract `independent_firsthand_ids(problem_evidence_ids, registry) -> list[str]` (the existing comprehension) and use it in `validate_analysis_output`.
2. `analysis_agent/models.py`: add `downgraded_statuses: list[str]` to `AnalysisDiagnostics`.
3. `analysis_agent/service.py` `_assemble`: build the merged registry view needed for the check (Research evidence plus the delta items created so far; independence and class of existing Research evidence is what matters, and new delta evidence is `uncertain`/class from selection), apply the two rules, extend `gaps` and diagnostics.
4. Nothing else.

Note on ordering: `_assemble` creates delta evidence lazily, so the check runs after the problem's alternatives and counterevidence are resolved, using the research registry plus `delta` accumulated so far.

## 4. Tests (offline, `tests/test_analysis_agent.py`; written first, failing on current code)

- **Corroborated without support is downgraded:** a planner claims `corroborated` for a problem whose linked evidence is only `uncertain` independence (the fixture's EV-003, or EV-001 with one independent item): `run` returns normally, status is `needs_validation`, `research_gaps` names the claim, `diagnostics.downgraded_statuses` has one entry. Fails today with `lacks two linked independent firsthand Evidence IDs`.
- **Corroborated with support is kept:** the existing default fixture (two independent firsthand items) stays `corroborated`, no note.
- **Contradicted/outdated without counterevidence is downgraded** (parametrized over both statuses, using a `counterevidence_sources` URL that is not a lead): `needs_validation` plus note. Fails today with `lacks linked counterevidence`.
- **Contradicted/outdated with a resolved counterevidence source is kept.**
- **`needs_validation` untouched:** no extra gap or diagnostic.
- **Validator still strict:** existing `test_finalization_cannot_claim_unsupported_status_or_alternative_gap` and the other validation tests stay unchanged and green; one added test calls the shared helper directly.
- Full suite (`uv run pytest`) stays green (167 today).

## 5. Verification

1. Offline: new tests failing first, then the full suite; report results as run.
2. Cheapest live check (needs authorization; Analysis-stage model + search calls only): run Analysis on the saved Research output of `…8ae597e2` with the scratchpad probe. It reveals which support was missing for P-001/P-003 through the diagnostics, without re-spending Research.
3. Authorized full rerun, same focus; compare with `…8ae597e2`. If a later stage fails, treat it as a new single-cause investigation.

## 6. Risks and open decisions

- **A third validator rule may still fire.** After statuses and alternatives, the Analysis validator has no other model-claim rules (the rest are reference checks that stay fail-fast); Evaluation has its own validators, not touched here. The next failing stage, if any, is a separate investigation.
- **Quiet loss of confidence.** The model's `status_rationale` may argue for the original status while the status is lower. The gap note and diagnostics make this visible; the human review checks it. Rewriting the rationale is not proposed.
- **Over-downgrading:** `corroborated` depends on Research's independence labels. If those are conservative (`uncertain`), statuses will rarely rise above `needs_validation`; that is the policy ("even `corroborated` is not validated demand"), but it means the rubric may show few strong problems. The diagnostics let us measure it.
- **Decision requested:** approve the status downgrade with the shared validator helper (recommended). Optionally decide separately whether to persist the failed Analysis plan on failure.

## 7. Approval boundary

Wait for explicit approval before any code, test or live run changes.
