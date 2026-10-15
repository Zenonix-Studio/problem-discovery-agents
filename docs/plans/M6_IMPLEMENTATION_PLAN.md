# M6 Implementation Plan — Evaluation Agent & Report Generation

## 1. Milestone goal and source references

**Goal:** implement the third and final specialized agent for the manually invoked pilot. It must turn validated analyzed problems into evidence-linked Stage 1 proposals, apply the existing deterministic Python `/12` classification and Stage 2 gate, and have that **same Evaluation Agent** produce one inspectable Markdown research report. It is a problem-discovery evaluation step, not a product-selection or product-design step.

This plan covers only [M6 — Evaluation Agent & Report Generation](../milestones/M6_evaluation_agent_report_generation.md), including its objective, scope, exclusions, and acceptance checks. The governing sources are:

- `AGENTS.md` — **Data contracts and provenance**, **Stage 1: mandatory user-value gate**, and **Deterministic checks and error behavior**.
- `docs/Problem_Discovery_Step3_Evaluation_Rubric_Decisions.md` — §§2–6 (authoritative anchors, evidence-linked rationales, partial scoring, `/12` classification, Stage 2 gate, and reporting).
- `docs/Problem_Discovery_Research_Agent_Guide.md` — §§5–8 (user-value-first policy, Stage 2 limits, and mandatory report structure).
- `docs/Problem_Discovery_Step4_Implementation_Contracts_Decisions.md` — §§3.1, 3.5–3.6 and §4 (registry/`EvaluationOutput`, deterministic enforcement, and pilot review).
- `docs/Problem_Discovery_Workflow_Architecture_v1.md` — §§3–5 (three-agent sequence, Evaluation Agent responsibility, and traceability).
- `docs/Problem_Discovery_Step1_Research_Tools_Evidence_Quality_Decisions.md` §5 and `docs/Problem_Discovery_Step2_Analysis_Rules_Decisions.md` §§3–6 — source-verification, alternatives, counterevidence, current-status, and analysis-status context the evaluator must preserve rather than overwrite.

## 2. Scope and non-goals

### Included

- An injectable Evaluation Agent service accepting validated `ResearchOutput`, `AnalysisOutput`, and the one merged authoritative `EvidenceRegistry` produced by `validate_analysis_output`.
- Evaluation instructions and strict local proposal models for the exact four Stage 1 dimensions: Problem Reality, Frequency / Recurrence, Alternative Gap, and Meaningful Benefit.
- Evidence-linked rationales, counterevidence, uncertainty, explicit `Research needed` dimension gaps, and non-scored user-access/reproducibility follow-up context.
- Deterministic use of M2’s `stage1_result` and `validate_handoffs`; Python, not the LLM, derives totals, labels, and Stage 2 eligibility.
- Conditional Stage 2 qualitative assessment (`Strong`, `Partial`, `Weak`, `Unknown`) only for deterministically eligible Strong/Promising problems with an articulable user benefit.
- One Markdown report written by the same Evaluation Agent, covering the guide’s executive summary, examined landscape, comparison, shortlisted cards, rejected/inconclusive observations, source appendix, and validation questions.
- Offline fixtures and representative unit tests for contracts, rubric boundaries, contrary/outdated evidence, report traceability, and report inclusion of inconclusive observations.

### Explicitly excluded

- A fourth report-writing/verifier agent, an LLM-authored ranking engine, demand/adoption/star predictions, or product ideas/design.
- Any new research retrieval, automatic Analysis → Research rerun, additional vendor, browser automation, database, dashboard, scheduler, or generic agent harness.
- CrewAI Flow orchestration, run-directory selection, JSON/Markdown file persistence, and human pilot Pass/Fail recording; those belong to M7 and M8.
- Changing M2 contracts, the four-dimension `/12` rubric, score anchors, thresholds, or Stage 2 gate unless a concrete contract defect is found and separately approved.

## 3. Current repository state and dependencies

Verified on 2026-10-15:

