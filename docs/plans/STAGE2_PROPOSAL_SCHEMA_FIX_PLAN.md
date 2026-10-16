# Fix Plan — Stage 2 Proposal Schema Accepted by OpenAI Structured Output (targeted M8 correction)

**Status: proposed, not yet approved.** Small, single-cause correction following the M8 failure policy (fix only the responsible boundary, rerun, compare). Builds on M9 (`dd1bae1`), the evidence-class fix (`34c24bf`) and the report-label fix (`de3c96d`). No production code, test or live run until this plan is approved; a live rerun additionally needs explicit authorization because it is paid.

## 1. Problem and evidence

Live run `artifacts/run-20261016T172923Z-2eed52c6` (category *Developer Tools & Productivity*, focus *debugging failing GitHub Actions workflows*, 2026-10-16) passed Research and Analysis (4 problems; P-001 `corroborated`, the first time that status was reachable) and Evaluation Stage 1, then **failed on the Stage 2 model call**:

```text
Error code: 400 - Invalid schema for response_format 'Stage2ProposalBatch':
In context=('properties', 'assessments'), 'minProperties' is not permitted.
```

Phase 1 findings:

- `evaluation_agent/models.py:46`: `Stage2Proposal.assessments: dict[str, QualitativeAssessment] = Field(min_length=1)`. Pydantic emits `minProperties` for a dict `min_length` and a schema-valued `additionalProperties` for the dict values.
- A scan of every model-facing `response_format` schema (`PassPlan`, `CandidateSelection`, `AnalysisPlan`, `Stage1ProposalBatch`, `Stage2ProposalBatch`) found the problem **only** in `Stage2ProposalBatch`: the unsupported `minProperties`, plus a schema-valued `additionalProperties`, both at `/$defs/Stage2Proposal/properties/assessments`.
- Stage 2 is requested only when at least one problem is deterministically eligible (`Strong`/`Promising` with a user benefit). No earlier live run reached it, and all tests use fake agents, so OpenAI's schema acceptance was never exercised.
- The authoritative contract `Stage2Assessment.assessments` (`contracts.py:244`, same dict + `min_length`) is **not** sent to the model, so it does not cause this error.

**Root cause:** the model-facing proposal type uses a JSON-schema construct (`dict` with a minimum size) that OpenAI structured output rejects. Only the first violated keyword is reported (`minProperties`); the schema-valued `additionalProperties` may be a second rejection that cannot be confirmed without another call, so the fix removes both.

## 2. Scope

### Included
- Replace the model-facing `Stage2Proposal.assessments` dict with a list of small items, each with `dimension: str`, `value: Stage2Value`, `rationale: str`. The service converts the list into the existing `Stage2Assessment` dict, so `EvaluationOutput`, `Stage2Assessment`, validation and the report context keep their current shape.
- Deterministic checks in the service for the new shape (fail fast on a broken contract): an empty list, a blank `dimension`, or duplicate `dimension` names within one proposal raise `ContractValidationError`. Duplicates are rejected rather than silently overwritten when converting to a dict.
- Update `STAGE2_INSTRUCTIONS` to describe the list-item shape in one sentence (what a `dimension` is: a short name such as capability, maintainability, constraints, demonstrability, matching the existing prompt wording).
- A guard test that scans the JSON schema of every model-facing `response_format` type for constructs OpenAI strict structured output rejects, so this class of error cannot recur silently.
- Update existing tests that build `Stage2Proposal(assessments={...})` dicts to the list shape.

### Non-goals
- No change to Stage 1 scoring, labels/thresholds, Stage 2 eligibility gating, `EvaluationOutput`/`Stage2Assessment` contracts, report validation, Research or Analysis, agent count or Flow order.
- No fixed list of Stage 2 dimensions: Step 3 leaves "specific Stage 2 data fields" to the Step 4 contract decision, and Step 4 leaves them to the coding agent, so `dimension` stays a free, non-blank string.
- Not part of this fix: the zero-problem report failure and the report placing `Low priority` problems under "Shortlisted problem cards" (both tracked separately).

