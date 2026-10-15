# M1 Implementation Plan — Project Foundation & Configuration

## 1. Milestone goal and source references

**Goal:** establish the smallest reproducible Python foundation and external configuration for the manually invoked research pilot, without implementing agents, research logic, external calls, scoring, persistence, or Flow wiring.

This plan implements only the intent of [M1 — Project Foundation & Configuration](../milestones/M1_project_foundation_configuration.md), especially **Objective**, **In scope**, **Out of scope**, and **Acceptance checks**. Governing decisions are:

- `AGENTS.md` — **Configuration and tools**, **Coding-agent working agreement**, and the required minimal three-agent workflow.
- `docs/Problem_Discovery_Workflow_Architecture_v1.md` — §§3, 7–8 (minimal Flow is deferred; low-level tooling is delegated).
- `docs/Problem_Discovery_Step1_Research_Tools_Evidence_Quality_Decisions.md` — §2.2 (the eventual GitHub REST/GraphQL and Tavily tool set; authenticated credentials).
- `docs/Problem_Discovery_Step4_Implementation_Contracts_Decisions.md` — §2 (one externally configurable shared model, initial values, and honest usage/cost handling) and §5 (smallest working pilot).

The Research Guide and Steps 2–3 are also governing context. Their evidence, analysis, and Stage 1 scoring rules intentionally have no implementation in M1.

## 2. Scope and non-goals

### Included

- A conventional installable Python package, test configuration, and reproducible dependency-lock strategy sufficient for the planned CrewAI Flow, Pydantic contracts, GitHub HTTP access, Tavily access, and tests.
- Environment-based settings for GitHub authentication, Tavily, and the configured LLM provider/model/reasoning effort; a committed secret-free example environment file.
- A single initial shared model configuration: `gpt-5.4-mini` with reasoning effort `medium`, externally overridden without editing agent code.
- Minimal configuration validation, including clear aggregated error messages for absent required credentials, blank values, unsupported local provider/configuration options, and incompatible model-wrapper arguments.
- A deliberately small logging/usage-cost policy and documentation of developer setup, test, and configuration-check commands.
- Focused configuration tests with no network access or live credentials.

### Explicitly excluded

- Agent prompts, CrewAI agents/tasks/Flow execution, research queries, GitHub/Tavily calls, retrieval, persistence/artifact production, Pydantic evidence/output contracts, scoring, report generation, and any live provider diagnostic.
- Product ideation, additional agents, dashboard/database/scheduler, generic agent framework, and automatic Analysis-to-Research feedback.
- Claims that `gpt-5.4-mini`, a given provider, or a particular CrewAI release is available until installation and an opt-in authenticated compatibility check demonstrate it.

## 3. Current repository state and dependencies

Verified current state (2026-10-15): the repository contains policy/architecture/decision documents, milestone briefs, `README.md`, and no Python source tree, packaging metadata, dependency lock, environment example, tests, configuration, or earlier implementation plans. `git status --short` was clean when this plan was prepared. Therefore M1 has no reusable implementation artifacts or prior-milestone dependencies.

M1 establishes prerequisites for M2–M8, but does not pre-create their domain contracts or runtime modules. Later milestones should import settings through the M1 configuration boundary rather than reading environment variables directly.

## 4. Proposed technical approach

### Project and dependency baseline

**Delegated choice, recommended:** use `pyproject.toml` with a `src/` layout, Python 3.11+, `uv` for deterministic environment creation/locking, and a committed `uv.lock`. `pyproject.toml` remains the human-maintained declaration; `uv.lock` is the resolved reproducibility artifact. Document a standard-library/pip fallback only if `uv` is unavailable, while CI and acceptance verification use the locked `uv` path. This is a small, conventional foundation and avoids creating bespoke setup tooling.

Declare only dependencies needed by the approved future boundaries, subject to compatibility verification during implementation:

