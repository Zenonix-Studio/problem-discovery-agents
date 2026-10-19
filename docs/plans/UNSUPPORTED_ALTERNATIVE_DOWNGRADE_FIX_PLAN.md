# Fix Plan — Downgrade Unsupported Alternative Gap Claims Instead of Failing the Run (targeted M8 correction)

**Status: proposed, not yet approved.** Small, single-boundary correction following the M8 failure policy. No production code, test or live run until approved; a live rerun additionally needs explicit authorization because it is paid.

## 1. Problem and evidence

Live run `artifacts/run-20261019T131536Z-47bca673` (category *Developer Tools & Productivity*, focus *slow dependency installs in CI*, 2026-10-19): Research succeeded (16 findings, 11 evidence, 14 workflows examined, no unsuccessful search; comment fetching worked live and its truncation notes reached the registry limitations). **Analysis then failed**:

```text
Contract validation failed:
Problem P-001.alternative[uv-based Python CI workflow] has need_substantially_met without linked Evidence IDs;
Problem P-003.alternative[Playwright Docker image or containerized workflow] has need_substantially_met without linked Evidence IDs
```

- Manifest: `status: failed`, `completed_stage: research`, `failed_stage: analysis`. Usage this run: 115,914 input / 43,278 output tokens; dollar and search cost not reported by the provider. Only `research_output.json` and the manifest were written; the Analysis plan is not persisted, so the proposed alternatives cannot be inspected.
- Mechanism (read from `analysis_agent/service.py`): `_assemble` builds `Alternative.evidence_ids` only from `AlternativeProposal.source_urls` that resolve to **newly inspected** records. The validator (`validation.py:139-145`) requires evidence IDs for `supported_gap` and `need_substantially_met`. If the model claims either outcome but its `source_urls` are empty, are not leads, or point at a source Research already registered (such URLs are excluded from new inspection, and `AlternativeProposal` has no field for existing evidence IDs), no ID is linked and the validator aborts the whole run.
- The prompts already tell the model: "A supported gap needs direct support; otherwise use unknown_gap." The model did not follow it, and the deterministic code has no step that enforces it before the validator.

**Root cause:** a model claim that the deterministic pipeline cannot support turns into a run-ending contract error. Weak or missing support should be recorded as uncertainty (`AGENTS.md`: do not fail a run because real-world facts are weak or missing).

**Not verified:** which of the three source situations above occurred for these two alternatives.

## 2. Scope

### Included
- In `AnalysisAgent._assemble`, after resolving an alternative's evidence IDs: if `gap_outcome` is `supported_gap` or `need_substantially_met` and no evidence ID resolved, set `gap_outcome` to `unknown_gap` and add a research gap to that problem naming the alternative and the original claimed outcome (for example: "Alternative 'X' was proposed as need_substantially_met but no inspected source supports it; recorded as unknown_gap."). The downgrade is also counted in the Analysis diagnostics (a small list `downgraded_alternatives` on `AnalysisDiagnostics`, so reviewers can see it).
- Tests (§4), written first.

### Non-goals
- The validator is **not** loosened: `validate_analysis_output` still raises for any `supported_gap`/`need_substantially_met` without evidence IDs. The downgrade happens before it, in assembly.
- No change to contracts, statuses, prompts, Research, Evaluation, agent count or Flow order.
- Not adding an `evidence_ids` field to `AlternativeProposal` so the model can cite existing Research evidence for an alternative. That is a possible follow-up if the downgrade fires often on well-supported alternatives (§6).
- Not persisting the failed Analysis plan (§6).

## 3. Proposed approach

1. `analysis_agent/models.py`: add `downgraded_alternatives: list[str]` (default empty) to `AnalysisDiagnostics`.
2. `analysis_agent/service.py`, in the alternatives loop of `_assemble`: compute `ids`, then, if the outcome claims support and `ids` is empty, use `GapOutcome.UNKNOWN_GAP`, append the message to the problem's gaps and to `diagnostics.downgraded_alternatives`. Gap ordering and everything else stay as is.
3. Nothing else.

## 4. Tests (offline, `tests/test_analysis_agent.py`; written first, failing on current code)

- **Downgrade instead of failure:** a planner whose `finalize` returns an alternative with `need_substantially_met` and no resolvable source URL (empty list, a non-lead URL, and a URL already in the Research registry as three cases): `run` returns normally, the alternative is `unknown_gap`, the problem's `research_gaps` names the alternative and claimed outcome, and `diagnostics.downgraded_alternatives` records it. Fails today with the contract error above.
- **Supported claims survive:** an alternative with a resolvable inspected URL keeps `need_substantially_met` and its evidence ID; no downgrade note.
- **`unknown_gap` untouched:** no extra gap or diagnostic entry.
- **Validator still strict:** the existing `test_finalization_cannot_claim_unsupported_status_or_alternative_gap` stays unchanged and green.
- Full suite (`uv run pytest`) stays green (162 today).

## 5. Verification

1. Offline: the new tests failing first, then the full suite; report results as run.
2. Cheapest live check (needs authorization; Analysis-stage model + search calls only): run Analysis on the saved Research output of `…47bca673` with the scratchpad probe. It shows which situation occurred, since `downgraded_alternatives` and `rejected_source_urls` will be visible, without re-spending Research.
3. Authorized full rerun with the same focus; compare with `…47bca673`. If a later stage fails, treat it as a new single-cause investigation.

## 6. Risks and open decisions

- **Masking a prompt/selection problem:** if the downgrade fires often, the real cause is upstream (selection choosing no usable sources, or existing evidence not citable). The diagnostics line makes this visible; the follow-up would be the `evidence_ids` field or a prompt change, decided from data.
- **Reviewers see fewer supported alternatives.** Intended: unsupported support claims were never acceptable evidence.
- **Failed-stage diagnosability:** the Analysis plan and diagnostics are lost when Analysis fails validation. A small separate change could persist them under the run directory on failure. Not included.
- **Decision requested:** approve the downgrade-in-assembly fix with a diagnostics entry (recommended). Optionally also decide whether to persist failed-stage Analysis output as a separate plan.

## 7. Approval boundary

Wait for explicit approval before any code, test or live run changes.