- M1–M5 are implemented (`cdc05cb` is the M5 implementation commit); the working tree is clean. There is no `evaluation_agent` package, report renderer, M6 test module, or M6 plan yet.
- `contracts.py` already has `ScoreAssessment`, `Stage1Scores`, `EvaluationRecord`, `EvaluationOutput`, `ValidationGap`, and qualitative `Stage2Assessment` contracts. The Stage 1 field names exactly map to the approved four dimensions.
- `validation.py` already has the required pure `stage1_result(scores)` function and `validate_handoffs(research, analysis, evaluation)`. It resolves the merged registry through `validate_analysis_output`, verifies all evidence/problem references, recomputes total/status, and blocks Stage 2 when the result is not fully scored Strong/Promising or lacks `user_benefit`.
- M5 exposes `AnalysisRunResult.evidence_registry`, which is the only merged registry to pass forward. Serialized `AnalysisOutput` retains only a registry delta, so M6 must not treat that delta alone as authoritative.
- M4/M5 establish the injected-service and non-running CrewAI boundary patterns (`models.py`, `prompts.py`, `crew.py`, `service.py`). `ResearchTools` are intentionally not needed by M6: evaluation must judge the supplied evidence and declared gaps, not silently perform new research.
- M7 will later invoke the three services in order and persist the validated JSON and the final Markdown. M6 should return in-memory `EvaluationOutput` plus report text and must not choose artifact paths or write files.

## 4. Proposed technical approach

### Evaluation boundary and deterministic sequence

**Delegated choice, recommended:** add an `evaluation_agent` package mirroring M4/M5’s fixture-testable service boundary. `EvaluationAgent.run(research, analysis, evidence_registry)` should first validate that the supplied registry equals the safe M5 merge (or derive it once through `validate_analysis_output` and reject a mismatch), then follow this fixed sequence:

1. Give the same Evaluation Agent the research/analysis handoffs and merged registry in a structured Stage 1 proposal prompt. It returns one proposal per analyzed Problem, containing only four score-or-unscoreable assessments, linked existing Evidence IDs, rationales, counterevidence IDs, dimension-specific gaps/actions, and a candidate user-benefit statement. It must not return a total, status, rank, or invented evidence.
2. Assemble `EvaluationOutput` deterministically. Before scoring, require the proposed and assembled Evaluation `problem_id` set to equal the Analysis `problem_id` set exactly: reject duplicate, omitted, and unknown IDs rather than silently dropping an analyzed problem. Convert the four proposals into the existing contracts, call `stage1_result`, and set `stage1_total`/`stage1_status` exclusively from that result. Call the existing full handoff validator before any report work. This service-level completeness check supplements M2's per-record reference validation, which does not require an evaluation record for every analyzed problem.
3. Select only deterministically eligible records (fully scored Strong/Promising plus nonblank benefit). If any exist, ask the **same Evaluation Agent instance** for qualitative Stage 2 assessments using supplied team skills/CV context, then attach them only after a second deterministic validation. If no record is eligible, make no Stage 2 agent request and retain each validation gap.
4. Ask that same Evaluation Agent instance to write one Markdown report from the validated records and merged registry. It may summarize, but must use only supplied IDs/URLs and must not introduce scores, totals, sources, product proposals, or claims of validated demand. Return the Markdown string with the structured output.

This staged use of one agent is a low-level guardrail, not extra agents or a feedback loop: it prevents a language-model-proposed label from authorizing its own total or Stage 2 access. It also means report generation receives authoritative Python-derived results.

### Rubric and provenance guardrails

The prompt and proposal models must encode the Step 3 anchors rather than approximate them:

- Problem Reality `3` requires independent firsthand reports **and** direct technical verification; report count alone is insufficient.
- Frequency/Recurrence must weigh demonstrated recurrence/reach, never invented rates.
- Alternative Gap `3` requires strong firsthand evidence of recurring unmet need; a feature comparison or merely finding an alternative is insufficient.
- Meaningful Benefit `3` requires directly supported serious impact and an identifiable measurable outcome, without fabricated improvement figures.
- A credible negative finding can support `0`; missing evidence is `Research needed`, never coerced to `0`. Partial scores remain visible but have no total and no Stage 2.

Each assessment must contain a brief anchor-specific rationale, resolvable evidence IDs, relevant counterevidence IDs, and uncertainty. Unscoreable dimensions require a precise evidence gap and next validation action under the existing validator. The service must preserve Analysis’s `outdated`/`contradicted` evidence and current-resolution uncertainty; neither an analysis status nor a large source count mechanically dictates a score.

For Stage 2, pass only an explicitly supplied, non-secret team skills/CV context (initially the guide’s documented team strengths if no separate input contract exists). Keep its qualitative dimensions/rationales in the existing flexible `Stage2Assessment.assessments` map; do not create a fifth Stage 1 score. `User Access / Validation` belongs in `ValidationGap.user_access_validation` when useful, not score arithmetic.

