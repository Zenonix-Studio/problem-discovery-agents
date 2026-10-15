# M7 Implementation Plan — CrewAI Flow Orchestration & Artifact Persistence

## 1. Milestone goal and source references

Connect the completed M4–M6 in-memory services into one manually invoked, straight-line CrewAI Flow for the **Developer Tools & Productivity** pilot. Each successful run must leave inspectable JSON handoffs, the one merged authoritative evidence registry, and exactly one Markdown report for human review.

Authoritative sources: `docs/milestones/M7_crewai_flow_orchestration_artifact_persistence.md`; Architecture v1 §§3–5; Step 1 §3; Step 4 §§1, 3, and 5; and the governing policy in `AGENTS.md`. The research guide’s report and human-review requirements and Steps 2–3’s single-pass analysis and deterministic `/12` evaluation rules continue to apply.

## 2. Scope and non-goals

### Included

- A single Flow path: M4 Research (Pass 1 then Pass 2) → M5 Analysis (one pass) → M6 Evaluation/report → artifact persistence → human-review handoff.
- Transition validation using the existing M2 validators, including the M5-returned merged registry as the only registry passed to M6 and persisted as authoritative.
- A minimal manual command accepting the pilot category and optional workflow focus; reject every category other than `Developer Tools & Productivity` before services start.
- Per-run persistence of `ResearchOutput`, `AnalysisOutput`, `EvaluationOutput`, authoritative `EvidenceRegistry`, one report, and a small safe run manifest/diagnostics record.
- Actionable errors, bounded retries inherited from the existing retrieval adapters, and best-effort recording of provider-supplied model usage/cost metadata only when available.
- Offline mocked Flow/integration tests and short run instructions.

### Explicitly excluded

- A controller/verifier/report-writing agent, extra CrewAI crews, debate, task queue, scheduler, dashboard, database, generalized harness, or Analysis → Research rerun.
- New research providers, unbounded retry behavior, live credential-dependent automated tests, invented usage/cost values, or automatic pilot grading.
- Changes to agent prompts, research policy, evidence semantics, Stage 1 scoring, Stage 2 gating, or M8’s mandatory human review.

## 3. Current repository state and dependencies

- M1 supplies `Settings`, shared-model construction, safe configuration errors, and a nullable `RunUsage`; no CLI or run directory exists.
- M2 supplies Pydantic handoffs and `validate_research_output`, `validate_analysis_output`, and `validate_handoffs`. Its registry merge is immutable and rejects Evidence-ID conflicts.
- M3 supplies injected, bounded-retry GitHub/Tavily adapters and `M3ResearchTools`; its errors are safe retrieval records rather than secrets.
- M4 supplies `ResearchAgent.run(ResearchRequest) -> ResearchRunResult`, including both research passes and diagnostics. M5 supplies `AnalysisAgent.run(ResearchOutput) -> AnalysisRunResult`, whose `evidence_registry` is the safely merged registry. M6 supplies `EvaluationAgent.run(research, analysis, registry) -> EvaluationRunResult`, including validated evaluation JSON and one in-memory report.
- Agent factory/adapters already exist but deliberately do not run a Flow. There is no Flow module, composition root, artifact writer, command entry point, artifact schema/manifest, or M7 test module.
- `pyproject.toml` already declares `crewai>=1.8,<2`; implementation must verify the installed Flow API with local fakes/compatibility tests before relying on a decorator/callback shape. It must not assume a remote model is available.

## 4. Proposed technical approach

### Composition root and straight-line Flow

**Delegated choice, recommended:** add a narrow `flow.py` composition boundary with a single `ProblemDiscoveryFlow` (or equivalently named) CrewAI `Flow`. It owns a typed ephemeral run state: request, the three service results, merged registry, artifact location, and safe diagnostics. The Flow invokes the existing services exactly once in this fixed order:

