# M8 Implementation Plan — End-to-End Pilot & Acceptance Review

## 1. Milestone goal and source references

Run the first authorized, real **Developer Tools & Productivity** pilot through the existing three-agent Flow, preserve its run artifacts, and have humans audit every generated problem record against its evidence chain. The result is an explicit five-criterion acceptance decision, not a product decision or an automated claim that the research is correct.

This plan implements only [M8 — End-to-End Pilot & Acceptance Review](../milestones/M8_end-to-end_pilot_acceptance_review.md). The primary authorities are:

- `AGENTS.md` — **Human pilot acceptance**, provenance, deterministic-check limits, and scope guardrails.
- `docs/Problem_Discovery_Step4_Implementation_Contracts_Decisions.md` §4 — full-record review, the five Pass/Fail criteria, and targeted fix/rerun policy.
- `docs/Problem_Discovery_Research_Agent_Guide.md` §§8–9 — required report content and research-quality stopping checks.
- `docs/Problem_Discovery_Workflow_Architecture_v1.md` §§3–6 — straight-line three-agent workflow, traceability, and pilot acceptance.
- `docs/Problem_Discovery_Step3_Evaluation_Rubric_Decisions.md` §§2–6 — four-dimension `/12` anchors, partial-score behavior, Stage 2 gate, and manual rubric review.
- `docs/Problem_Discovery_Step1_Research_Tools_Evidence_Quality_Decisions.md` §§4–6 and `docs/Problem_Discovery_Step2_Analysis_Rules_Decisions.md` §§2–7 — independence, source verification, alternatives, counterevidence, status, and their review implications.

## 2. Scope and non-goals

### Included

- A preflight and execution checklist for one authorized live pilot, using the existing `python -m problem_discovery_agents.run` entry point with the sole permitted category.
- Capture and inventory of the M7 run directory: `research_output.json`, `analysis_output.json`, `evaluation_output.json`, authoritative `evidence_registry.json`, `report.md`, and `run_manifest.json`.
- One structured, human-written review record per pilot run. It must enumerate every `Problem ID`, its Finding/Evidence IDs and direct URLs, per-record observations/gaps, and review of clustering, alternatives/workarounds, fixes/current status, counterevidence, Stage 1 rationales, Stage 2 eligibility, and report treatment.
- Exactly five run-level **Pass/Fail plus brief rationale** verdicts: Evidence Integrity, Research Quality, Analysis Quality, Evaluation Consistency, and Report Usability.
- A narrowly scoped fix/rerun comparison log only when one or more acceptance criteria fail. It records concrete examples, the responsible boundary, the targeted change, original and rerun artifact locations, resolved issues, and regressions/new issues.
- Offline checks of the existing automated path before live execution and a clear distinction between those structural checks and the mandatory human audit.

### Explicitly excluded

- Any second research category, demand validation based solely on scores, OSS-product selection/design, or a quota of `Strong` records.
- New agents, orchestration paths, research vendors, dashboard/database, scheduler, browser automation, automatic Analysis → Research loop, or a generic review platform.
- Treating passing unit tests, a successful manifest, open/closed issue metadata, or record counts as substitutes for source-content inspection.
- Broad or speculative remediation after a failed review. Changes must be limited to the demonstrated prompt, tool/retrieval, schema/validator, or agent behavior responsible for the failure.

## 3. Current repository state and dependencies

Verified current artifacts:

- M1–M7 are present in `src/` and their implementation commits precede this plan. `ProblemDiscoveryFlow` in `src/problem_discovery_agents/flow.py` executes Research → Analysis → Evaluation exactly once; it persists only validated handoffs through `ArtifactWriter`.
- `src/problem_discovery_agents/artifacts.py` creates one unique run directory and writes the six required successful-run artifacts. Its manifest distinguishes a failed partial run from a successful report.
- `src/problem_discovery_agents/run.py` provides the manual command, accepts optional focus, rejects non-pilot categories before services run, and loads credentials only through `settings.py`.
- Existing tests cover the Flow, artifact writer, CLI boundary, contracts, validators, agents, and tools using fakes. No live run artifact, human review record, reusable M8 review template, or targeted fix/rerun log exists yet.
- `README.md` documents the command, artifact names, credential policy, and the five required criteria, but does not yet give reviewers a record format or an end-to-end review procedure.

