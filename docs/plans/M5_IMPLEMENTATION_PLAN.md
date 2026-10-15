# M5 Implementation Plan — Analysis Agent Implementation

## 1. Milestone goal and source references

**Goal:** implement the one-pass Analysis Agent that consumes a validated `ResearchOutput`, produces solution-neutral `AnalysisOutput`, and performs bounded, evidence-aware clustering, alternatives/workarounds, currency/resolution, and counterevidence checks. It must preserve uncertainty and shared-registry provenance; it must not score problems or propose a product.

This plan implements only [M5 — Analysis Agent Implementation](../milestones/M5_analysis_agent_implementation.md), especially its **In scope**, **Out of scope**, and **Acceptance checks**. Its primary authorities are:

- `AGENTS.md` — **Required v1 workflow**, **Research and analysis rules**, **Data contracts and provenance**, and **Deterministic checks and error behavior**.
- `docs/Problem_Discovery_Step2_Analysis_Rules_Decisions.md` — §§2–6 (A1 clustering, A3 alternatives, A4 counterevidence, A5 statuses, and handoff traceability).
- `docs/Problem_Discovery_Workflow_Architecture_v1.md` — §4 **Analysis Agent** and §5 **Data flow and traceability**.
- `docs/Problem_Discovery_Step1_Research_Tools_Evidence_Quality_Decisions.md` — §5 (especially R6.4 current-status semantics and transparent failures).
- `docs/Problem_Discovery_Step4_Implementation_Contracts_Decisions.md` — §§3.1, 3.2, 3.4, and 3.6 (one registry, analysis handoff, and structural validation).

The Research Guide §§3–4 and §7 remain governing policy for source quality, solution neutrality, alternatives, workarounds, and transparent uncertainty. Step 3 is cross-milestone context only: M5 preserves inputs needed for later evaluation but does not perform Stage 1 or Stage 2.

## 2. Scope and non-goals

### Included

- A single-pass, injectable Analysis Agent service that accepts a validated `ResearchOutput` and returns a validated `AnalysisOutput` plus the safely merged authoritative evidence registry in memory.
- Flexible semantic clustering using the approved triad: common user task/workflow, underlying friction/failure mechanism, and consequences. Each output problem records its constituent Finding IDs and a concise merge/split rationale; uncertain equivalence stays separate.
- Bounded research of relevant built-ins, existing tools, and actual user workarounds. Each alternative records what it solves, linked evidence where available, and exactly one existing `GapOutcome`: `supported_gap`, `unknown_gap`, or `need_substantially_met`.
- A proportionate counterevidence check for every analyzed problem: current-version/currency context, actual resolution evidence, contrary experiences, and scope limitations. Closed/open metadata alone remains insufficient.
- Stable Problem IDs; source-backed new analysis evidence with stable, non-conflicting Evidence IDs; safe merge into the existing central registry; source links rather than copied source objects in downstream records.
- Exactly the existing statuses `corroborated`, `needs_validation`, `outdated`, and `contradicted`, each with a required evidence-linked classification rationale and explicit unresolved uncertainty.
- Prompt/instruction templates, M3-shaped retrieval use, fixture-driven offline tests, and focused standalone analysis-handoff validation.

### Explicitly excluded

- Stage 1 scoring, totals/labels, Stage 2/career fit, evaluation report generation, or changes to the approved four-dimension `/12` rubric.
- Product proposals, solution design, demand/market validation claims, rigid semantic-similarity thresholds, or fixed competitor/query quotas.
- A verification or report-writing agent, automated request/rerun of Research, agent debate, database, dashboard, scheduler, browser automation, or a new search vendor.
- M7 Flow orchestration, artifact-directory persistence, and a live model/provider/tool run as a unit-test requirement.

## 3. Current repository state and dependencies

Verified on 2026-10-15 before this plan was written: M1–M4 are implemented and the working tree was clean. The repository has no `analysis_agent` package, Analysis Agent prompts/service/tests, or analysis-specific fixtures. No M5 plan existed.

