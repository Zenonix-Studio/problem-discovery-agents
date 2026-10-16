# Problem Discovery Agents

An internal research pilot for finding evidence-grounded, underserved developer problems before proposing an open-source project.

## Current scope

The first manually invoked pilot examines **Developer Tools & Productivity** only. Its purpose is to produce auditable research for human review, not to select or build a product.

## Intended workflow

```text
Research Agent (broad discovery + evidence deepening)
  -> ResearchOutput JSON
  -> Analysis Agent (clustering, alternatives, counterevidence)
  -> AnalysisOutput JSON
  -> Evaluation Agent + deterministic Python checks
  -> EvaluationOutput JSON + Markdown report
  -> human review
```

The implementation uses a minimal CrewAI Flow with exactly these three specialized agents. It does not add a dashboard, database, scheduler, automatic research loop, or a report-writing agent.

## Research standards

- Start with user workflows and friction, not product ideas.
- Preserve direct URLs, dates when known, evidence excerpts, limitations, and the distinction between observations, inferences, and unknowns.
- Treat search snippets as leads; inspect original content before presenting it as verified evidence.
- Keep one authoritative evidence registry with stable IDs and traceability from evaluation to original source.
- Check alternatives, workarounds, fixes, and counterevidence. `open` does not prove an issue remains unresolved; `closed` does not prove it was fixed.

Stage 1 assesses four user-value dimensions—Problem Reality, Frequency / Recurrence, Alternative Gap, and Meaningful Benefit—on a `/12` scale only when all dimensions are scoreable. Otherwise the result is `Research needed`, with no total. Only fully scored `Strong` or `Promising` records with a clear user benefit may receive qualitative Stage 2 assessment.

## Status

M1 provides the project foundation and configuration boundary. M2 adds typed Pydantic handoff contracts, an authoritative in-memory evidence registry, and deterministic integrity/Stage 1 scoring checks. M3 adds small injected-client GitHub REST/Discussions GraphQL and Tavily Search/Extract adapters. M4 adds a fixture-testable two-pass Research Agent service: it accepts only the pilot category, runs broad discovery followed by deepening, constructs the authoritative `ResearchOutput`, and calls a research-only Finding-to-Evidence validator. M5 adds an injected, single-pass Analysis Agent service that clusters findings, checks bounded alternatives/current status/counterevidence, returns a validated `AnalysisOutput`, and exposes the safely merged in-memory evidence registry. M6 adds an injected Evaluation Agent service: it requires one evaluation for every analyzed problem, derives Stage 1 totals/labels and Stage 2 eligibility in Python, conditionally obtains Stage 2 from the same agent instance, and returns one structurally checked Markdown report in memory. M7 runs those existing services once in a CrewAI Flow and persists validated handoffs plus the final report.

M2 validators are structural: they resolve IDs, reject unsafe registry merges, derive the four-dimension Stage 1 `/12` result, and enforce the Stage 2 gate. They deliberately do not certify source truth, independence, clustering, or score quality; those remain research and human-review responsibilities.

## Local setup (M1)

