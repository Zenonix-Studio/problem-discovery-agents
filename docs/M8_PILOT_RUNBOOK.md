# M8 Pilot Runbook

Use this runbook only for the first authorized **Developer Tools & Productivity** pilot. It is a human review procedure, not an automatic acceptance mechanism or a product-selection process.

## 1. Preconditions

- M8 documentation/template changes and offline checks have been completed.
- A human has authorized the networked, potentially paid run and chosen whether to provide an optional workflow focus.
- A local, uncommitted `.env` (or equivalent environment) supplies nonblank `PDA_GITHUB_TOKEN`, `PDA_TAVILY_API_KEY`, and `PDA_LLM_API_KEY`. Do not place values in this document, an artifact, or a commit.
- The category is exactly `Developer Tools & Productivity`. No other category is in scope.

Run the non-network configuration check first. It validates local configuration only; it does not prove provider entitlement or remote model availability.

```text
uv run python -m problem_discovery_agents.config_check
```

## 2. Execute one authorized pilot

With no preselected workflow focus, run:

```text
uv run python -m problem_discovery_agents.run \
  --category 'Developer Tools & Productivity'
```

If a human explicitly authorized a focus, append `--focus '<approved focus>'`. Do not use a focus to presuppose a problem. The command creates a unique directory under `artifacts/` unless `--output-dir` was specified.

Record the exact command, start date/time, focus choice, and returned run directory in the review record. A non-zero exit or a manifest whose status is not `succeeded` is an operational failure, not a completed semantic pilot review. Preserve its safe artifacts/manifest and report the failure; do not fabricate later-stage review results.

## 3. Confirm a successful artifact set

For a successful run, inspect `run_manifest.json` and confirm it names status `succeeded` and that the run directory contains all of:

- `research_output.json`
- `analysis_output.json`
- `evaluation_output.json`
- `evidence_registry.json` — the authoritative merged registry
- `report.md`
- `run_manifest.json`

Copy the review template into this completed run directory before reviewing. It is a human-authored supplement; do not alter the generated JSON, report, or manifest.

```text
cp docs/templates/M8_PILOT_REVIEW_TEMPLATE.md artifacts/<run-id>/m8_review.md
```

Do not create a review record for missing downstream artifacts as if they were produced.

## 4. Audit every problem record

Create exactly one audit-table row in `m8_review.md` for every `Problem ID` in `analysis_output.json`, including `needs_validation`, `outdated`, `contradicted`, Low priority, and `Research needed` records. If there are no problems, explicitly record that fact; do not create fictional rows.

For each row, trace **Evaluation → Problem → Finding/Evidence → original URL**. Open accessible original sources and compare their content/context and any excerpt with the recorded observation. An inaccessible source, unavailable excerpt, incomplete extraction, unknown date, or uncertain independence remains a limitation; a search snippet is never upgraded to verified firsthand evidence.

Review at least the following for each problem:

- evidence relationship (`independent`, `dependent`, or `uncertain`) and its rationale, separately from problem status;
- solution-neutral statement, constituent findings, and merge/split rationale;
- built-ins, other tools, actual workarounds, supported versus unknown gaps, fixes/current-version context, and counterevidence;
- all four Stage 1 rationales and cited Evidence IDs. Reality `3` requires direct technical verification beyond independent firsthand reports; Alternative Gap `3` requires strong firsthand unmet-need evidence; Meaningful Benefit `3` requires concrete impact and a measurable outcome;
- partial-score behavior: any unscoreable dimension must yield no `/12` total and no Stage 2; and
- correct, non-misleading treatment in `report.md`, including retained inconclusive/rejected records and stated limitations.

## 5. Record the five acceptance verdicts

Complete every criterion in `m8_review.md` with exactly `Pass` or `Fail` and a brief evidence-based rationale:

1. Evidence Integrity
2. Research Quality
3. Analysis Quality
4. Evaluation Consistency
5. Report Usability

Name unresolved uncertainty, coverage gaps, access failures, and targeted validation questions even when a criterion passes. A successful Flow or test suite cannot itself pass these human criteria. A passing M8 review is not validation of product demand and does not authorize another category or product work.

## 6. Failed review: targeted correction and comparison

If any criterion fails, first preserve the completed review record and copy the conditional log:

```text
cp docs/templates/M8_FIX_RERUN_LOG_TEMPLATE.md artifacts/<run-id>/m8_fix_rerun_log.md
```

Record the failed criterion, a concrete Problem/Finding/Evidence example, the one responsible prompt/tool/retrieval/schema/validator/agent boundary, and the smallest proposed correction. Do not automatically rerun, add an agent/provider/platform, broaden scope, or change research categories.

After separate approval for the correction and a separately authorized rerun, complete a new review record for the new run directory. Use the fix/rerun log to compare the original and rerun: identify resolved issues, remaining issues, and newly introduced quality issues.