### Report composition and traceability

The report prompt should receive the validated evaluation JSON, related problem/finding records, the authoritative registry, research coverage, and a compact report schema. Require these sections, even when data are sparse:

1. Executive summary: Developer Tools & Productivity scope, date/access context, coverage limits, highest-confidence observations (not pitches), patterns, disconfirming findings, and unverified items.
2. Examined landscape: actually examined workflows, candidate count, user groups, recurring pains, alternatives, deferred/unexamined coverage, and limitations.
3. Comparison: fully scored records ordered primarily by deterministic Stage 1 classification/total; `Research needed` records visibly separated and never given a fabricated total/rank.
4. Shortlisted problem cards: statement, user/workflow/consequence, 2–4 direct linked sources where available, alternatives/workarounds, measurable outcome, four dimension assessments, counterevidence, conditional Stage 2, and next validation.
5. Rejected and inconclusive observations: retain `outdated`, `contradicted`, `needs_validation`, Low priority, and partial-score records with their reasons.
6. Source appendix and validation questions: Evidence ID, direct URL, type, source/access date where known, verification/limitations, and supported claim.

Use a small deterministic report-input builder to hand the model source URLs and evidence metadata alongside IDs, and a lightweight post-generation check for required headings, every Evaluation Problem ID, and only registry-resolvable `EV-…` citations/URLs. This is a structural completeness check, not semantic validation. Keep report text in memory; M7 owns filename and atomic persistence choices.

### CrewAI construction

Add one non-running Evaluation Agent factory using M1’s `build_shared_llm`, `allow_delegation=False`, and M6-specific instructions. A small planner/writer adapter should accept strict response formats for Stage 1 and Stage 2; Markdown uses the same instantiated agent’s normal text response. Test construction and parsing with fake factories/agents only. If the installed CrewAI API rejects the selected structured-output call shape, raise an actionable configuration/integration error and request the smallest compatible adjustment—do not silently alter model configuration or add another framework.

## 5. File change map

All production paths below are proposals for implementation after approval.

| Path | Change | Purpose |
| --- | --- | --- |
| `src/problem_discovery_agents/evaluation_agent/__init__.py` | Create | Narrow exports for service, result, and CrewAI adapter/factory. |
| `src/problem_discovery_agents/evaluation_agent/models.py` | Create | Strict local Stage 1/Stage 2 proposal, report-input, and diagnostic models; no duplicate authoritative handoff contracts. |
| `src/problem_discovery_agents/evaluation_agent/prompts.py` | Create | Versioned Step 3 anchor instructions, scope prohibitions, Stage 2 conditionality, and report-section requirements. |
| `src/problem_discovery_agents/evaluation_agent/service.py` | Create | Input/registry validation, proposal-to-contract assembly, deterministic scoring/gating, same-agent Stage 2/report calls, and in-memory result. |
| `src/problem_discovery_agents/evaluation_agent/crew.py` | Create | Non-running shared-LLM Agent factory plus structured proposal/report adapter. |
| `src/problem_discovery_agents/evaluation_agent/report.py` | Create if it keeps `service.py` focused | Report-context construction and non-semantic Markdown completeness/reference checks; no filesystem I/O. |
| `tests/test_evaluation_agent.py` | Create | Offline service, prompt, CrewAI-boundary, score/gate, and Markdown report behavior tests. |
| `tests/test_validation.py` | Update only if M6 exposes an uncovered M2 validator integration case | Retain/extend pure contract assertions without duplicating service tests. |
| `tests/fixtures/evaluation_agent/...` | Create | Redacted research/analysis/registry/proposal/report fixture data for positive and failure paths. |
| `README.md` | Update | Describe M6’s in-memory Evaluation Agent/report boundary and verified offline test command; keep M7 persistence explicitly future work. |
| `docs/plans/M6_IMPLEMENTATION_PLAN.md` | Create | This planning artifact only. |

No change to `contracts.py` or `validation.py` is planned: M2 already supplies the required output and deterministic boundary. If implementation exposes a genuine missing contract rather than a local-agent convenience, stop and request a scoped decision before changing agreed semantics.

## 6. Ordered implementation tasks