- `contracts.py` already supplies `Problem`, `Alternative`, `AnalysisOutput`, `ProblemStatus`, `GapOutcome`, and `EvidenceRegistry`. Its current `Problem` model has no explicit status-classification-rationale field, although Step 2 §5 requires one; M5 must add that focused required field. `AnalysisOutput.evidence_registry_delta` is intentionally a registry delta; `EvidenceRegistry.merge()` rejects duplicate IDs rather than overwriting them.
- `validation.py` currently validates analysis references only as part of `validate_handoffs(research, analysis, evaluation)`. It lacks an Analysis-only boundary appropriate before M6 exists.
- M3 adapters normalize search leads and retrieved source records, retaining accessibility, dates, error/limitation state, and GitHub metadata without interpreting open/closed state as resolution.
- M4 supplies an injected two-pass `ResearchAgent`, a validated `ResearchOutput`, `ResearchTools`/`M3ResearchTools`, and a CrewAI construction boundary. It deliberately does not analyze alternatives, clustering, fixes, or status.
- M6 will consume M5's `AnalysisOutput`; M7 will own Flow invocation and JSON artifact persistence. M5 must not duplicate either responsibility.

The established `AnalysisOutput` delta design is compatible with the “one authoritative registry” decision only if every M5 run constructs and exposes the derived `research.evidence_registry.merge(analysis.evidence_registry_delta)` result, refuses conflicts, and later persistence writes that merged registry once. The delta is not a second source of truth.

## 4. Proposed technical approach

### Service boundary and one-pass shape

**Delegated choice, recommended:** add an `analysis_agent` package mirroring M4's narrow injected-service pattern. `AnalysisAgent.run(research: ResearchOutput)` first calls `validate_research_output`, invokes one structured analysis-planning/decision boundary, conducts only the bounded retrieval requested by that plan, assembles contracts deterministically, calls a new analysis-only validator, and returns an in-memory `AnalysisRunResult`.

`AnalysisRunResult` should contain `analysis_output` and `evidence_registry` (the merged registry). This makes the central-registry handoff unambiguous while retaining the established compact `evidence_registry_delta` serialization contract. It performs no Flow run, filesystem persistence, direct environment read, or automatic call back to Research.

Use one Analysis Agent with a single analysis pass. Its structured decision may propose clusters, alternative/counterevidence search queries, and candidate source URLs, but it cannot create trusted evidence merely by naming an ID, URL, status, fix, alternative gap, or quote. A deterministic assembler admits new evidence only after M3-shaped search-and-original-source retrieval and preserves unavailable material as unverified/limited rather than presenting it as proof.

### Clustering and problem assembly

The analysis prompt and internal decision types should require, for each proposed problem:

1. Constituent existing Finding IDs and a solution-neutral statement in the guide form: `[user] struggles to [task] because [friction], causing [consequence]`.
2. An explicit comparison of workflow, underlying friction, and consequence, followed by a concise merge rationale. Findings that share only a stack, keyword, or consequence are not merged. If the evidence cannot establish equivalence, retain separate problem proposals and document the split/ambiguity.
3. Existing supporting Evidence IDs only where they resolve through the input registry; independence context synthesized from the evidence's relationship fields without inflating repeated authors/comments.

Allocate deterministic run-local `P-001…` IDs in accepted decision order. Validate that each proposed Finding ID exists and that every copied supporting evidence reference is in the input registry or the safely merged new evidence set. Do not require a problem merely because a finding exists: an empty `problems` list is valid when the input has no analyzable findings, with the uncertainty retained in the input coverage and/or run diagnostics.

### Alternatives, currency, and counterevidence retrieval

**Delegated choice, recommended:** define a small analysis-tool protocol over M4's `ResearchTools` shape (`search(query)` and `extract(urls)`) rather than adding an API/client. For each proposed problem, issue only relevant, bounded query intents covering:

- a platform built-in or documented capability;
- directly relevant tools and actual workarounds;
- current-version/fix/closure context where a relevant report or issue exists; and
- a contrary experience or configuration/scope qualifier.

The plan/request does not impose a numeric minimum or an exhaustive market survey. The service records tool failure, empty results, inaccessible pages, absence of a verifiable release/fix, and unsuccessful counter-searches as limitations/research gaps. It never treats the lack of found counterevidence as corroboration.

For inspected analysis sources, create an `EvidenceItem` using the same source-faithfulness rules as M4: direct/canonical URL, provider dates/access date, short verbatim excerpt only when retrieved, observation distinct from optional interpretation, evidence class, independence rationale, verification status, and limitations. A source's `open`/`closed` metadata may be retained in an observation, but a “fixed” conclusion requires retrieved support such as a linked PR/release/current documentation or credible confirmation. New evidence must be registered in `evidence_registry_delta`, be allocated outside existing IDs, then merged with the input registry; neither copied items nor conflicting IDs are allowed.