1. Validate/normalise the CLI request as `ResearchRequest`, then call Research.
2. Revalidate `ResearchOutput`, call Analysis once, and retain its returned merged registry.
3. Revalidate Research → Analysis and registry equality/identity-by-content, call Evaluation once with that exact merged registry, then call `validate_handoffs` on all three outputs.
4. After each successful transition validation, persist that stage's validated JSON and atomically update the manifest's completed stage. Only after final handoff validation may the Flow persist `EvaluationOutput`, the full merged registry, and the unchanged M6 report, then mark the manifest successful.

The Flow may use normal CrewAI Flow start/listen primitives for this sequencing, but a small injected service bundle must remain the primary test seam. It must not create an agent per stage at runtime or call a service twice as a retry. Construction belongs in a separate composition function: load settings once, build the three existing CrewAI agents/planners, construct one shared `M3ResearchTools` instance from the existing adapters, then inject these dependencies into M4/M5/M6 services.

### Artifact and failure boundary

**Delegated choice, recommended:** write runs under a caller-selectable root (default proposed: `artifacts/`) into a freshly allocated timestamp/UUID-style directory, never an implicit overwrite. Serialize Pydantic objects with `model_dump(mode="json")` and UTF-8 JSON; use deterministic filenames such as `research_output.json`, `analysis_output.json`, `evaluation_output.json`, `evidence_registry.json`, `report.md`, and `run_manifest.json`.

`run_manifest.json` should record non-secret request inputs, start/finish timestamps, completed stage, artifact names, safe diagnostics, available usage fields, separate/unknown search cost, and final status. The writer should use same-directory temporary files followed by atomic replacement so a completed artifact is not torn. Research JSON is written only after Research validation; Analysis JSON only after Research → Analysis validation; Evaluation JSON, the full registry, and report only after final handoff validation. On a stage/validation failure, preserve only those already-valid earlier-stage artifacts and atomically replace the manifest with a `failed` status, failing stage, and safe actionable error; never emit a later-stage artifact or call a later agent. The command returns non-zero after surfacing the run directory and error. This preserves inspection without presenting partial output as a successful report.

The writer must reject a mismatched registry or invalid handoff before writes. It persists the full M5 merged registry, never `AnalysisOutput.evidence_registry_delta` as if it were authoritative. JSON readers, if added for verification, parse through the existing contract models and rerun relevant validators rather than trusting files.

### Usage, costs, configuration, and CLI

Use `Settings`/existing configuration validation at the composition boundary; no module may read credentials directly. A proposed `python -m problem_discovery_agents.run` argparse entry point accepts required `--category`, optional `--focus`, and optional `--output-dir`; `--category` must be the one pilot category. It prints only a short success/failure summary and artifact directory, never secrets or full provider responses.

Aggregate usage only from provider metadata exposed by the real CrewAI/LLM result objects. Because M4–M6 planners currently parse and discard those results, the composition root must wrap each already-created CrewAI agent in a lightweight, non-agent `UsageCapturingAgent` proxy before passing it to the existing planner adapter. The proxy delegates `kickoff()` unchanged, records only its safe provider metadata, and therefore covers Research's two plans, Analysis's plan/finalize calls, and Evaluation's Stage 1/conditional Stage 2/report calls without changing prompts, service contracts, or agent count.

An observability helper normalizes known provider fields into per-call `RunUsage` records and a run-level summary. It must emit a run-level token/cost total only when that field is available for every captured model call; otherwise its total is `null` and the manifest identifies it as partial/unknown while retaining any safely available per-call values. It must not infer missing counts or prices. Keep `search_retrieval_cost_usd` null/unknown unless a provider actually exposes it, and distinguish it in the manifest. Tests use fake metadata and absence cases. Existing M3 retry policies remain the only retrieval retries; Flow-level retries are not added.

## 5. File change map

All paths below are proposals for implementation after approval.

