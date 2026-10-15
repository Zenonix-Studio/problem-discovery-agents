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

The research policy and implementation contracts are agreed; implementation is pending. Before writing code, read [`AGENTS.md`](AGENTS.md) and the linked decision records in the required order. Credentials must be provided through configuration or environment variables and must never be committed.

## First-pilot acceptance

Human review is mandatory for every generated problem record. Record Pass/Fail plus rationale for Evidence Integrity, Research Quality, Analysis Quality, Evaluation Consistency, and Report Usability.
