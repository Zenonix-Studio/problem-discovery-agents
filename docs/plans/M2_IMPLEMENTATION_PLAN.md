# M2 Implementation Plan — Data Contracts & Deterministic Validation

## 1. Milestone goal and source references

**Goal:** introduce the smallest typed, serializable contracts and deterministic validators that future Research, Analysis, and Evaluation milestones can share. The implementation must preserve one authoritative evidence registry, end-to-end ID traceability, legitimate real-world uncertainty, and the four-dimension Stage 1 `/12` gate.

This plan implements only [M2 — Data Contracts & Deterministic Validation](../milestones/M2_data_contracts_deterministic_validation.md), specifically its **Objective**, **In scope**, **Out of scope**, and **Acceptance checks**. The governing sources are:

- `AGENTS.md` — **Data contracts and provenance**, **Stage 1: mandatory user-value gate**, and **Deterministic checks and error behavior**.
- `docs/Problem_Discovery_Step4_Implementation_Contracts_Decisions.md` — §3.1–§3.6 (registry, conceptual handoffs, and fail-fast policy).
- `docs/Problem_Discovery_Step3_Evaluation_Rubric_Decisions.md` — §§2–6 (the authoritative score values, `/12` labels, partial scoring, rationale/reference rules, and Stage 2 gate).
- `docs/Problem_Discovery_Step2_Analysis_Rules_Decisions.md` — §§2–6 (problem statuses, clustering/provenance, alternatives, and counterevidence handoff).
- `docs/Problem_Discovery_Research_Agent_Guide.md` — §§3–5 and 9 (evidence provenance, uncertainty, and user-value policy).
- `docs/Problem_Discovery_Workflow_Architecture_v1.md` — §§3–5 (three-agent handoffs and intermediate JSON traceability).

## 2. Scope and non-goals

### Included

- Pydantic contracts for evidence, evidence registry, research findings/output/coverage, analyzed problems/output, evaluation records/output, alternatives/counterevidence, score assessments, validation gaps, and Stage 2 assessment records.
- Stable, nonblank Evidence, Finding, and Problem IDs; a single registry referenced by downstream IDs rather than copied evidence objects.
- Safe registry merge/add semantics that reject duplicate/conflicting Evidence IDs and preserve existing canonical entries.
- Deterministic structural/reference validation across `ResearchOutput`, `AnalysisOutput`, and `EvaluationOutput`.
- Deterministic Stage 1 total/label derivation and Stage 2 eligibility validation, with exactly four dimensions: Problem Reality, Frequency / Recurrence, Alternative Gap, and Meaningful Benefit.
- JSON-compatible serialization round trips and focused tests/representative fixtures for valid, invalid, partial, and merged records.

### Explicitly excluded

- CrewAI agents, prompts, Flow wiring, external search/retrieval tools, live API calls, persistence/run-directory policy, final report generation, or actual research data.
- Semantic verification that a source is truthful, an excerpt is faithful, evidence is genuinely independent, a cluster is correct, or a model-selected score meets its rubric anchor. Validators enforce only machine-checkable contracts.
- Product proposals, a database, UI/dashboard, scheduler, additional agents, automatic analysis-to-research reruns, and a generalized validation framework.

## 3. Current repository state and dependencies

M1 is complete and committed (`1a42464`). It supplies the Python 3.11–3.13 package foundation, Pydantic settings dependency, conventional `src/` layout, pytest configuration, and the one shared configurable model boundary. The tracked working tree is clean.

No M2 domain model, evidence registry, output schema, JSON fixture, validator, score calculator, or artifact persistence code exists. `pydantic-settings` already brings Pydantic into the runtime dependency graph, so M2 should use that installed Pydantic version rather than introduce another schema/validation library. M2 must not make settings or credentials a precondition for contract-only tests.

## 4. Proposed technical approach

### Contract module and value vocabulary

**Delegated choice, recommended:** add one focused `contracts.py` module using Pydantic `BaseModel` and `str` enums. It should define the transport/domain shapes used at all three future handoffs while avoiding agent-specific behavior. Use semantic enum values required by policy:

- evidence independence: `independent`, `dependent`, `uncertain`;
- verification status: `verified`, `partial`, `unverified`;
- analysis status: `corroborated`, `needs_validation`, `outdated`, `contradicted`;
- Stage 1 classification: `Strong`, `Promising`, `Low priority`, `Research needed`;
- Stage 2 qualitative values: `Strong`, `Partial`, `Weak`, `Unknown`.

Required textual fields will reject blank/whitespace-only values. Dates will use `date` (not timestamps) for `published_at` and `accessed_at`; publication date remains nullable, while access date is required. `source_excerpt`, `interpretation`, and other policy-approved unknowns remain nullable/optional. Evidence keeps `observation` distinct from optional `interpretation`, and `verification_status` distinct from the Analysis resolution/current-status fields.

To keep M2 narrowly scoped, use one simple ID rule per namespace (a nonblank string with a documented recommended prefix such as `EV-`, `F-`, `P-`), rather than overfitting a sequence/format that later agents cannot satisfy. Uniqueness is enforced by the owning collection/registry.

### Authoritative registry and handoff records

Model the registry as an ID-keyed collection with explicit `add`/`merge` operations. The operations must be atomic from the caller's perspective: validate all incoming IDs first, reject a duplicate within the incoming collection or a conflict with an existing ID, and leave the original registry unchanged on failure. An existing ID is never silently overwritten—even if most fields happen to match—so deduplication remains an explicit producer decision.

`ResearchOutput` owns the initial registry and stores findings as Evidence-ID references. `AnalysisOutput` accepts its linked finding IDs and problem records plus a registry delta; a merge helper will combine that delta with the authoritative Research registry before cross-output validation. It must not embed copied `EvidenceItem` objects within findings, problems, alternatives, or score assessments. `EvaluationOutput` stores `problem_id` references and four named score assessments with Evidence-ID references.

Supporting records should make the mandated provenance visible without designing future agent behavior: research coverage/gaps, alternatives/workarounds with a supported/unknown/substantially-met gap outcome and evidence IDs, counterevidence/current-resolution notes, clustering/status rationale, and validation gaps. The exact field names remain implementation choices, but all required Step 4 concepts must be representable.

### Deterministic validator boundary

**Delegated choice, recommended:** add `validation.py` for cross-object rules and a small domain-specific `ContractValidationError` that aggregates actionable violations. Model-level Pydantic errors remain appropriate for local malformed data; this validator handles relationships and derived state that cannot be validated in a single model.

The validator will:

1. Check unique Evidence/Finding/Problem IDs and resolve all Finding → Evidence, Problem → Finding/Evidence, and Evaluation → Problem/Evidence references against the supplied authoritative records.
2. Require a nonblank rationale for every one of the four assessments. A scored assessment must have at least one resolvable Evidence ID. An unscoreable assessment must retain any available Evidence IDs; an empty reference list is valid only when it has a nonblank, specific evidence gap and targeted next validation action explaining why no supporting evidence can be cited. Retain counterevidence without attempting to judge its content.
3. Accept each Stage 1 score as either an integer in `{0,1,2,3}` or an explicit unscoreable state. Never coerce a missing/unknown score to `0`.
4. Recompute the total and classification in Python only: all four scored gives `10–12 Strong`, `7–9 Promising`, or `0–6 Low priority`; any unscoreable dimension gives `Research needed` and no total.
5. Reject caller-provided totals/statuses that disagree with the computed values, and reject a Stage 2 assessment unless the fully scored computed status is `Strong` or `Promising` and a nonblank user benefit is present.

No validator will reject a record solely because evidence is weak, contradictory, unavailable, unverified, or only supports `needs_validation`; those are represented as source limitations, analysis status, validation gaps, or unscoreable Stage 1 dimensions.

### Serialization seam

Use Pydantic’s JSON APIs for canonical model serialization/deserialization. Provide small, explicit serialization helpers only if they prevent callers from bypassing validation; do not select final run-directory filenames or add artifact persistence before M7. Fixtures will be static, secret-free JSON under `tests/fixtures/contracts/` and represent contract examples, not research claims.