Prerequisite: Python 3.11–3.13 and [uv](https://docs.astral.sh/uv/). The repository's development baseline is Python 3.12.

```bash
cp .env.example .env
# Edit .env with real values only when preparing an authorized future live run.
uv sync --all-groups
uv run pytest
```

Tests use only placeholder credentials and fake model wrappers; they do not call GitHub, Tavily, or an LLM provider.

### Research-tool boundary (M3)

`problem_discovery_agents.research_tools` exposes REST-first GitHub retrieval
(repository, issue/PR, issue comments, PR review submissions, and inline review
comments), a fixed GitHub Discussions GraphQL operation, and Tavily Search and
Extract. Adapters require a `Settings` instance plus an injected `httpx.Client`;
this keeps unit tests offline and prevents direct environment reads in tool code.

Search results are discovery leads only: their snippets are not verified source
content or evidence excerpts. Extracted material and incomplete/inaccessible
sources retain URLs, limitations, states and safe errors for later Research or
Analysis work. GitHub `open`/`closed` state is preserved as metadata only and is
not a conclusion that a friction persists or was resolved. Live use needs valid
credentials and later M4/M5 wiring; it is not a standalone evidence-verification
claim.

Run the M3 offline tests with:

```bash
uv run pytest tests/test_research_tools_http.py tests/test_github_tools.py tests/test_tavily_tools.py
```

### Research Agent (M4)

`problem_discovery_agents.research_agent.ResearchAgent` is intentionally an
injected service until M7 supplies Flow wiring. It receives a structured
two-pass planner and a M3-shaped `search`/`extract` tool boundary, so its tests
have no credentials or network calls. It accepts `ResearchRequest` with the
pilot category and optional workflow focus, then returns an in-memory
`ResearchRunResult` containing validated `ResearchOutput` plus query
diagnostics. Search leads must be inspected before they can become evidence;
inaccessible originals remain `unverified` with no excerpt.

Run the M4 offline tests with:

```bash
uv run pytest tests/test_research_agent.py tests/test_validation.py
```

### Analysis Agent (M5)

`problem_discovery_agents.analysis_agent.AnalysisAgent` accepts validated
`ResearchOutput`, uses an injected structured planner and the existing M3-shaped
`search`/`extract` boundary, and performs no Flow run or filesystem persistence.
Only sources returned as discovery leads and then inspected become analysis-registry
entries. `AnalysisRunResult` exposes both the delta-shaped `AnalysisOutput` and the
single safely merged registry. The agent records uncertainty rather than inferring a
fix from open/closed metadata, and it does not score candidates or request research
reruns.

Run the M5 offline tests with:

```bash
uv run pytest tests/test_analysis_agent.py tests/test_validation.py
```

### Evaluation Agent and report (M6)

`problem_discovery_agents.evaluation_agent.EvaluationAgent` accepts validated
Research and Analysis handoffs plus the exact merged M5 evidence registry. Its injected
planner proposes only the four Stage 1 assessments; Python derives every total, label,
and Stage 2 gate. The service rejects missing, duplicate, or unknown Evaluation Problem
IDs, so every analyzed record is retained. The same injected agent optionally assesses
eligible Stage 2 records and writes one in-memory Markdown report. The service checks
required report sections, evaluated Problem IDs, Evidence IDs, and direct registry URLs;
M7 remains responsible for Flow orchestration and artifact persistence.

Run the M6 offline tests with:

```bash
uv run pytest tests/test_evaluation_agent.py tests/test_validation.py
```

### Flow and artifacts (M7)

M7 writes each validated stage to a unique directory under `artifacts/` by default.
Successful runs contain `research_output.json`, `analysis_output.json`,
`evaluation_output.json`, `evidence_registry.json`, one `report.md`, and a safe
`run_manifest.json`. A failed run keeps only earlier validated artifacts and a
failed manifest; it never creates a later-stage artifact.

After configuring real credentials, manually invoke the pilot with:

```bash
uv run python -m problem_discovery_agents.run \
  --category 'Developer Tools & Productivity' \
  --focus 'CI/CD troubleshooting'
```

The focus is optional. Model usage/cost is recorded only when provider metadata
is returned; missing or incomplete totals remain explicitly unknown. M7 tests
use fakes and do not call external services:

```bash
uv run pytest tests/test_flow.py tests/test_artifacts.py tests/test_run.py tests/test_observability.py
```

Configuration is loaded only through `problem_discovery_agents.settings`, using these environment variables (or their counterparts in a local `.env`):

| Setting | Default / purpose |
| --- | --- |
| `PDA_GITHUB_TOKEN` | Required authenticated GitHub token for a future tool run. |
| `PDA_TAVILY_API_KEY` | Required Tavily key for a future tool run. |
| `PDA_LLM_API_KEY` | Required LLM provider credential. |
| `PDA_LLM_PROVIDER` | `openai`; the only currently configured provider adapter. |
| `PDA_LLM_MODEL` | `gpt-5.4-mini`; configurable without changing agent code. |
| `PDA_LLM_REASONING_EFFORT` | `medium`; accepted values are `none`, `low`, `medium`, `high`, and `xhigh`. |
| `PDA_LLM_BASE_URL` | Optional OpenAI-compatible endpoint. |
| `PDA_LOG_LEVEL` | `INFO`; one of `DEBUG`, `INFO`, `WARNING`, `ERROR`. |
| `PDA_RECORD_PROVIDER_USAGE` | `true`; future runs record provider-supplied usage/cost metadata only. |

Run the local, non-network configuration check after setting placeholder or real values:

```bash
uv run python -m problem_discovery_agents.config_check
```

It reports missing or unsupported configuration without revealing values, then constructs the local CrewAI wrapper without invoking it. This checks local package/argument compatibility only; it does not prove account access or remote model availability. OpenAI's current model documentation lists `gpt-5.4-mini` and supports `medium` reasoning effort; a live smoke test still requires separate authorization and credentials.

Never commit `.env` or real keys. The committed [`.env.example`](.env.example) contains placeholders only.

### Logging and usage-cost policy

M1 uses no telemetry service. Future application code should configure standard-library logging at its boundary and never log credentials or full provider responses. It may record input/output/reasoning token counts and estimated **model** cost only when supplied by provider metadata. Missing values remain unknown; search/retrieval costs are kept separate and are not estimated.

## First-pilot acceptance

Human review is mandatory for every generated problem record. Record Pass/Fail plus rationale for Evidence Integrity, Research Quality, Analysis Quality, Evaluation Consistency, and Report Usability.

M8 provides the [pilot runbook](docs/M8_PILOT_RUNBOOK.md), a copyable
[review record](docs/templates/M8_PILOT_REVIEW_TEMPLATE.md), and a conditional
[targeted fix/rerun log](docs/templates/M8_FIX_RERUN_LOG_TEMPLATE.md). A successful
Flow, manifest, or offline test suite is not pilot acceptance: complete the human
review record for every generated problem before treating the pilot as reviewed.