## 3. Proposed approach

1. In `models.py` add `Stage2Item(_StrictModel)` with `dimension`, `value: Stage2Value`, `rationale` (non-blank validators, like the existing ones) and change `Stage2Proposal.assessments` to `list[Stage2Item]` with no schema-level minimum.
2. In `service.py` `_attach_stage2`, before building `Stage2Assessment`, validate each proposal: non-empty list, non-blank and unique `dimension` (case-insensitive comparison to catch `Feasibility` vs `feasibility`), then build `{item.dimension: QualitativeAssessment(value=item.value, rationale=item.rationale)}`. Errors are collected into the existing `ContractValidationError` message style.
3. In `prompts.py` add the single sentence about the list-item shape to `STAGE2_INSTRUCTIONS`.
4. Add a test helper that recursively walks `model_json_schema()` and flags `minProperties`, `maxProperties`, `patternProperties`, `propertyNames` and any schema-valued `additionalProperties`; apply it to all model-facing response types.

## 4. File change map

| Path | Change |
| --- | --- |
| `src/problem_discovery_agents/evaluation_agent/models.py` | Add `Stage2Item`; `Stage2Proposal.assessments` becomes a list. |
| `src/problem_discovery_agents/evaluation_agent/service.py` | Validate and convert the list into the existing `Stage2Assessment` dict in `_attach_stage2`. |
| `src/problem_discovery_agents/evaluation_agent/prompts.py` | One sentence in `STAGE2_INSTRUCTIONS`. |
| `src/problem_discovery_agents/evaluation_agent/__init__.py` | Export `Stage2Item` only if tests need it (keep exports narrow). |
| `tests/test_evaluation_agent.py` | Migrate the three existing `Stage2Proposal(...)` usages to the list shape; add the new tests. |
| `tests/test_response_schemas.py` (new) | Schema-compatibility guard across all model-facing response types. |

## 5. Tests (offline, fakes only; shown failing on current code first)

- **Schema guard:** `Stage2ProposalBatch` has none of the rejected keywords. This fails today at `/$defs/Stage2Proposal/properties/assessments` and reproduces the live 400 offline. The same guard passes for `PassPlan`, `CandidateSelection`, `AnalysisPlan` and `Stage1ProposalBatch` (documents the scan result).
- **Conversion:** a proposal with items `capability` and `maintainability` becomes `Stage2Assessment.assessments` with those keys, values and rationales intact; `EvaluationOutput` JSON shape is unchanged.
- **Fail-fast:** empty list, blank dimension, and duplicate dimensions (including differing case) each raise `ContractValidationError`.
- **Existing behavior preserved:** Stage 2 is still attached only to eligible records, and ineligible/missing/duplicate proposal IDs still fail as before.
- Full suite (`uv run pytest`) stays green.

## 6. Verification

1. Offline: new tests, then the full suite. Report results as run.
2. Cheap staged check (needs authorization; Evaluation-only model calls): re-run Evaluation on the saved Research/Analysis outputs of run `…2eed52c6` with the staged probe; confirm the Stage 2 call is accepted by OpenAI and the report validates. Research and Analysis are not re-spent.
3. Authorized full run with the same focus; compare against `…2eed52c6` and record resolved and newly introduced issues per the M8 fix/rerun log. If a later stage fails, treat it as a new single-cause investigation.

## 7. Risks and open decisions

- **A second schema rejection is possible.** If OpenAI rejects another construct, the staged Evaluation-only check surfaces it cheaply; the guard test would then be extended with that keyword.
- **Free-form `dimension` names** may vary between runs. Acceptable for a qualitative Stage 2 (records are human-reviewed); fixing a closed set of dimensions is a separate contract decision.
- **Decision requested:** approve the list-item shape with free-form, non-blank, case-insensitively unique `dimension` names, and the guard test across all response types.

## 8. Approval boundary

Wait for explicit approval before any code, test or live run changes.