Dependencies before executing the pilot are deliberately external and must be verified without guessing: an authorized live run, valid GitHub/Tavily/LLM credentials, provider/model availability and argument compatibility, permitted API spend, and reachable source content. The live run must not start until a human explicitly authorizes it; no credential value belongs in a review record or commit.

## 4. Proposed technical approach

### Review artifacts and location

**Delegated choice, recommended:** add documentation-only templates under `docs/templates/` and copy them into the completed run directory as human-authored files (`m8_review.md`, plus `m8_fix_rerun_log.md` only after a failed review). This keeps review evidence adjacent to the immutable run JSON/Markdown while leaving reusable instructions outside generated artifacts. The run directory is the source of truth for the reviewed output; the template must record its relative/absolute run path and manifest run metadata rather than copy model outputs.

`m8_review.md` should be a compact but fixed Markdown record with:

1. Run identity, reviewer/date, command category/focus, manifest status, artifact inventory, and declared coverage/access limitations.
2. A **record-by-record audit table** with one mandatory row for every `Problem ID` in `analysis_output.json` (including `outdated`, `contradicted`, `needs_validation`, Low priority, and `Research needed` records). Each row links Problem → Finding IDs → Evidence IDs/direct URLs and records source/excerpt inspection, independence conclusion, clustering/alternative/counterevidence/current-status review, evaluation/rubric review, report representation, uncertainties, and a record-level finding.
3. Five named acceptance verdicts, each exactly `Pass` or `Fail` with a concise evidence-based rationale. The template embeds the Step 4 pass requirements so reviewers do not invent a meta-score.
4. Unresolved uncertainties, coverage gaps, inaccessible sources, and follow-up validation questions, even when the run passes.
5. A final disposition: accepted for human use as a research pilot, or failed pending targeted correction. It must explicitly say that acceptance is not validation of product demand or authorization to expand categories.

`m8_fix_rerun_log.md` is created only for a failed review. Each entry links the failed criterion and concrete `Problem`/`Finding`/`Evidence` example to one responsible code/prompt/tool/validator boundary, states the narrowly proposed correction, identifies both run directories, compares the original issue with the rerun, and records newly introduced issues. It must not prescribe an automatic rerun or an architectural expansion.

### Human review procedure

The runbook should direct reviewers to first confirm `run_manifest.json` is `succeeded` and the required six artifacts are present, then use existing Pydantic/validator-backed artifacts as a structural baseline. Reviewers must still open/inspect accessible original URLs and their stored excerpts/content context; inaccessible sources are recorded as limitations, never upgraded to verified evidence.

For each problem, reconcile the exact graph **Evaluation → Problem → Finding/Evidence → source URL**. Reviewers check the Step 1 independence classification separately from Step 2 status; inspect merge/split rationale; verify that alternatives, actual workarounds, fixes/current-context evidence, and counterevidence were investigated or honestly unknown; and apply the Step 3 anchors rather than source counts. In particular, the checklist calls out that Reality `3` needs direct technical verification in addition to independent firsthand reports, Alternative Gap `3` needs strong firsthand unmet-need evidence, Meaningful Benefit `3` needs concrete impact plus a measurable outcome, and any unscoreable dimension means no total and no Stage 2.

The report review compares `report.md` to all generated records and registry entries: it must retain inconclusive/rejected material, separate `Research needed` from ranked fully-scored records, name limitations, avoid product pitches/demand claims, and preserve only resolvable direct citations.

### Execution and remediation boundaries

The first live run should omit `--focus` unless the human approver specifies a workflow focus; omission best supports the required bounded, category-level workflow sampling without presupposing a pain point. Record the exact authorized command in the review record. Preflight with offline tests and the non-network configuration check; configuration success does not assert remote access or source availability.

