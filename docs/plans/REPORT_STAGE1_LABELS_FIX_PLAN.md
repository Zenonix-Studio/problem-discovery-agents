# Fix Plan — Report Stage 1 Dimension Labels (targeted M8 correction)

**Status: proposed, not yet approved.** Small, single-cause correction following the M8 failure policy (fix only the responsible boundary, rerun, compare). Builds on M9 (`dd1bae1`) and the evidence-class fix (`34c24bf`). No production code, test or live run until this plan is approved; a live rerun additionally needs explicit authorization because it is paid.

## 1. Problem and evidence

Live run `artifacts/run-20261016T163719Z-e8b53313` (category *Developer Tools & Productivity*, focus *debugging failing GitHub Actions workflows*, 2026-10-16) passed Research (12 findings / 12 evidence, classes now from the closed vocabulary) and Analysis (7 problems, all `needs_validation`), then **failed at Evaluation**:

```text
Invalid Evaluation report: missing required report content:
Problem Reality, Frequency / Recurrence, Alternative Gap, Meaningful Benefit
```

A staged Evaluation-only re-run on the saved Research/Analysis outputs reproduced the identical error and let us inspect the rejected report (it is not persisted when validation fails):

- The report is complete otherwise: all seven required headings, a shortlisted card (P-003 … P-007 were scoreable, Stage 1 total 4/12 `Low priority`; P-001/P-002 `Research needed`), and the other five required labels (Alternatives, Counterevidence, Potential measurable outcome, Stage 2, Next validation) are present.
- The four Stage 1 dimension names never appear in display form. Instead the report contains the machine keys: `problem_reality` ×5, `frequency_recurrence` ×5, e.g. `problem_reality: Partial`.
- `build_report_context` (`evaluation_agent/report.py:22-31`) passes `evaluation.model_dump()`, so the model sees `stage1_scores` keyed `problem_reality`, `frequency_recurrence`, `alternative_gap`, `meaningful_benefit`.
- `REPORT_INSTRUCTIONS` only says "all four named Stage 1 assessments" and does not give the display labels.
- The validator `REQUIRED_REPORT_CONTENT` (`report.py:15-19`) does a case-sensitive substring match for `Problem Reality`, `Frequency / Recurrence`, `Alternative Gap`, `Meaningful Benefit`.
- The test fake `write_report` in `tests/test_evaluation_agent.py` hard-codes the exact display labels, so the real model's formatting was never exercised.

**Root cause:** the labels the validator requires are never given to the model; it mirrors the snake_case keys it is shown. This is a formatting-contract mismatch, not missing content. (My earlier hypothesis that no shortlisted cards existed was wrong; the probe disproved it.)

## 2. Scope

### Included
- Define one shared mapping of Stage 1 field name → display label in `evaluation_agent/report.py`, and derive the four dimension entries of `REQUIRED_REPORT_CONTENT` from it so the validator and the context cannot drift.
- In `build_report_context`, present each evaluation's `stage1_scores` keyed by display label (`"Problem Reality"`, `"Frequency / Recurrence"`, `"Alternative Gap"`, `"Meaningful Benefit"`) instead of the snake_case keys. Values are unchanged. The authoritative `EvaluationOutput` and its JSON contract are **not** touched.
- Add one sentence to `REPORT_INSTRUCTIONS` that names the four labels verbatim and requires each shortlisted card to use them as the assessment labels.
- Tests (§4), written first.

### Non-goals
- No change to scoring, labels/thresholds, Stage 2 gating, `EvaluationOutput`, Analysis, Research, agent count or Flow order.
- The validator is **not loosened** (no case-insensitive or snake_case acceptance): it stays the structural check that the report names the four assessments.
- Not part of this fix, listed for transparency:
  - **Zero-problem run:** with no problems, no card exists, so the per-card labels can never appear and Evaluation fails. A different cause (the validator requires card-level content when there are no cards). Needs its own failing test; see decision 1.
  - **Report classification quality:** the probe's report lists `Low priority` (4/12) problems under "Shortlisted problem cards", while the prompt expects Low priority records under "Rejected and inconclusive". Not a contract failure; note for the M8 `Report Usability` review.