For every `Alternative`, record what it actually addresses and classify its gap strictly as:

- `supported_gap` only for direct user reports or verifiable limitations relevant to the stated workflow;
- `unknown_gap` when an alternative was found/inspected but inadequacy is not established; or
- `need_substantially_met` when credible evidence shows it sufficiently addresses that need in context.

Evidence IDs for alternatives/counterevidence resolve against the merged registry. The problem's `current_resolution_uncertainty` must be nonblank whether resolution is evidenced, contradicted, unavailable, or unknown.

### Status and validation boundary

The agent selects only the four approved statuses. **Required M5 contract integration:** add a nonblank `status_rationale: str` to `Problem`, distinct from `clustering_rationale`, and include it in every serialized `AnalysisOutput`. It briefly explains why the selected status applies, while the existing `evidence_ids` and `counterevidence_ids` supply its resolvable supporting/contrary sources; `independence_context`, `current_resolution_uncertainty`, and `research_gaps` retain related qualification. The prompt must prevent treating multiple comments, votes, or closed issues as automatic corroboration/fixes.

Add a public `validate_analysis_output(research: ResearchOutput, analysis: AnalysisOutput) -> EvidenceRegistry` helper in `validation.py`. It should:

- call `validate_research_output`;
- merge the registry delta with the research registry and surface conflicts as `ContractValidationError`;
- reject duplicate Problem IDs, dangling Problem → Finding/Evidence/counterevidence references, dangling Alternative → Evidence references, and a missing/blank `status_rationale`; and
- return the merged registry on success.

Refactor `validate_handoffs` to reuse this helper, then retain its existing evaluation-specific validation. This prevents M5 from inventing empty Evaluation objects and ensures M6 cannot diverge from the same merge/reference rules. Structural validation remains deliberately unable to prove semantic clustering, source truth, independence, status appropriateness, or alternative adequacy; M8 human review retains those duties.

### CrewAI boundary and prompt guardrails

Create one non-running CrewAI Analysis Agent factory using M1's shared configurable LLM helper, `allow_delegation=False`, and M5 instructions. A small planner adapter may use `response_format` with M5-local decision models, as M4 does. Verify local constructor/output compatibility with fake factories only; do not claim the configured remote model is available.

The instructions must make these boundaries explicit: consume findings rather than rediscover them; cluster flexibly; investigate (not assume) alternatives/fixes/contrary experiences; append only inspected evidence; preserve unknowns; never propose an implementation/product, score user value, rate team fit, claim demand validation, invent citation IDs/URLs/quotes/dates, or rerun Research.

## 5. File change map

All paths are proposals for implementation after approval.

| Path | Change | Purpose |
|---|---|---|
| `src/problem_discovery_agents/analysis_agent/__init__.py` | Create | Narrow exports for the service, run result, and CrewAI factory/planner. |
| `src/problem_discovery_agents/analysis_agent/models.py` | Create | Strict M5-local structured decision, cluster, retrieval-intent, and diagnostic models; distinct from authoritative handoff contracts. |
| `src/problem_discovery_agents/analysis_agent/prompts.py` | Create | Versioned single-pass instructions encoding clustering, alternatives, counterevidence, status, provenance, and non-goals. |
| `src/problem_discovery_agents/analysis_agent/tools.py` | Create only if it improves clarity | Small injected protocol/adapter over M4/M3 `search`/`extract`; reuse `ResearchTools` directly if a second identical protocol would add no value. |
| `src/problem_discovery_agents/analysis_agent/service.py` | Create | One-pass sequencing, bounded source inspection, deterministic `P-###`/new evidence allocation, safe merge, contract assembly, and validation call. |
| `src/problem_discovery_agents/analysis_agent/crew.py` | Create | Non-running configured single-Agent factory and structured planner adapter; no Flow. |
| `src/problem_discovery_agents/validation.py` | Update | Add standalone analysis-handoff validator and make full validation reuse it. |
| `src/problem_discovery_agents/contracts.py` | Update | Add the required nonblank `Problem.status_rationale` field needed by Step 2 §5; retain all M2 registry and status semantics. |
| `tests/test_analysis_agent.py` | Create | Offline fixture-driven service, prompt, merge, source-status, and clustering behavior tests. |
| `tests/test_validation.py` | Update | Cover standalone analysis validation, delta merge conflicts, and all M5 reference namespaces. |
| `tests/fixtures/analysis_agent/...` | Create | Redacted deterministic research input, retrieved source, search failure, and expected-decision fixtures; no live sources or credentials. |
| `README.md` | Update | Describe the M5 in-memory Analysis Agent boundary and its offline test command, without claiming Flow/persistence exists. |
| `docs/plans/M5_IMPLEMENTATION_PLAN.md` | Create | Approved planning reference; it contains no runtime behavior. |