If all five criteria pass, preserve the review record alongside artifacts and stop: later category expansion remains a separate human decision. If any criterion fails, record the failure before changing anything, make only the identified correction after separate implementation authorization, execute a new manually authorized run, and compare it in the fix/rerun log. The Flow itself never loops back automatically.

## 5. File change map

All paths are proposed for implementation after approval.

| Path | Change | Purpose |
| --- | --- | --- |
| `docs/M8_PILOT_RUNBOOK.md` | Create | Human-operable preflight, authorized live-run, artifact inventory, complete audit, verdict, and failed-review handoff procedure. |
| `docs/templates/M8_PILOT_REVIEW_TEMPLATE.md` | Create | Fixed, copyable per-run Markdown record for every-problem audit, the five verdicts/rationales, uncertainties, and final disposition. |
| `docs/templates/M8_FIX_RERUN_LOG_TEMPLATE.md` | Create | Conditional, copyable log for concrete failed examples, narrow remediation, rerun comparison, and regressions. |
| `README.md` | Update | Link the M8 runbook/templates and state that a successful Flow is not accepted until the human review record is complete. |
| `tests/test_m8_review_docs.py` | Create | Lightweight offline regression checks that templates contain the five exact criteria, a per-problem audit section, uncertainty/failure-rerun fields, and no automatic-expansion language. |
| `docs/plans/M8_IMPLEMENTATION_PLAN.md` | Create | This proposed plan only. |

No change is proposed to the Flow, agents, prompts, contracts, scoring code, provider adapters, or persistent artifact schema unless an actual M8 review failure identifies one of them as responsible.

## 6. Ordered implementation tasks

1. Reconfirm existing M7 artifact filenames and the Evaluation → Problem → Finding/Evidence URL chain against the installed contracts/validators; retain M7 as the only run/persistence path.
2. Write the M8 runbook with preflight, credential/secrets safety, explicit human authorization boundary, authorized manual command, success/failure artifact inventory, and a review order that reaches every problem record.
3. Create the review template with the exact audit and verdict structure above. Require a row for every analyzed problem and explicit handling of zero-problem runs (five criteria are still reviewed; no per-problem rows are fabricated).
4. Create the conditional fix/rerun template with original/rerun artifact links, a bounded responsible component field, resolved/unresolved/new-issue comparison, and no automatic remediation instruction.
5. Add narrowly targeted documentation-template tests; they may check fixed required headings/criteria only and must not pretend to verify evidence quality.
6. Update README with the M8 handoff, copying instructions, and the distinction between structural test success and human acceptance.
7. Run the focused documentation test and the existing full offline suite. Do not invoke live providers during this verification.
8. After implementation approval and successful offline verification, request/obtain explicit approval for the paid/networked pilot. Run exactly the approved category/focus command, complete `m8_review.md` against the actual run directory, and stop or follow the documented targeted-failure path.

## 7. Test and verification plan

### Offline implementation verification

- Run existing M7 and broader regression suites to establish that the manual Flow still creates the required artifact shape without network credentials:

```text
uv run pytest tests/test_flow.py tests/test_artifacts.py tests/test_run.py tests/test_observability.py
uv run pytest
```

- Run the proposed documentation-template test:

```text
uv run pytest tests/test_m8_review_docs.py
```

- Run the existing non-network configuration check only with non-secret, valid local configuration. It checks parsing/compatibility, not live provider entitlement:

```text
uv run python -m problem_discovery_agents.config_check
```

### Live-pilot verification (only after explicit authorization)

- Execute the existing command with category exactly `Developer Tools & Productivity` and the approved focus choice, directing artifacts to the normal unique run location.
- Confirm a successful manifest and all six mandatory artifacts before starting semantic review. A failed manifest is recorded as an operational failure and does not become a review of nonexistent downstream output.
- Complete every row of the review template, cross-opening direct sources when accessible and recording access failures/limitations faithfully.
- Confirm exactly five Pass/Fail verdicts and rationales, then verify that unresolved uncertainty remains named even under a Pass.
- On failure, confirm the log points to concrete examples and a bounded correction; after a separately approved correction/rerun, compare the two review records for both resolved and newly introduced issues.