- runtime: CrewAI, Pydantic plus `pydantic-settings`, an HTTP client for GitHub REST/GraphQL, and the official Tavily Python client;
- development/test: pytest (and pytest configuration in `pyproject.toml`).

Do not add a GitHub SDK, database layer, observability platform, or unrelated CLI framework. Pin/resolve compatible versions through the lockfile, then record the chosen versions in the lockfile rather than asserting them here.

### Settings boundary

**Delegated choice, recommended:** create `problem_discovery_agents.settings` as the sole runtime environment/configuration boundary. Use a frozen Pydantic Settings model loaded from process environment and an optional local `.env` file (never committed). It should expose grouped settings rather than credentials scattered through future agents:

- `GitHubSettings`: required nonblank authenticated token.
- `TavilySettings`: required nonblank API key.
- `LLMSettings`: provider, model, reasoning effort, provider API credential, and optional provider base URL.
- `RunObservabilitySettings`: log level and an explicit policy flag/value for recording provider-reported usage/cost metadata only when available.

Recommended environment names are `PDA_GITHUB_TOKEN`, `PDA_TAVILY_API_KEY`, `PDA_LLM_PROVIDER`, `PDA_LLM_MODEL`, `PDA_LLM_REASONING_EFFORT`, `PDA_LLM_API_KEY`, optional `PDA_LLM_BASE_URL`, and `PDA_LOG_LEVEL`. Defaults apply only to the non-secret initial provider/model/reasoning effort values; required credentials have no default. Keep the settings prefix documented and configurable only if it does not obscure the simple local setup.

The initial defaults are `openai`, `gpt-5.4-mini`, and `medium`. Provider/model remain strings/configuration values, not constants embedded in future agent modules. M1 should permit only a small explicitly supported provider adapter set (initially the provider selected by the initial configuration); unknown providers or invalid/blank reasoning effort must fail with a message identifying the setting and supported option(s). Supporting another provider later is a deliberate adapter addition, not an unvalidated free-form promise.

Expose `load_settings()` plus a non-network `validate_runtime_configuration()` used by a tiny `python -m ...config_check` command. The validation should aggregate missing secrets and invalid fields, redact values, and return a non-zero exit code with remediation guidance. It must never print tokens/API keys or log them.

### Model compatibility and external uncertainty

M1 should isolate construction of the eventual CrewAI/LLM configuration in a small provider-adapter helper, but must not create agents or call a model. Implementation verifies that the installed CrewAI/provider wrapper accepts the selected configuration shape (including reasoning effort) using its documented constructor/introspection path, and converts an incompatibility to an actionable error naming the model, provider, installed package version, and alternative remediation (upgrade/select a supported configured model/remove an unsupported parameter only after a decision).

This verifies local dependency/API compatibility, not remote model availability or credentials. An authenticated, opt-in live compatibility smoke check belongs after the actual runtime/tool wiring exists; the docs must say so plainly. Unit tests use a fake adapter/wrapper to cover accepted and rejected argument combinations, never a provider request.

### Logging, tokens, and estimated cost

Use standard-library logging configured once at the application boundary. M1 logs configuration validation lifecycle and errors at safe levels but does not log secrets or full provider responses. Define a run-metrics interface/data shape now only if it is no more than a small typed helper: later Flow code may record model token usage and estimated model cost **only** when provider metadata supplies it. Missing metadata is recorded as `unknown`/absent, not estimated. Search and retrieval costs remain separate/unknown unless their provider exposes them. Do not implement cost calculation, telemetry export, or logging infrastructure in M1.

### Documentation and security

Commit `.env.example` containing keys and harmless defaults only; add `.env` and common virtual-environment/cache paths to `.gitignore`. Update the README with prerequisites, `uv` installation reference/command, local environment creation, copying/editing `.env`, install, tests, and configuration check. Explain that credentials are needed for a future live run but not tests, and that the model default is a starting configuration requiring compatibility confirmation.

## 5. File change map

All paths below are proposals for the implementation after approval.