## 5. File change map

All production paths below are proposed for implementation after approval.

| Path | Change | Purpose |
| --- | --- | --- |
| `src/problem_discovery_agents/contracts.py` | Create | Pydantic models/enums for registry, handoffs, provenance/supporting records, scores, and Stage 2 data. |
| `src/problem_discovery_agents/validation.py` | Create | Registry merge, cross-output ID/ref checks, deterministic score/label computation, and Stage 2 gate. |
| `src/problem_discovery_agents/__init__.py` | Update if useful | Expose only stable top-level contract/validation entry points; avoid a broad public API. |
| `tests/test_contracts.py` | Create | Field optionality, enums, nonblank fields, JSON round trips, and ID uniqueness cases. |
| `tests/test_evidence_registry.py` | Create | Atomic registry add/merge, duplicate/conflict rejection, and no silent overwrite behavior. |
| `tests/test_validation.py` | Create | Cross-handoff references, score boundaries, partial scoring, computed-state consistency, and Stage 2 eligibility. |
| `tests/fixtures/contracts/*.json` | Create | Small representative valid research/analysis/evaluation and malformed-reference JSON inputs. |
| `README.md` | Update | State that M2 contracts/validators now exist, explain their non-semantic boundary, and give the test command. |
| `docs/plans/M2_IMPLEMENTATION_PLAN.md` | Create | Approved implementation reference; no runtime behavior. |

## 6. Ordered implementation tasks

1. Reconfirm M1’s installed Pydantic API and establish the minimal model/enum layout; do not add dependencies unless a verified incompatibility requires it.
2. Define shared enum/value objects and the evidence registry with required provenance fields, allowed nullable fields, nonblank validation, and JSON-friendly dates.
3. Add finding/coverage and research-output models that reference registry IDs only.
4. Add analysis models for problems, clustering, alternatives/workarounds, counterevidence/current-resolution uncertainty, gaps, and the four approved problem statuses; model analysis registry additions as a delta that must merge into the same registry.
5. Add evaluation models with exactly the four named Stage 1 dimensions, score-or-unscoreable assessments, derived total/status fields, Stage 2 data, and non-scored validation/user-access context.
6. Implement atomic registry merging and cross-record integrity validation; surface duplicate/dangling/conflicting IDs as actionable contract failures.
7. Implement the pure deterministic Stage 1 classification and Stage 2 eligibility functions, then make output validation compare stored derived values against them.
8. Add minimal JSON fixtures and focused tests, including success paths and all M2 acceptance failure modes. Run the M1 and M2 tests together; update README only with verified commands/behavior.

## 7. Test and verification plan

Unit tests, with no credentials or network access:

- Evidence accepts nullable publication date/excerpt/interpretation but requires URL, source type, access date, observation, evidence class, independence rationale, verification status, and limitations.
- Invalid enum values, blank required strings, duplicate IDs within each namespace, and duplicate Evidence IDs in an incoming merge fail with clear errors.
- Registry merge accepts new nonconflicting Evidence IDs, rejects any existing/incoming conflict, and leaves the prior registry unchanged on rejection.
- A valid Research → Analysis → Evaluation chain resolves every ID down to an original source URL; each dangling Evidence/Finding/Problem reference fails.
- Every score `0`, `1`, `2`, and `3` is accepted only with a nonblank rationale and resolvable evidence references; invalid numeric values and unreferenced IDs fail.
- Fully scored totals at `0`, `6`, `7`, `9`, `10`, and `12` yield the exact required labels; stored totals/labels that disagree are rejected.
- One unscoreable Stage 1 dimension preserves other defensible scores but results in `Research needed`, `stage1_total is None`, and no Stage 2 assessment. Test that every unscoreable assessment has a rationale, preserves any available Evidence IDs, and—when none exist—requires a specific evidence gap plus targeted next validation action.
- Stage 2 is accepted only for fully scored `Strong`/`Promising` output with an articulable user benefit; reject `Low priority`, `Research needed`, absent benefit, or a non-null Stage 2 object where forbidden.
- Verified/partial/unverified source verification and analysis resolution/status are independently representable; weak, contradictory, or missing real-world evidence does not itself cause a schema failure.
- Pydantic JSON serialization/deserialization retains IDs, nullable values, enum values, and dates without copying registry entries into downstream records.