| Path | Change | Purpose |
| --- | --- | --- |
| `src/problem_discovery_agents/flow.py` | Create | One injected, straight-line CrewAI Flow/state and service-composition boundary, including the non-agent `UsageCapturingAgent` proxy. |
| `src/problem_discovery_agents/artifacts.py` | Create | Validated JSON/Markdown persistence, atomic writes, manifest, safe partial-failure recording, and optional verified reads. |
| `src/problem_discovery_agents/run.py` | Create | Minimal `python -m` manual entry point, argument validation, settings/composition invocation, safe exit handling. |
| `src/problem_discovery_agents/observability.py` | Update | Add small provider-metadata normalization and run aggregation helpers; retain missing/partial totals as null. |
| `src/problem_discovery_agents/__init__.py` | Update if useful | Export the intentionally small public Flow/entrypoint boundary; do not expose framework internals unnecessarily. |
| `tests/test_flow.py` | Create | Offline happy-path, order, no-rerun, transition-validation, usage, and safe-failure Flow tests using injected fakes. |
| `tests/test_artifacts.py` | Create | Temporary-directory persistence, JSON round trip, merged-registry, atomic/failure manifest, and no-secret artifact tests. |
| `tests/test_run.py` | Create | CLI argument/category/output/error behavior with mocked composition; no live service invocation. |
| `README.md` | Update | M7 manual run command, artifact layout, offline test command, credentials caveat, and M8 human-review handoff. |
| `docs/plans/M7_IMPLEMENTATION_PLAN.md` | Create | This proposed plan only. |

No contract, validator, provider-adapter, agent-prompt, or migration change is planned. A real gap in an existing M1–M6 public boundary is a decision request, not authorization to redesign it.

## 6. Ordered implementation tasks

1. Reconfirm M4–M6 input/result contracts and installed CrewAI Flow construction locally with fakes; select the smallest compatible Flow API and document an actionable incompatibility if there is one.
2. Define small M7-only run state/dependency protocols and a composition factory. Keep service injection possible so no test needs settings, credentials, network, or a model.
3. Implement the fixed Flow transitions, validating before every downstream call and asserting the exact M5 merged registry is passed to Evaluation. Persist each successfully validated stage immediately; ensure a failure prevents all later transitions.
4. Implement artifact names, unique run directories, safe manifest model/serializer, and atomic file writes. Write only the final Evaluation/registry/report set after final contract validation; implement the specified completed-stage failure manifest behavior.
5. Wrap real CrewAI agents at composition time with a metadata-capturing proxy, normalize only returned provider usage metadata, and aggregate only complete run-level fields. Preserve partial/unknown values and pass only safe diagnostics to the manifest.
6. Implement the thin CLI and composition wiring using existing settings, agent factories, and M3 adapters. Validate category before constructing/running live services; provide safe error exits.
7. Add focused offline fixtures/fakes and tests, then update README with only commands and behavior actually verified.
8. Run the focused suites and the full suite. Do not execute a paid/live research run, begin M8 review, or broaden pilot scope.

## 7. Test and verification plan

All automated tests use injected fake services/agents/providers, temporary directories, and placeholder configuration only.

- **Happy path:** one mocked run writes all four JSON artifacts, exactly one report, and a successful manifest; parse them back and validate the complete chain, direct URLs, and registry references.
- **Order and cardinality:** record calls to prove Research runs once (including its internal two passes), Analysis once, Evaluation once, and no Analysis → Research or hidden report-agent path exists.
- **Transition integrity:** invalid research, analysis, registry mismatch/conflict, dangling reference, invalid evaluation, and mismatched registry fixtures fail with the stage/validator message and never invoke downstream services or produce success artifacts.
- **Persistence:** verify full merged registry includes M5 delta evidence exactly once; no output uses the delta alone; verify UTF-8/model JSON round trip, unique directories, atomic-write cleanup, and report content equals the M6-returned string.
- **Partial failure:** fail each stage in turn and assert only prior valid artifacts plus a safe failed manifest exist, with no fabricated evaluation/report. Assert error text and serialized diagnostics omit fake secret values.
- **CLI/configuration:** unsupported category/focus formatting and missing config fail actionably; valid mocked arguments propagate category/focus/output root. No CLI test contacts GitHub, Tavily, or an LLM.
- **Usage:** fake complete metadata across all intercepted planner calls produces accurate run totals; an absent field in any call makes that run-level total explicitly partial/`null`, while safely available per-call values remain inspectable. Search costs remain null/unknown unless fake provider metadata explicitly supplies them.
- **CrewAI boundary:** a local fake/compatibility test proves the selected Flow shape can execute the injected chain without making a remote call; a separate real configuration check remains non-network only.