1. Reconfirm the M2 contracts/validators and M4/M5 service/CrewAI patterns. Verify with fakes that the installed CrewAI release supports the proposed structured Stage 1/Stage 2 response boundary; do not use credentials or make live calls.
2. Define strict local proposal models that make all four and only four Stage 1 dimensions mandatory; prohibit totals/statuses in LLM output. Define optional Stage 2/report input models and a run-result model containing `EvaluationOutput`, report Markdown, and minimal diagnostics.
3. Write Evaluation Agent instructions using the exact Step 3 anchors, distinction between zero and missing evidence, evidence/counterevidence/uncertainty rules, no-product/no-demand-prediction constraint, and guide-compliant report requirements. Add prompt regression tests before live adapter work.
4. Implement service input validation: validate Research → Analysis references, obtain/confirm the single merged registry, and reject mismatched or copied/delta-only registry inputs actionably.
5. Implement Stage 1 proposal assembly, including exact Analysis-to-Evaluation Problem ID set equality, then call M2’s `stage1_result` plus `validate_handoffs`. Reject an omitted, duplicate, or unknown evaluation proposal before report work. Ensure every label/total comes from Python and unscoreable dimensions retain their gap/action with no total.
6. Implement conditional Stage 2 with the same Evaluation Agent instance, only after deterministic eligibility. Attach/validate its qualitative assessments and record non-scored user-access/reproducibility follow-up where supplied.
7. Implement same-agent Markdown generation from validated context plus a small report completeness/reference check. Preserve inconclusive/rejected records and ensure report citations resolve to the authoritative registry.
8. Add redacted fixtures and focused offline tests. Run M6 tests, then the entire suite; update README only for behavior actually verified. Do not implement Flow, artifact writes, human review workflow, or a live provider call.

## 7. Test and verification plan

All tests use static contracts, fake planners/writers, and fake CrewAI factories. They require no environment secrets, network, model invocation, GitHub, or Tavily access.

- **Stage 1 assembly and anchors:** test all four named assessments are required; a proposal cannot add a fifth dimension, total, or status. Fixture cases distinguish `0` supported by credible negative evidence from an unscoreable gap; preserve partial scores and evidence/counterevidence IDs.
- **Evaluation completeness:** a fixture with two analyzed Problems and one proposal, duplicate proposals for one Problem, and a proposal for an unknown Problem each fail actionably. A complete one-to-one Problem ID set succeeds, so every analyzed record receives a visible evaluation/report outcome.
- **Deterministic thresholds:** mocked fully scored proposals totaling `0`, `6`, `7`, `9`, `10`, and `12` produce exactly M2’s labels. Assert attempted LLM-provided totals/statuses have no path into `EvaluationOutput`.
- **Partial scoring:** an unscoreable dimension with specific rationale/gap/action yields `Research needed`, `stage1_total is None`, no rank/Stage 2, and report wording that does not imply a `/12` total.
- **Stage 2 gate:** Strong/Promising plus a nonblank benefit invokes the same-agent Stage 2 adapter and accepts qualitative values/rationales. Low priority, Research needed, absent benefit, and attempted disallowed Stage 2 are rejected/omitted before report generation.
- **Counterevidence and currency:** fixtures for a current fix, credible contrary account, uncertainty, and analysis `outdated`/`contradicted` records show their linked evidence is passed to the evaluator and reported; the service does not turn closed metadata or missing contrary evidence into certainty.
- **Traceability:** dangling proposal/report Evidence IDs, unknown Problem IDs, inconsistent supplied merged registry, and copied/invalid source URLs fail with actionable errors. Every report evidence citation/link must resolve to the registry and every evaluated problem must be present.
- **Report content:** use a mixed Strong/Promising, Low priority, Research needed, outdated, and contradicted fixture. Assert required sections, examined coverage/limitations, comparison treatment, source appendix, validation questions, and explicit inclusion of inconclusive/rejected observations. Assert no product pitch, star prediction, or ungrounded numeric benefit enters fixture output.
- **CrewAI/prompt boundary:** fake construction receives the single shared configured LLM and `allow_delegation=False`; one fake Evaluation Agent instance performs the permitted staged calls. Structured parsing and malformed response handling are tested without claiming remote model availability.

Commands to establish after implementation:

```text
uv run pytest tests/test_evaluation_agent.py tests/test_validation.py
uv run pytest
```

## 8. Acceptance matrix