## 6. Ordered implementation tasks

1. Re-read the M2 contracts/validators and M3/M4 normalized retrieval interfaces. Confirm the installed CrewAI construction/structured-output surface with fake/injected factories only; report an actionable compatibility failure rather than changing model configuration.
2. Add required nonblank `Problem.status_rationale` to the M2 contract and update representative fixtures. Define strict M5-local analysis-decision models: proposed clusters, alternatives, counterevidence/currency retrieval intents, candidate source URLs, status choice/rationale inputs, and diagnostics. Keep all IDs as references to known records until deterministic validation.
3. Write the single-pass prompt with explicit A1/A3/A4/A5 rules and prohibitions. Add prompt-level regression tests for solution neutrality, unknown gaps, closed-not-fixed semantics, counterevidence retention, and no scoring/rerun.
4. Implement `validate_analysis_output`; refactor `validate_handoffs` to consume it. Add focused validation tests before the service so errors name the exact broken Problem/Finding/Evidence/Alternative reference or registry conflict and reject missing/blank status rationale.
5. Implement the injectable analysis service's clustering assembly. Validate the input research handoff, preserve uncertain splits, allocate stable Problem IDs, derive independence context from existing evidence, and allow valid scarcity/empty analysis without filler records.
6. Implement bounded alternative/current-status/counterevidence search and inspection through the existing M3-shaped interface. Map retrieved source records to new registry entries faithfully, allocate conflict-free IDs, merge once, and preserve failed/inaccessible retrieval as gaps rather than evidence-backed conclusions.
7. Assemble `Alternative` records and each `Problem` with linked support/counterevidence, required `status_rationale`, resolution uncertainty, gaps, and one approved status. Run standalone validation and expose the merged registry in the result.
8. Add the non-running CrewAI factory/planner adapter using the shared M1 model boundary; test construction and structured-plan parsing with fakes only.
9. Add redacted fixtures and offline tests, run focused then complete suites, and correct only M5 defects. Do not add Flow wiring, artifact persistence, scoring, report work, or live calls merely to satisfy a test.

## 7. Test and verification plan

All tests inject fake structured decisions and M3-shaped `search`/`extract` fakes (or `httpx.MockTransport` only for lower adapter regressions). They require no credentials, network, LLM, GitHub, or Tavily call.

- **Input and one-pass behavior:** valid `ResearchOutput` enters exactly one analysis service invocation; no internal Research Agent call occurs; valid empty/scarce input results preserve gaps rather than failing or inventing a problem.
- **Clustering:** fixture findings with the same workflow, mechanism, and consequence merge with all constituent Finding IDs and rationale; same stack but distinct underlying friction stay separate; ambiguous cases stay split with a documented uncertainty.
- **Alternatives/workarounds:** fixtures cover built-in, existing-tool, and actual-workaround records. Assert `supported_gap` has linked source support, merely discovered alternatives yield `unknown_gap`, and credible sufficiency yields `need_substantially_met`; no assumed barrier becomes an evidenced gap.
- **Counterevidence/current status:** test an open item with unresolved status, a closed duplicate/wontfix that is not called fixed, an evidenced release/confirmation that supports `outdated`, a contrary successful account/scope restriction that can support `contradicted`, and inaccessible/no-result checks that remain uncertainty. Every produced problem receives recorded counterevidence attempt/gap context.
- **Registry/provenance:** newly inspected analysis evidence receives stable non-conflicting IDs, exists only in the delta before merge, resolves for alternative/counterevidence references after merge, and leaves input evidence unchanged. Conflicting IDs, copied/unknown IDs, duplicate Problem IDs, dangling Finding/Evidence/counterevidence/Alternative references, and malformed enum/status values fail actionably.
- **Independence and statuses:** same-author/cross-post/reaction evidence remains dependent or uncertain; multiple comments and closed state cannot mechanically select `corroborated` or `outdated`. Tests cover all four allowed statuses, a nonblank evidence-linked `status_rationale`, and rejection of missing/blank rationale or an invented status.
- **Prompt/CrewAI boundaries:** assert the prompt forbids products, scores, demand claims, fabricated provenance, and automatic reruns; fake CrewAI factory receives M1's shared model boundary and `allow_delegation=False`; structured response parsing rejects malformed decisions.
- **Regression commands:** after implementation run `uv run pytest tests/test_analysis_agent.py tests/test_validation.py`, then `uv run pytest`. Do not state either passes until executed and observed. A separately authorized live run belongs after M7 and is not M5 acceptance evidence.

