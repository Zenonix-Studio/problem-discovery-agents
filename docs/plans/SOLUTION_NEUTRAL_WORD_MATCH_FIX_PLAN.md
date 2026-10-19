# Fix Plan — Whole-Word Matching in the Solution-Neutral Guard (targeted M8 correction)

**Status: proposed, not yet approved.** Small, single-cause correction following the M8 failure policy. No production code, test or live run until approved; a live rerun additionally needs explicit authorization because it is paid.

## 1. Problem and evidence

Live run `artifacts/run-20261019T130934Z-e424272c` (category *Developer Tools & Productivity*, focus *slow dependency installs in CI*, 2026-10-19) **failed in Research** before any source was analysed:

```text
1 validation error for CandidateSelection
candidates.8.friction_hypothesis
  Value error, friction_hypothesis must remain solution-neutral and unscored
  input_value='Fresh installs can fail ...ndency on a cache miss.'
```

- Manifest: `status: failed`, `failed_stage: research`; token usage tiny (528 input / 1,154 output); dollar and search cost not reported by the provider.
- Cause in code: `research_agent/models.py:78-83` (`CandidateSignal._solution_neutral`) rejects a hypothesis when any of `"solution"`, `"product"`, `"score"`, `"validated demand"` appears **as a substring** of the lowercased text.
- Offline reproduction (these innocent sentences are all rejected today): "dependency **resolution** hits a cache miss" (re**solution**), "slow down in **product**ion CI runs", "Developer **Product**ivity drops", "The **score**board is unclear".
- A scan of `src/` found no other banned-term list (`forbidden`/`solution`/`product`/`score` appear only here, in prompts, in agent goal text, and in Tavily's numeric `score` field).

**Root cause:** the guard checks substrings instead of words, so ordinary technical vocabulary (notably *dependency resolution*, central to this topic) aborts the whole run. One bad candidate out of 12+ kills the run.

**Not verified:** the exact word in the failing candidate. The log truncates the text and the rejected `CandidateSelection` is not persisted. "resolution" is the most likely trigger given the topic, but "production" / "productivity" are equally possible; all share the same defect and the same fix.

## 2. Scope

### Included
- In `CandidateSignal._solution_neutral`, match whole words with a compiled regex, case-insensitive: `solutions?`, `products?`, `scor(e|es|ed|ing)`, and the phrase `validated demand`. Same error message, same field, same strictness for real violations.
- Tests (§4), written first.

### Non-goals
- No change to the policy itself (no proposing solutions/products, no scores, no demand claims), to prompts, contracts, Research flow, or other models.
- Not loosening to "warn and continue", and not changing fail-fast behavior for real violations. Dropping a single non-compliant candidate instead of failing the run would be a separate decision (see §6).
- Not adding persistence of rejected model output (diagnosability gap noted in §6).

## 3. Proposed approach

In `research_agent/models.py`:

```python
_FORBIDDEN_TERMS = re.compile(r"\b(solutions?|products?|scor(?:e|es|ed|ing)|validated demand)\b", re.IGNORECASE)
...
if _FORBIDDEN_TERMS.search(value):
    raise ValueError("friction_hypothesis must remain solution-neutral and unscored")
```

Same file only; no new module or dependency.

## 4. Tests (offline, `tests/test_research_agent.py`; written first, failing on current code)

- **Innocent wording is accepted** (parametrized): "dependency resolution", "production CI runs", "developer productivity", "scoreboard", "the resolution of the lockfile fails" in a `friction_hypothesis`. Fails today on each.
- **Real violations still rejected** (parametrized): "The solution is a product.", "Solutions exist for this", "Users give it a score of 7", "validated demand exists", "a PRODUCT would fix it" (case-insensitive). Passes today and after.
- Existing `test_scope_and_solution_language_are_rejected` stays unchanged.
- Full suite (`uv run pytest`) stays green (152 today).

## 5. Verification

1. Offline: the new tests failing first, then the full suite; report results as run.
2. Authorized rerun with the same focus (*slow dependency installs in CI*): checks that Research passes and gives the first live exercise of the comment-fetching change. Compare with the failed run. If a later stage fails, treat it as a new single-cause investigation.

## 6. Risks and open decisions

- **Genuine uses of the words still trip the guard** (for example "product team", "health score" as a user complaint). That matches the policy's intent for a *hypothesis* and is rare; widening it is not part of this fix.
- **One violation still aborts the run.** With whole-word matching this becomes much rarer, but a model that truly writes "the solution is…" still kills a 12-candidate run. Option for a later decision: drop only that candidate and record it as a rejected candidate/gap. Not proposed here because it changes validation semantics.
- **Diagnosability:** the rejected model output is not persisted, so the exact offending word could not be read from the artifacts, only from truncated log text. Not addressed here.
- **Decision requested:** approve the whole-word regex fix only (recommended), and separately whether to later consider drop-the-candidate behavior.

## 7. Approval boundary

Wait for explicit approval before any code, test or live run changes.