## 8. Acceptance matrix

| M8 acceptance check | Observable verification action | Expected result |
| --- | --- | --- |
| Each record is auditable back to original direct URLs | For every `Problem ID`, complete the review-table trace through its Finding/Evidence IDs to registry URLs; open accessible sources and compare claimed observation/excerpt/context. | No generated problem is omitted; inaccessible/unverifiable sources remain explicit limitations rather than upgraded evidence. |
| Five acceptance criteria each have explicit verdict/rationale | Inspect completed `m8_review.md` against its template and Step 4 §4.2. | Exactly Evidence Integrity, Research Quality, Analysis Quality, Evaluation Consistency, and Report Usability each have one Pass/Fail and evidence-based rationale; no numerical meta-score replaces them. |
| Unsolved uncertainties are named | Compare coverage, retrieval limitations, status uncertainty, unscoreable dimensions, and report gaps in artifacts with the review record. | The record identifies unresolved questions and next validation needs; it does not infer certainty from missing evidence, `open`/`closed`, or a passing test. |
| Failures cause targeted fixes, not automatic scope expansion | Review any failed verdict and its `m8_fix_rerun_log.md` before a corrective implementation/run. | The log identifies concrete examples and one responsible boundary; remediation is narrow, separately approved, and a rerun comparison includes regressions/new issues. |
| First pilot remains within approved scope | Inspect authorized command, manifest request, review record, and changed files. | Only Developer Tools & Productivity uses the existing three-agent Flow; no product decision, additional category, agent, vendor, database, dashboard, or feedback loop is introduced. |

## 9. Risks, assumptions and decision requests

### Risks and mitigations

- **A successful Flow could be mistaken for research acceptance.** Keep the required review document in the same run directory, make its five verdicts mandatory, and state plainly that structural validation cannot judge truth, independence, clustering, or rubric quality.
- **Live sources may be blocked, changed, or deleted between collection and review.** Record the inspection time and limitations; do not reconstruct missing content from snippets or declare a source verified.
- **The first live run may incur cost or expose provider incompatibility.** Use the existing configuration boundary and an explicit authorization gate; preserve safe manifest diagnostics and report unknown usage/cost rather than estimating it.
- **Review fatigue could skip weak or rejected records.** Require one row for every analyzed Problem ID, not merely Strong/Promising candidates, and compare the row count to `analysis_output.json` before issuing verdicts.
- **A failed pilot could grow into a redesign.** The fix log requires a concrete failure-to-boundary link and comparison; any new agent, provider, category, or architecture change requires a new decision outside M8.

### Assumptions and delegated choices

- Markdown templates are the smallest inspectable, version-controlled review medium; they are intentionally human-authored rather than a new database or dashboard.
- Copies live inside the reviewed run directory to bind the decision to immutable artifacts, while templates and runbook remain tracked under `docs/`.
- A blank `--focus` is the recommended first-run choice because it permits bounded workflow coverage; an explicitly approved focus is equally valid and must be recorded.
- A zero-problem run is still reviewable for coverage and report usability, but it cannot fabricate record-level evidence; reviewers record this explicitly.

### Unresolved blockers / decision requests

No policy ambiguity blocks documentation/template implementation. Actual pilot execution has two intentional prerequisites: valid authorized credentials/provider access and explicit human approval for the networked, potentially paid run (including whether to supply a workflow focus). If preflight or the live run exposes an M1–M7 defect, that defect must be documented and receive scoped implementation authorization before any fix.

### Cross-milestone impact

M8 is the mandatory human-review endpoint for M1–M7. A passing M8 review permits human consideration of what to research next; it does not itself authorize expansion to other categories, product selection, or any product implementation.

## 10. Approval boundary

**Status: proposed, not yet approved.** This plan covers M8 documentation, review-record structure, offline verification, and the later authorized pilot-review procedure only. Do not implement the plan, run live research, or make targeted fixes until explicit human approval is given.
