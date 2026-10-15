# Problem Discovery Workflow — Step 1 Decisions: Research Tools & Evidence Quality

**Status:** Agreed decisions for Step 1 (R1, R2, R4, R6)  
**Date:** 2026-10-14  
**Purpose:** Decision record / handoff for later architecture sessions and the coding agent. This is **not** an implementation specification or a proposal for the eventual open-source product.

## 1. Governing context and boundaries

- The `Problem_Discovery_Research_Agent_Guide.md` remains the **authoritative research policy**. The `Problem_Discovery_Workflow_Architecture_v1.md` defines the agreed minimal orchestration. If this decision record is silent, follow those documents.
- Goal: a **minimal, manually run CrewAI Flow** to find evidence-grounded, underserved developer problems, not to build a sophisticated research platform.
- Pilot category: **Developer Tools & Productivity**. The other two guide categories are deferred until the pilot is manually reviewed.
- Preserve the existing agents: **Research Agent** (two passes), **Analysis Agent** (one pass), **Evaluation Agent** (Stage 1 before Stage 2). No additional agent, controller, automatic research feedback loop, database, or dashboard.
- **Problem first, solution later.** No product ideas or OSS project proposals at this phase; visibility/stars remain secondary to user value.
- Research workload caps remain **provisional, not quotas**: up to approximately 8–10 candidate signals in Pass 1 and approximately 4–5 researched in Pass 2. Fewer are acceptable. Never fill quotas with weak or invented evidence.

## 2. R1 — Sources and tools (agreed)

### 2.1 Research sources and priority

- **GitHub-first:** Issues, Discussions, pull request conversations, and associated firsthand developer reports are primary discovery sources.
- **Supporting sources:** Reddit, Stack Overflow, developer forums and communities.
- **Official documentation, changelogs and migration guides:** useful for context, capabilities, fixes and limitations; documentation alone does not demonstrate firsthand user pain.
- An engine search result/snippet is **a discovery lead, not verified evidence**. Inspect the underlying source whenever possible.

### 2.2 Minimal tool set

| Tool | Agreed role | Approach |
|---|---|---|
| GitHub REST API | Issues, PRs, comments, metadata | **REST-first** |
| GitHub GraphQL API | Discussions and needed associated data | Use selectively, especially for Discussions |
| Tavily Search | General web search and discovery outside GitHub | Single web-search provider for v1 |
| Tavily Extract | Retrieve original web page content for evidence inspection | Pair with Tavily Search |

- GitHub access will use authenticated token access; Tavily uses an API key. Credential storage and exact implementation are deferred.
- The REST + GraphQL split is **within one Research Agent**, not extra agents.
- No initial Brave Search, Firecrawl, dedicated Reddit/Stack Overflow integration, or browser automation. Add tools **only if the pilot demonstrates a concrete retrieval or evidence-quality limitation**.
- Treat provider extraction as fallible: partial pages, missing comments, blocked sites, stale search results, or inaccessible pages must not be represented as fully verified source evidence.

## 3. R2 — Search strategy and user input (agreed)

### 3.1 User-facing research scope

**Decision: Category-first + Optional Focus + Bounded Exploration.**

- **Required input concept:** research category, e.g. `Developer Tools & Productivity`.
- **Optional input concept:** workflow focus, e.g. `CI/CD troubleshooting`.
- If focus is omitted, Research Agent maps a bounded variety of developer workflows and explores potential friction within them.
- If focus is present, Research Agent concentrates research within that workflow, without presupposing a particular problem.
- These are **conceptual input behaviors**, not final YAML/Pydantic field names or schemas.
- Broad discovery is a **sample**, not exhaustive category coverage. Record which workflows were examined, which were not, and the resulting coverage limitations. No findings in an examined subset must not be described as proof that the overall category has no problems.

### 3.2 Query generation

**Decision: Workflow-driven + friction-oriented + adaptive query variation.**

- Generate searches from **workflow/task + friction or failure expression + relevant source**.
- Prefer firsthand expressions of broken workflows, repeated manual work, errors, slowness, uncertainty, poor reliability, confusing setup and actual workarounds. These are search prompts, **not asserted problems**.
- Vary queries by observed failure mechanism, user wording, workflow subtask and source; do not rely on a single keyword, hype phrase, or predefined technology trend.
- Allow observed source evidence to inform follow-up queries, but do not treat speculative agent-generated hypotheses as confirmed pain.

### 3.3 Pass behaviors and bounds

- **Pass 1 — Broad Discovery:** map users and recurring tasks; explore multiple workflows before spending all effort on a single interesting result; collect concrete firsthand friction signals. Prefer **coverage before depth**.
- **Pass 2 — Evidence Deepening:** focus on the selected researchable signals; seek additional independent firsthand reports and context. Prefer **evidence depth over breadth**.
- A signal eligible for deeper research has an identifiable user/workflow, at least one relevant direct source, and concrete investigable friction. This is **not** a validated problem or a Stage 1 score.
- Stop unproductive query variations instead of repeating them indefinitely; record unsuccessful searches and gaps.
- Do **not** hardcode new per-workflow/per-query quotas or retry counts before pilot evidence shows they are necessary. The existing provisional workload caps stand.

## 4. R4 — Independent corroboration (agreed)

**Decision: Seek two independent firsthand reports where feasible; this is a research target, not an exclusion rule.**