| M6 acceptance check | Observable verification action | Expected result |
| --- | --- | --- |
| Mocked scenarios cover fully scored thresholds | Parameterize four valid assessments whose sums are 0, 6, 7, 9, 10, and 12; run service assembly and `validate_handoffs`. | Python produces only `Low priority`, `Promising`, and `Strong` at the agreed boundaries; no LLM total/status is trusted. |
| Partial score has no total | Mock one dimension as unscoreable with rationale, resolvable evidence where available, gap, and next action. | Output is `Research needed`, total is `null`, Stage 2 is absent, and the report presents targeted validation rather than a partial rank. |
| Disallowed Stage 2 is blocked | Return a Stage 2 proposal for Low priority/Research needed or omit benefit on an otherwise high score. | Service/validator rejects or omits it; only fully scored Strong/Promising records with a nonblank benefit retain Stage 2. |
| Contrary/outdated evidence is covered | Supply analyzed problems linked to credible fix/contrary evidence and a current-status uncertainty fixture. | Assessments and report include the evidence’s limiting effect/uncertainty; no source state alone becomes a resolution conclusion. |
| Source references resolve | Feed valid and dangling Evidence/Problem IDs into Stage 1 proposals and report fixtures. | Valid report citations resolve through the merged registry to direct URLs; invalid references fail before output is returned. |
| Every analyzed problem is evaluated | Supply fixtures with omitted, duplicate, unknown, and one-to-one Evaluation Problem ID sets. | Service rejects every non-bijective Analysis-to-Evaluation mapping before scoring/report generation; complete mappings retain every analyzed problem. |
| Report includes inconclusive observations | Generate a report from mixed scored, partial, contradicted, and outdated records. | Markdown has the guide-required sections and explicitly retains Research needed/rejected/inconclusive observations with reasons and next validation questions. |

## 9. Risks, assumptions and decision requests

### Risks and mitigations

- **The model may smuggle arithmetic, an unsupported score, or invented citations into prose.** Local proposal models omit derived fields; Python derives all labels/totals/gates; report context is normalized and citation/heading checks reject structural drift. Human M8 review still assesses semantics.
- **A report can hide uncertainty despite valid JSON.** Require a separate rejected/inconclusive section, pass validation gaps/counterevidence into report context, and use mixed-outcome regression fixtures.
- **Stage 2 may contaminate Stage 1.** Make Stage 2 a conditional same-agent call after deterministic Stage 1 validation; do not give it a path to alter Stage 1 records.
- **Registry ambiguity can break traceability.** M6 consumes M5’s merged registry and reuses `validate_handoffs`; it never resolves citations against the analysis delta alone.
- **CrewAI structured-output surface may differ from M4/M5 assumptions.** Test injected fake boundaries first and report a concrete incompatibility rather than silently substituting a new provider, agent, or parsing framework.

### Assumptions and delegated implementation choices

- An in-memory `EvaluationRunResult` with `evaluation_output`, `report_markdown`, and minimal diagnostics is the smallest boundary before M7 persistence.
- Reusing the guide’s documented team strengths as default Stage 2 context is acceptable only when a separate non-secret skills/CV input is absent; exact public API and field names are implementation choices. Missing context should lead to `Unknown`, not an invented fit claim.
- A two/three-call staged interaction with the **same** Evaluation Agent instance is preferable to trusting an all-in-one LLM response because it preserves Python authority over totals/gates. Exact adapter method names and private report-check mechanics are delegated.
- Report heading names may vary slightly if they unmistakably cover every mandatory guide section and tests check the agreed semantic structure.

### Unresolved blockers / decision requests

None. The M6 brief and Step 4 deliberately leave local module names, CrewAI adapter mechanics, report formatting, and Stage 2 assessment-key vocabulary to implementation. A concrete incompatibility with the existing M2 contracts or installed CrewAI structured-output API must be reported rather than silently broadened into a policy change.

### Cross-milestone impact

M7 must call this service only after M4/M5, persist `EvaluationOutput` and exactly one Markdown report together with research/analysis artifacts and the merged registry, and retain the report returned here without introducing a report agent. M8 must manually inspect every evaluation/problem/source chain plus all five Pass/Fail criteria; M6’s structural tests and report checks supplement but cannot replace that review.

## 10. Approval boundary

**Status: proposed, not yet approved.** This document plans M6 only. Do not implement M6 or begin M7/M8 until explicit human approval is given.
