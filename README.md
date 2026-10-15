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

M1 provides the project foundation and configuration boundary. Agents, research tools, contracts, scoring, persistence, and Flow orchestration are not implemented yet. Before changing later milestones, read [`AGENTS.md`](AGENTS.md) and its linked decision records in the required order.

## Local setup (M1)

Prerequisite: Python 3.11–3.13 and [uv](https://docs.astral.sh/uv/). The repository's development baseline is Python 3.12.

```bash
cp .env.example .env
# Edit .env with real values only when preparing an authorized future live run.
uv sync --all-groups
uv run pytest
```

Tests use only placeholder credentials and fake model wrappers; they do not call GitHub, Tavily, or an LLM provider.

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