| Path | Change | Purpose |
|---|---|---|
| `pyproject.toml` | Create | Package metadata, Python constraint, runtime/dev dependencies, pytest settings, and `uv`-compatible project definition. |
| `uv.lock` | Create (generated) | Committed resolved dependency graph for reproducible installs. |
| `.python-version` | Create | Declares the selected supported Python minor version for local tooling. |
| `.gitignore` | Create | Excludes `.env`, virtual environments, Python caches, coverage, and local artifacts; never ignores `.env.example`. |
| `.env.example` | Create | Secret-free settings template and documented initial model defaults. |
| `src/problem_discovery_agents/__init__.py` | Create | Minimal installable package marker/version exposure if useful. |
| `src/problem_discovery_agents/settings.py` | Create | Typed environment loading, redacted validation errors, and the provider/configuration boundary. |
| `src/problem_discovery_agents/model_config.py` | Create | Narrow non-network construction/compatibility adapter for the future shared model configuration. |
| `src/problem_discovery_agents/config_check.py` | Create | Small module entry point for local configuration validation; no agents or external calls. |
| `src/problem_discovery_agents/observability.py` | Create only if needed | Minimal safe logging setup and provider-metadata-only usage/cost representation; omit if it would be empty scaffolding. |
| `tests/test_settings.py` | Create | Settings defaults/overrides, missing/blank secret errors, redaction, and no-live-credential behavior. |
| `tests/test_model_config.py` | Create | Fake-wrapper compatibility and actionable failure behavior without provider access. |
| `README.md` | Update | Reproducible setup, commands, secure credential handling, expected configuration failures, and scope boundary. |
| `docs/plans/M1_IMPLEMENTATION_PLAN.md` | Existing | Retain as the approved implementation reference; no production behavior resides here. |

## 6. Ordered implementation tasks

1. Confirm the supported Python version and current CrewAI/provider package compatibility from their installed/documented interfaces before selecting exact constraints. Record the resulting dependency/lock strategy in `pyproject.toml`; do not install or lock a version based only on memory.
2. Create package metadata, `src/` package skeleton, `.gitignore`, `.python-version`, and the lockfile workflow. Keep dependencies at the minimal approved set.
3. Add the secret-free `.env.example` with the initial shared model defaults and all required future credential placeholders. Add comments distinguishing required live-run secrets from optional settings.
4. Implement typed grouped settings and an explicit configuration-error type. Load `.env` locally without requiring it in test/CI; reject blank required credentials; aggregate errors; redact all secret values.
5. Implement the narrow provider/model configuration adapter and the no-network configuration-check module. Validate provider choice, model/reasoning fields, and wrapper argument compatibility; make unverified remote availability explicit.
6. Add minimal safe logging setup and metadata-only usage/cost policy representation only where it directly supports settings/config checking. Avoid a telemetry subsystem.
7. Update `README.md` with exact install, environment, test, and configuration-check commands; document that no agent/research call exists yet and no secret may be committed.
8. Add tests and generated lockfile; run the verification plan from a clean environment. Correct dependency/configuration incompatibilities before treating the foundation as complete.

## 7. Test and verification plan

Unit tests (with `monkeypatch`/temporary environment and fake wrappers):

- Default non-secret LLM values resolve to `openai` / `gpt-5.4-mini` / `medium`; explicit environment overrides replace each without code changes.
- Missing or whitespace-only GitHub, Tavily, and LLM credentials yield a single clear actionable validation error; messages/output do not contain supplied secret test values.
- Invalid provider, invalid reasoning effort, blank model, malformed optional base URL, and a rejected provider-wrapper argument fail clearly and non-zero through the configuration-check entry point.
- Accepted fake wrapper configuration preserves the one shared model configuration; configuration loading itself makes no HTTP/provider/Tavily/GitHub calls.
- Provider usage/cost metadata is represented only when passed in; absent metadata remains explicitly unknown and search/retrieval cost is not folded into model cost.

Installation/reproducibility verification after implementation:

1. In a clean temporary environment, run `uv sync --all-groups` (or the documented exact equivalent) from the committed lockfile.
2. Run `uv run pytest` with no `.env` and confirm tests pass without live credentials.
3. Run the documented config check with deliberately absent/invalid variables and verify redacted actionable errors and non-zero exit.
4. Run it with test-only placeholder credentials plus valid initial settings and a mocked/constructor-only provider adapter; verify it performs no external request.
5. If an authorized, credentialed environment is available, perform the explicitly documented opt-in compatibility check separately and record whether the provider accepts the model/reasoning parameters. Its absence must not fail M1 tests.

Exact command spelling may change with the selected lock tool, but the README and CI/test command must use one coherent documented path.

## 8. Acceptance matrix

| M1 acceptance check | Observable verification action | Expected result |
|---|---|---|
| A fresh developer can install and run the test suite | Create a clean environment and execute the documented locked install then test command. | Dependencies resolve from committed metadata/lock and all configuration tests run successfully. |
| Secrets are not committed | Inspect tracked files (`git ls-files`), `.env.example`, `.gitignore`, and test fixtures; scan for credential-shaped values as a review aid. | No real token/key is tracked; `.env` is ignored; only placeholders are in the example and fixtures. |
| Config overrides work | Run settings tests and config check with isolated environment overrides for provider/model/reasoning/base URL. | Overrides take precedence over defaults; no agent source edit is required. |
| Missing/unsupported config is surfaced clearly | Exercise missing/blank secret, invalid provider/reasoning/model, and wrapper-argument rejection tests plus the command exit behavior. | Non-zero, actionable, redacted errors identify the setting/remedy; no network request or silent fallback occurs. |
| No live API keys required for tests | Execute the complete test suite in a clean environment with no `.env` and no credential variables. | Tests pass using fixtures/fakes only; no GitHub, Tavily, or LLM request is attempted. |

## 9. Risks, assumptions and decision requests

### Risks and mitigations

- **CrewAI/provider parameter drift:** `reasoning_effort` or model construction APIs may differ across releases. Mitigate with a pinned compatible lockfile, a thin adapter, constructor-level compatibility test, and an actionable configuration failure rather than guessing.
- **Remote model availability cannot be established offline:** distinguish local wrapper compatibility from authenticated runtime availability; document and defer the opt-in live smoke check.
- **Credential leakage:** use environment loading, redacted errors, placeholder-only files, and tests that assert test-secret redaction.
- **Foundation creep:** keep the package limited to configuration and safe setup; reject Flow/agent/tool/persistence work until its milestone.

### Assumptions and delegated implementation choices

- Python 3.11+ with `uv` and `src/` layout is the recommended minimal baseline; another conventional lock tool is acceptable only if it provides the same committed, reproducible workflow and is documented consistently.
- `openai` is the initial provider-name convention because the initial model name requires a provider setting, but this is a configuration default—not a verified availability claim or a new policy decision.
- A small explicit provider adapter is preferable to accepting arbitrary providers before their credential names and argument mappings are verified.
- Exact package versions, Pydantic class names, error text, module names, and CLI spelling remain implementation choices within this plan.

### Unresolved blockers / decision requests

None block approval of M1. The exact package versions and provider-wrapper API must be verified during implementation; that is an M1 verification task, not a policy choice. If verification shows `gpt-5.4-mini` or `medium` is unsupported by the selected provider/CrewAI combination, implementation must report the concrete incompatibility and request a configuration decision rather than silently changing the agreed initial values.

### Cross-milestone impact

M2–M8 should use the M1 settings/configuration boundary, reuse its safe logging and usage-metadata policy, and retain the single configurable shared model unless a later human decision authorizes a demonstrated per-agent need. M1 deliberately leaves evidence contracts, tools, agents, Flow wiring, artifact paths, and report behavior to their specified later milestones.

## 10. Approval boundary

**Status: approved for M1 implementation by human review on 2026-10-15.** This document governs only M1. Do not begin M2 without a new explicit approval.