Run `uv run pytest` for the complete suite. The M2 test suite must run with no `.env`, credentials, provider construction, HTTP request, or CrewAI invocation.

## 8. Acceptance matrix

| M2 acceptance check | Observable verification action | Expected result |
| --- | --- | --- |
| Duplicated/conflicting IDs | Create duplicate IDs in model collections and collide incoming registry entries with existing records. | Validator rejects each with namespace/ID context and does not mutate the existing registry. |
| Dangling references | Build analysis/evaluation records with unknown Evidence, Finding, or Problem IDs. | Cross-output validation fails before any derived score/report use. |
| Nullable dates/excerpts | Deserialize fixture evidence with `published_at` and `source_excerpt` set to `null`. | Contract accepts legitimate unknown source metadata while retaining required access/provenance fields. |
| Invalid enums/scores | Parameterize invalid independence/verification/status values and scores outside `0..3`. | Pydantic/validator rejects invalid contract values with actionable errors. |
| Boundary totals | Evaluate complete records totaling 0, 6, 7, 9, 10, and 12. | Python computes `Low priority`, `Promising`, and `Strong` at the agreed boundaries. |
| Partial scoring | Make one of the four dimensions explicitly unscoreable while retaining valid scores for the rest; test both available-reference and no-reference cases. | Result is `Research needed` with no total; no unknown score is coerced to zero; an unscoreable assessment always has a rationale and, if it has no Evidence IDs, a specific gap plus targeted next validation action. |
| Stage 2 gating | Attempt Stage 2 on each ineligible state and on eligible fully scored states with/without user benefit. | Only fully scored `Strong`/`Promising` records with nonblank articulated benefit may include Stage 2. |
| Safe registry merging | Merge valid additions, duplicate incoming entries, and conflicts with original registry data. | Valid addition succeeds; duplicates/conflicts fail atomically and never silently overwrite. |
| Lack of evidence is not zero | Validate a record with unresolved evidence gaps/unscoreable dimensions rather than negative evidence. | It remains structurally valid as uncertainty/`Research needed`, not a fabricated `0`. |

## 9. Risks, assumptions, and decision requests

### Risks and mitigations

- **Overly rigid schemas could confuse unknown facts with bad data.** Keep only the agreed structural fields mandatory; preserve nullable source metadata and explicit gaps/statuses.
- **Registry duplication across handoffs could undermine independence and provenance.** Centralize merge/reference checks and test that downstream records hold IDs, not copied evidence.
- **Derived score state could drift from model-provided values.** Use pure deterministic functions as the sole calculation path and reject inconsistent serialized values.
- **Premature persistence could lock in M7 concerns.** Limit this milestone to in-memory models and JSON serialization/fixtures; leave run paths and atomic file writes to M7.

### Delegated implementation choices

- Exact Pydantic class names, error message wording, ID-prefix validation strictness, and helper function names.
- Whether collection-level uniqueness lives in Pydantic validators, explicit cross-output validation, or both, provided all acceptance behavior remains deterministic and tested.
- Whether supporting sub-records are nested in `contracts.py` or split into one additional module only if that materially improves clarity without expanding scope.

### Unresolved blockers / decision requests

None. The M2 brief and Step 4 intentionally delegate exact class and file names; the recommended choices above are sufficiently narrow to implement without changing policy.

### Cross-milestone impact

M3’s tool adapters must emit `EvidenceItem` records into the M2 registry rather than their own copied source shapes. M4, M5, and M6 must construct only these contracts and use M2 validators at handoffs; M7 will add the actual JSON artifact lifecycle. M8’s manual review relies on the preserved provenance and explicit uncertainty established here.

## 10. Approval boundary

**Status: approved for M2 implementation on 2026-10-15.** This plan covers M2 only. Do not begin another milestone without separate human approval.