## 8. Acceptance matrix

| M5 acceptance check | Observable verification action | Expected result |
|---|---|---|
| Tests/examples distinguish over-merging from related but distinct frictions | Feed deterministic research fixtures for shared mechanism, shared stack-only, and ambiguous pairs through the analysis service. | Only the true common-friction findings merge; distinct/ambiguous pairs remain separate with constituent Finding IDs and merge/split rationale. |
| Tests/examples retain uncertainty and counterevidence | Use fixtures with inaccessible current context, failed contrary search, and a credible contrary source. | Gaps and limitations remain visible; counterevidence IDs are retained; each selected status has a nonblank `status_rationale`; absence of counterevidence never becomes corroboration. |
| Tests/examples handle closed-but-not-fixed | Supply closed duplicate/wontfix/stale fixtures and a separately evidenced fix/release fixture. | Closure alone does not label a problem fixed/outdated; only direct fix evidence can support that conclusion, otherwise resolution remains uncertain. |
| New evidence IDs resolve through the central registry | Add an inspected alternative/fix/counterevidence source to a research input, validate analysis alone, and inspect the returned merged registry. | Delta IDs do not conflict; every new ID resolves in the merged central registry and every alternative/counterevidence reference resolves; conflicts fail fast without overwrite. |

## 9. Risks, assumptions and decision requests

### Risks and mitigations

- **Semantic over-merging or accidental product ideation:** use a structured triad/rationale, split on uncertainty, strong prompt constraints, and representative fixture tests. Human M8 review remains required for semantic quality.
- **Unsupported alternative/fix claims:** source candidate proposals are not evidence; accept only inspected sources, classify gaps as unknown when support is absent, and retain retrieval failures.
- **Registry drift:** retain M2's delta plus `EvidenceRegistry.merge()` semantics, centralize standalone validation, and return the merged registry from the service. No ID collision is silently renamed or overwritten.
- **False resolution from issue metadata:** require linked/retrieved fix, release, documentation, or credible confirmation; otherwise record uncertainty. Test closed-but-not-fixed explicitly.
- **Tool/model API drift:** reuse M3/M4 injected boundaries and fake construction tests. A concrete incompatibility must surface an actionable error rather than a hidden fallback or new provider/tool.
- **Scope creep into M6/M7:** keep all Stage 1/2/report, Flow, filesystem, and live-run concerns outside M5.

### Assumptions and delegated implementation choices

- An in-memory `AnalysisRunResult` that exposes the safely merged registry is the smallest way to honor the central-registry policy while preserving the established `AnalysisOutput.evidence_registry_delta` contract. M7 will choose the JSON filenames and persist the merged registry once.
- Reusing M4's tool protocol is preferred over a parallel adapter. A thin M5-local wrapper is acceptable only if it expresses analysis query intent without duplicating transport behavior.
- Exact private decision-model names, query phrasing, deterministic ordering/ID allocation implementation, source-excerpt length within the existing short-quote rule, retry use, and diagnostic representation are implementation choices, provided IDs are stable for a fixed input/fixture order.

### Unresolved blockers / decision requests

None block approval. Two implementation checks remain deliberately empirical: the installed CrewAI release must accept the planned structured-output invocation, and M3's normalized source records must expose enough accessible metadata for a given alternative/fix conclusion. If either fails, implementation must report the concrete boundary deficiency and request the smallest compatible adjustment; it must not silently add a new agent, vendor, browser automation, or policy.

### Cross-milestone impact

M6 will consume the validated `AnalysisOutput` and its merged evidence registry to make evidence-linked four-dimension judgments; M5 must not pre-score or imply eligibility. M7 must run this service only after M4, persist inspectable research/analysis JSON plus the authoritative merged registry, and not turn analysis gaps into an automatic research rerun. M8 must manually inspect every problem's clusters, alternatives, current-status evidence, counterevidence, gaps, and source traceability as part of the required Analysis Quality and Evidence Integrity review.

## 10. Approval boundary

**Status: proposed, not yet approved.** This document plans M5 only. Do not implement M5 or begin M6–M8 until explicit human approval is given.
