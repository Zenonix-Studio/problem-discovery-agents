# Fix Plan — Controlled `evidence_class` Vocabulary (targeted M8 correction)

**Status: proposed, not yet approved.** This is a small, single-cause correction, so it has no separate milestone brief. It follows the M8 failure policy (fix only the responsible boundary, rerun, compare) and builds on M9 (`dd1bae1`).

## 1. Problem and evidence

Live run `artifacts/run-20261016T160833Z-f68aef61` (category *Developer Tools & Productivity*, focus *debugging failing GitHub Actions workflows*, 2026-10-16) passed Research (16 findings, 13 verified evidence items, all direct issue URLs) and then **failed at Analysis**:

```text
Problem P-002/P-004/P-005 is corroborated but lacks two linked independent firsthand Evidence IDs
```

A staged Analysis-only re-run on the saved `research_output.json` reproduced the same class of failure (P-001/002/003/004/006), so it is not a one-off.

Phase 1 findings:

- `validation.py:116-125` requires, for `corroborated`, at least two linked evidence items with `independence == independent` **and** `evidence_class == "firsthand"` (exact string).
- `evidence_class` is a free-text `str` (`contracts.py:88`). Research copies the model-supplied value from `CandidateSignal.evidence_class` (`research_agent/models.py:63`, default `"firsthand"` but model-overridable) into the registry (`research_agent/service.py:276`). Analysis does the same through `SourceRequest.evidence_class` (`analysis_agent/models.py:29`).
- In the live registry the 13 values were `GitHub issue lead` ×9 and `issue_or_pull_request` ×4. **None was `"firsthand"`**, so `corroborated` was unreachable regardless of how good the evidence was.
- Offline check on the saved output: relabelling all `evidence_class` values to `firsthand` reduces the failure from five problems to one. The remaining one (P-006: one `uncertain` + one `independent` source, labelled `corroborated`) is a genuine model over-claim that the validator correctly rejects.
- Every existing test hard-codes `evidence_class="firsthand"`, which is why the vocabulary mismatch was never exercised.

**Root cause:** the contract leaves the vocabulary undefined (Step 4 only lists "Firsthand, documentation, technical verification, etc.") while a deterministic rule depends on one exact value. The validator is correct; the model-facing fields are unconstrained.

## 2. Scope

### Included
- Define one shared, closed vocabulary for the model-proposed class: `firsthand`, `documentation`, `technical_verification`. (`unverified_source_lead` remains a system-assigned value for inaccessible sources and is never model-chosen.)
- Use it as a `Literal`/enum on the two **model-facing** fields (`CandidateSignal.evidence_class`, `SourceRequest.evidence_class`) so CrewAI structured output cannot return free text.
- Make `validation.py` compare against the shared constant instead of a bare `"firsthand"` string.
- Give the selection and Analysis prompts one-line definitions of each class (what counts as `firsthand`: the author describes their own experience; `documentation`: vendor/maintainer docs or release notes; `technical_verification`: reproducible technical check of the behavior).
- Tests (see §5) including a regression test with the real-world free-text values.

### Non-goals
- No change to `EvidenceItem.evidence_class` type or to stored artifacts' readability: it stays a non-blank `str`, so existing artifacts and fixtures still load. (Tightening it is a separate decision.)
- No change to the independence logic, scoring, Stage 1/2, Evaluation, the `corroborated` rule itself, agent count or Flow order.
- No change to the report validator for zero problems (separate known follow-up).
- No live run as part of implementation; a rerun needs separate human authorization.

## 3. Proposed approach

1. Add the vocabulary to `contracts.py` (e.g. `EvidenceClass = Literal["firsthand", "documentation", "technical_verification"]` and a constant `FIRSTHAND = "firsthand"`), exported where the research and analysis models import it.
2. Retype `CandidateSignal.evidence_class` and `SourceRequest.evidence_class` with it; keep the current defaults (`"firsthand"` / `"documentation"`).
3. In `validation.py`, replace the literal with the constant. Behavior unchanged for valid data.
4. Prompts: add the three one-line definitions to `SELECTION_INSTRUCTIONS` and `ANALYSIS_INSTRUCTIONS`. Add one sentence to the Analysis instructions: use `corroborated` only when at least two linked evidence items are independent firsthand; otherwise use `needs_validation` (this targets the P-006 over-claim; the deterministic check still decides).
5. The assembly code paths (`research_agent/service.py:276`, `analysis_agent/service.py:170`) already pass the model value through, so they need no change beyond typing.

## 4. File change map

| Path | Change |
| --- | --- |
| `src/problem_discovery_agents/contracts.py` | Add `EvidenceClass` literal and `FIRSTHAND` constant. |
| `src/problem_discovery_agents/research_agent/models.py` | Type `CandidateSignal.evidence_class` with it. |
| `src/problem_discovery_agents/analysis_agent/models.py` | Type `SourceRequest.evidence_class` with it. |
| `src/problem_discovery_agents/validation.py` | Compare against the constant. |
| `src/problem_discovery_agents/research_agent/prompts.py`, `analysis_agent/prompts.py` | Class definitions; `corroborated` threshold sentence. |
| `tests/test_research_agent.py`, `tests/test_analysis_agent.py`, `tests/test_validation.py` | New/updated tests (§5). |

## 5. Tests (all offline, fakes only)

Written first; each must be shown failing on the current code before the change.

- Research model rejects a free-text class: `CandidateSignal(..., evidence_class="GitHub issue lead")` raises a validation error; the three allowed values are accepted.
- Analysis model rejects a free-text class in `SourceRequest`.
- Validator regression: a `corroborated` problem linked to two independent evidence items with `evidence_class` from the vocabulary passes; one independent + one uncertain still fails with the existing message (keeps the P-006 behavior covered).
- Prompt text contains the three class definitions and the `corroborated` threshold sentence.
- Existing suites still pass (`uv run pytest`).

## 6. Verification

1. Offline: focused tests, then the full suite. Report results as run.
2. Cheap staged check (needs authorization, small cost): re-run **Analysis only** on the saved `research_output.json` of run `…f68aef61`, which still carries the old free-text classes. It should *not* be expected to pass, since that registry predates the fix; this step only confirms nothing else regressed. The meaningful check is item 3.
3. Authorized full run with the same focus. Success: Research output has `evidence_class` values only from the vocabulary; Analysis either completes, or fails only on a genuine independence over-claim (as P-006) that is then handled as a separate decision. Compare against run `…f68aef61` and record resolved and newly introduced issues per the M8 fix/rerun log.

## 7. Risks and open decisions

- **Classification happens before inspection.** The selection step sees only title/snippet, so `firsthand` is the model's guess about a lead, then the validator treats it as fact. This conflicts in spirit with "snippets are leads, not evidence". Accepted for this fix (smallest change); the human M8 review must check `evidence_class` against the actual excerpt. A later, separate option is to assign the class after extraction from the original text.
- **Over-claimed `corroborated` can still fail the whole run** (AGENTS.md: broken contract → fail fast). The prompt sentence reduces but does not eliminate it. Decision for the human: if it keeps recurring, consider downgrading to `needs_validation` deterministically instead of failing. Not part of this fix.
- **Model may still pick `documentation` for issues.** Mitigated by the definitions; visible in the next live run.
- **Existing artifacts** keep loading because the registry field stays a string.

**Decision requests:** (1) approve the three-value vocabulary, (2) approve including the `corroborated` threshold sentence in this change or defer it.

## 8. Approval boundary

No production code, test or live run until this plan is approved. A live rerun additionally needs explicit authorization because it is paid.