- Pass 2 deliberately searches for separate developers' **own experience of the same underlying friction or failure pattern**.
- Multiple firsthand accounts can occur within **one GitHub issue thread**. Separate URLs or platforms are not necessary for independence.
- Multiple comments by the same author, cross-posted versions of one report, quotations of another report and generic reactions/upvotes do **not** become independent firsthand reports by being numerous.
- Distinct authors and, where feasible, distinct projects or contexts provide stronger corroboration; distinct platform or repository is useful but **not mandatory**.

Classify the relationship of evidence items to other reports:

| Classification | Meaning |
|---|---|
| `independent` | A distinct firsthand user experience supports the same friction, with a defensible independence rationale. |
| `uncertain` | Related report exists, but whether it represents a separate firsthand experience cannot be established. |
| `dependent` | Duplicate/cross-post, same author's repeated account, quotation/rebroadcast, or otherwise not a separate firsthand experience. |

- Record why each classification was chosen; avoid intrusive identity matching or personal-information collection.
- **A single credible report can remain a hypothesis / `needs_validation`**; do not automatically reject a rare but serious reported problem. Neither one nor two reports alone establishes product demand.
- Keep the Research Agent's **evidence relationship classification** distinct from the Analysis Agent's later **problem status** (`corroborated`, `needs_validation`, `outdated`, `contradicted`, as applicable). `corroborated` does not mean demand validated.

## 5. R6 — Source verification (agreed)

**Decision: Four checks + “Fail Transparently”; distribute responsibilities across existing agents and deterministic checks.**

| Rule | Check | Primary responsibility |
|---|---|---|
| R6.1 — URL accessibility | Can the underlying original resource/content actually be accessed? | Research Agent |
| R6.2 — Content support | Does the fetched material directly support the specific observation or claim? | Research Agent |
| R6.3 — Date context | Record source publication/post date if known and access date; use update dates when available without equating them to persistence. | Research Agent |
| R6.4 — Resolution/current status | Check fixes, closed reasons, linked PRs, current versions, changelogs and counterevidence; determine if solved, continuing or uncertain. | Analysis Agent |

### 5.1 Evidence interpretation

Keep the following distinct:

- **Observed:** what original content actually states or demonstrates.
- **Inferred:** an interpretation supported by, but not directly identical to, what the source states.
- **Unknown:** unverified or missing information.

Record direct URL, source type, original relevant context and claim supported, publication/post date when known, and access date. Do not invent unknown dates, quotations, claims or metrics. Where available, an `updated_at` value is metadata, **not proof the issue still exists**.

### 5.2 Resolution semantics

- `open` does not conclusively prove unresolved pain.
- `closed` does **not** prove a fix: duplicates, stale closures, `wontfix` and other closure reasons must be differentiated.
- “Fixed” needs actual supporting evidence (e.g., identified fix/PR/release or credible confirmation); current status can remain **unknown** when not verifiable.
- Recently resolved/outdated reports must not be marketed as ongoing gaps. Preserve counterevidence and contradictory findings rather than suppressing them.

### 5.3 Fail transparently

- **Inaccessible original source:** record as inaccessible/unverified, not verified firsthand evidence based only on search snippets.
- **Retrieved text does not support claim:** do not use that source to support the claim.
- **Unknown publication date:** preserve the source with explicit date uncertainty; make no unsupported freshness assertion.
- **Unknown resolution:** mark uncertainty; do not silently classify as fixed or ongoing.
- **Incomplete or failed retrieval:** report what was unavailable and the consequent limitations; do not manufacture content.

### 5.4 Responsibility split

- **Research Agent:** source access, source-claim correspondence, dates, evidence observations vs inferences and limitations.
- **Analysis Agent:** currency, fixes/resolution, workarounds, alternatives, counterevidence and problem-level uncertainty.
- **Deterministic Python rules:** basic required-field, provenance, classification and structural consistency checks. **They cannot guarantee semantic truth** or replace manual review.
- No separate Verification Agent/service, numerical confidence engine or automated Research ↔ Analysis loop is required for v1.

## 6. Traceability and pilot review implications

- Preserve direct source links and stable source/finding IDs across agent handoffs. The coding agent will define the final contracts later.
- Keep independent evidence distinct from reactions, duplicate reports and indirect citations.
- Intermediate structured **JSON** outputs and the final **Markdown** report should make provenance and missing evidence inspectable.
- During the first pilot, manually inspect **every generated problem record** and its referenced evidence/source context, alongside independence claims, unresolved statuses, workflow coverage, and whether claimed findings remain source-supported. This later, stricter review requirement is reconciled with Step 4's full-review decision.
- Neither high source counts nor positive issue reactions imply demand, user adoption or a validated OSS opportunity.

## 7. Historical open decisions (resolved by later records)

At the time of this Step 1 decision, the following remained open. They are retained for provenance only; later decision records and `AGENTS.md` resolve them.

- Concrete prompt templates, query counts, retry policies, hard time/search budgets and provider-specific response parsing.
- Exact Pydantic field names, persistence layout, CrewAI Flow wiring, file naming, credential management and fallback implementations.
- Stage 1 score anchors and missing-evidence thresholds, and the detailed Analysis Agent clustering/alternatives rules (scheduled for later roadmap steps).
- Whether an additional search/retrieval provider is required; consider only after documented pilot problems.

**Historical next step:** Step 2 — Analysis rules (A1, A3, A4, A5). This step is complete; see the Step 2 decision record.