## 3. Proposed approach

1. In `report.py` add `STAGE1_LABELS = {"problem_reality": "Problem Reality", "frequency_recurrence": "Frequency / Recurrence", "alternative_gap": "Alternative Gap", "meaningful_benefit": "Meaningful Benefit"}` and build the first four `REQUIRED_REPORT_CONTENT` entries from `STAGE1_LABELS.values()` (the other five labels stay as is).
2. In `build_report_context`, after `evaluation.model_dump(mode="json")`, rename the keys under each record's `stage1_scores` through `STAGE1_LABELS`. Do this on the dumped dict only, never on the model.
3. In `REPORT_INSTRUCTIONS`, add: each shortlisted problem card must label its four Stage 1 assessments exactly `Problem Reality`, `Frequency / Recurrence`, `Alternative Gap` and `Meaningful Benefit`, never the field names.

Why change the context rather than only the prompt: the model reproduced the keys it was shown, so the data it sees is the strongest lever; the prompt sentence is a second, cheap reinforcement. Together they stay deterministic on the input side, while the validator remains the final guard.

## 4. File change map

| Path | Change |
| --- | --- |
| `src/problem_discovery_agents/evaluation_agent/report.py` | Add `STAGE1_LABELS`; derive the four dimension entries of `REQUIRED_REPORT_CONTENT`; relabel `stage1_scores` keys in `build_report_context`. |
| `src/problem_discovery_agents/evaluation_agent/prompts.py` | One sentence naming the four labels in `REPORT_INSTRUCTIONS`. |
| `tests/test_evaluation_agent.py` | New tests below; existing tests unchanged. |

## 5. Tests (offline, fakes only; shown failing on current code first)

- **Context labels:** `build_report_context(...)["evaluations"]["evaluations"][i]["stage1_scores"]` has exactly the four display labels as keys and none of the snake_case names; scores and rationales are identical to the model's values.
- **Contract untouched:** the `EvaluationOutput` object (and its `model_dump`) still uses snake_case keys after `build_report_context` runs (no mutation).
- **Prompt:** `REPORT_INSTRUCTIONS` contains the four labels verbatim.
- **Realistic report:** a fake `write_report` that builds its card text from the *context it receives* (not hard-coded strings) passes `validate_report_markdown` — this exercises the same data path the real model sees, closing the gap that hid the bug.
- **Negative:** a report that uses only the snake_case keys still fails validation with the existing message (validator stays strict).
- Full suite (`uv run pytest`) stays green.

## 6. Verification

1. Offline: new tests, then the full suite. Report results as run.
2. Cheap staged check (needs authorization; Evaluation-only model calls, no Research/Analysis spend): re-run Evaluation on the saved outputs of run `…e8b53313` with the staged probe and confirm the report validates and uses the four display labels. Expected to pass the validator; the report's section placement quality is reviewed separately.
3. Authorized full run with the same focus; compare against `…e8b53313` and record resolved and newly introduced issues per the M8 fix/rerun log. If a later stage fails, treat it as a new single-cause investigation.

## 7. Risks and open decisions

- **Model may still use other wording** (for example "Problem reality"). The context relabel and verbatim instruction make this unlikely; the strict validator would still reject it, so a full run could fail after paid stages. If it recurs, consider a deterministic post-check/regeneration of only the report as a separate decision.
- **Display labels in context but snake_case in other fields** (`stage1_status`, `stage1_total`) remain; they are not validated, so left alone.
- **Decisions requested:** (1) keep the zero-problem report failure out of this plan and handle it as a separate fix (recommended: different cause, own test), or bundle it as a second item? (2) Approve the context-relabel + prompt-sentence approach with the validator staying strict.

## 8. Approval boundary

Wait for explicit approval before any code, test or live run changes.