Commands to establish after implementation:

```text
uv run pytest tests/test_flow.py tests/test_artifacts.py tests/test_run.py
uv run pytest
uv run python -m problem_discovery_agents.config_check
```

## 8. Acceptance matrix

| M7 acceptance check | Observable verification action | Expected result |
| --- | --- | --- |
| Mocked end-to-end run writes consistent inspectable artifacts | Run injected happy-path Flow in a temporary output root, read JSON/Markdown/manifest, and run existing validators. | Research, Analysis, Evaluation, full merged registry, and exactly one report exist; all handoffs validate and manifest is successful. |
| All Evidence/Finding/Problem links resolve | Use a fixture with research evidence, analysis delta evidence, findings/problems/evaluations, then inspect persisted files and validate. | Every downstream ID resolves against the persisted authoritative merged registry; no duplicate/conflicting Evidence ID is silently overwritten. |
| Deliberate schema violations fail clearly | Inject invalid/dangling handoff and registry-conflict cases at each transition. | Error identifies the failing stage/contract; later services are not called; manifest records safe failure state only. |
| No keys needed for automated tests | Run all M7 tests with fake services/providers and isolated temp directories. | Tests pass without `.env`, network, GitHub/Tavily, or model credentials. |
| No extra agents or hidden rerun paths | Assert construction/call trace for the Flow under happy and failure cases. | Only existing Research, Analysis, and Evaluation agents/services are used once in prescribed order; no retry re-invokes an agent and no Analysis → Research path exists. |

## 9. Risks, assumptions and decision requests

### Risks and mitigations

- **CrewAI Flow APIs may differ across the declared version range.** Isolate Flow-specific wiring behind one module, verify locally with fakes, and fail actionably rather than silently replacing the architecture.
- **Persisted partial results can be mistaken for a completed report.** Make status/last completed stage explicit, omit later files, and write a failure manifest; use a unique directory for every invocation.
- **A delta registry could be persisted or passed as authoritative.** Accept the registry only from M5’s result, compare it to `validate_analysis_output`, and test delta/full-registry confusion.
- **Provider usage objects are unstable or unavailable.** Intercept metadata at the CrewAI agent boundary before M4–M6 planners discard it; normalize only known fields, make incomplete run totals null/partial, and never infer prices or token counts.
- **Error/diagnostic persistence could expose secrets.** Serialize only structured safe errors and known diagnostics; test with sentinel secret strings and never serialize settings or raw provider responses.

### Assumptions and delegated implementation choices

- A local filesystem `artifacts/` default, run-scoped unique directories, and the proposed filenames are the smallest inspectable persistence approach; exact names and the run-ID format remain implementation choices.
- A `python -m` argparse command is sufficient manual invocation; adding a console-script entry point is optional only if it does not add a second execution path.
- The Flow’s state may hold Pydantic objects in memory while artifact files use JSON; its exact Pydantic/Flow state declaration is delegated.
- Existing adapter retries cover retrieval; no Flow-level agent retry is needed unless a concrete implementation failure demonstrates one without risking duplicate research.

### Unresolved blockers / decision requests

None currently. The milestone brief expressly delegates Flow API mechanics, persistence layout/naming, and partial-failure handling; the recommended choices above remain within that delegation. If installed CrewAI cannot support a single compatible Flow while preserving injected offline tests, implementation must report the concrete incompatibility before substituting another orchestration mechanism.

### Cross-milestone impact

M7 is the final automated path before M8. It must leave artifacts sufficient for M8 to inspect every problem/source/evaluation chain and record Pass/Fail plus rationale for Evidence Integrity, Research Quality, Analysis Quality, Evaluation Consistency, and Report Usability. M7 must not attempt that human review or automatically grade it.

## 10. Approval boundary

**Status: proposed, not yet approved.** This document plans M7 only. Do not implement M7, invoke a live research run, or begin M8 until explicit human approval is given.
