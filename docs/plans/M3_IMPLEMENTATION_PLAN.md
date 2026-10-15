# M3 Implementation Plan — Research Tools Integration

## 1. Milestone goal and source references

**Goal:** provide a deliberately small, reliable, offline-testable adapter surface for the Research and Analysis agents to discover and retrieve original source material. The adapters must preserve source provenance, metadata, access limitations, partial results, and provider errors; they must not judge evidence, cluster findings, prompt agents, or make research decisions.

This plan implements only [M3 — Research Tools Integration](../milestones/M3_research_tools_integration.md): its **Objective**, **In scope**, **Out of scope**, and **Acceptance checks**. The governing requirements are:

- `AGENTS.md` — **Configuration and tools**, **Research and analysis rules**, **Data contracts and provenance**, and **Deterministic checks and error behavior**.
- `docs/Problem_Discovery_Research_Agent_Guide.md` — §3 (**Boundaries and research sources**) and §7 (**Research workflow**).
- `docs/Problem_Discovery_Workflow_Architecture_v1.md` — §§3–5 (three-agent Flow, Research/Analysis responsibility split, and traceability).
- `docs/Problem_Discovery_Step1_Research_Tools_Evidence_Quality_Decisions.md` — §2.2 (approved tool set), §§3.2–3.3 (two-pass research bounds), §5 (source verification and fail transparently).
- `docs/Problem_Discovery_Step2_Analysis_Rules_Decisions.md` — §§3–5 (alternatives, counterevidence, and the distinction between an issue state and a resolution judgment).
- `docs/Problem_Discovery_Step4_Implementation_Contracts_Decisions.md` — §2 (tools unchanged), §3.1–3.2 (registry/provenance), and §3.6 (honest uncertainty vs contract failure).

## 2. Scope and non-goals

### Included

- Authenticated, REST-first GitHub access for issue/PR records, issue comments, review comments, and repository metadata; bounded pagination only for collection endpoints that need it.
- A narrow, fixed-query GitHub GraphQL adapter for Discussions and required associated metadata; it is not a general GraphQL client.
- Tavily Search for non-GitHub discovery and Tavily Extract for original-page retrieval.
- Shared, normalized result records retaining direct/original URLs, returned content or snippets, publication/update metadata where returned, access time, pagination/incompleteness, and normalized retrieval errors.
- Bounded retry behavior for transient transport failures, `429`, and `5xx`, including transparent exhausted-retry results.
- HTTP-mocked unit tests and fixtures for success, missing/partial content, malformed/limited metadata, `401`, `403`, `429`, and `5xx` behavior. Tests must work with no credentials or network.
- Documentation/configuration adjustments required to use the existing `Settings` credential boundary safely.

### Explicitly excluded

- Evidence-item creation or quality/independence judgments, evidence-registry persistence/merge changes, deduplication, research hypotheses, prompt templates, query strategy, agent code, CrewAI Flow wiring, artifacts, scoring, reports, and live calls.
- Additional vendors, direct Reddit/Stack Overflow APIs, browser automation, monitoring, a generic HTTP/agent framework, a database, dashboard, or automated Analysis → Research cycle.
- Treating a Tavily snippet as inspected source evidence, treating inaccessible/partial content as verified, or treating GitHub `open`/`closed` state as proof a friction is unresolved/resolved.

## 3. Current repository state and dependencies

Verified on 2026-10-15:

- M1 and M2 are implemented. `pyproject.toml` already declares `httpx`, `tavily-python`, Pydantic settings, CrewAI, and pytest; `uv.lock` exists.
- `src/problem_discovery_agents/settings.py` is the sole environment boundary and already exposes nonblank secret `github_token` and `tavily_api_key`. No tool module, HTTP client, external call, agent, Flow, or persistence implementation exists.
- `src/problem_discovery_agents/contracts.py` supplies strict `EvidenceItem`, `EvidenceRegistry`, `VerificationStatus`, and provenance contracts; `validation.py` supplies M2 handoff validation. M3 must return source/retrieval records rather than prematurely manufacture `EvidenceItem` judgments. M4/M5 will deliberately convert inspected results into those contracts.
- Existing M1/M2 tests are offline. `README.md` and `.env.example` document required credential names but not tool invocation.
- `docs/plans/M1_IMPLEMENTATION_PLAN.md` and `docs/plans/M2_IMPLEMENTATION_PLAN.md` are approved historical plans. This M3 plan was reviewed and explicitly approved for implementation on 2026-10-15.

M3 depends on M1 settings and M2 contracts but does not require an LLM/provider runtime or live credentials to test. M4 (Research) and M5 (Analysis) are its consumers; M7 later owns JSON artifact persistence.

## 4. Proposed technical approach

### Boundary and return model

**Delegated implementation choice; recommended:** create a small `research_tools` package with provider-neutral immutable Pydantic/dataclass result models and provider-specific adapters. Keep raw provider payloads out of downstream agent contracts except for a deliberately bounded `raw_context`/metadata mapping when necessary for audit/debugging. A result must carry:

- provider and request kind; original/requested URL(s) and canonical returned URL where known;
- `retrieved_at`, nullable source publication/update dates, source title/type/context, and returned text/snippet separately;
- a retrieval state such as `complete`, `partial`, `inaccessible`, or `failed`, plus pagination/completeness information;
- a structured, non-secret error record (provider, HTTP status when available, category, safe message, retryability); and
- enough GitHub state metadata (`state`, `closed_at`, linked/returned URLs) to inspect later, while documenting that it is not a resolution conclusion.

Use `complete` only when the requested provider response was obtained as expected. A Search result is a **lead** even when its API request completes: model it as a distinct result/item type whose `snippet` never implies a verified excerpt or firsthand evidence. Tavily Extract has separate returned text and per-URL status so a batch can be partially successful. `inaccessible`/`partial` must preserve the URL and error/limitation rather than disappearing.

Expected remote failures return normalized result/error data for agent reporting. Invalid caller input, impossible response shapes that violate the adapter's declared contract, or unavailable required settings should surface an actionable local exception; no credential values may be included. This separates real-world access uncertainty from programming/configuration defects.

### HTTP, authentication, retries, and pagination

**Delegated implementation choice; recommended:** use the already declared `httpx` directly through an injected synchronous `httpx.Client`/transport protocol, rather than relying on provider SDK response shapes. This makes request headers, pagination, error normalization, and offline `MockTransport` tests deterministic. The adapters must obtain tokens only from `Settings`, never from environment reads or method arguments.

- GitHub requests use the configured token, GitHub API version/accept headers, and explicit user agent. Tavily requests use its API key only in the provider-approved header/body mechanism.
- Use narrow timeout values and a small constant retry policy (recommend at most two retries after the initial attempt) for transport errors, `429`, and `5xx`; do not retry `401`, `403`, `404`, or validation errors. Respect a parsable `Retry-After` only up to the configured bounded delay; otherwise record the limit/exhaustion. Exact timeout/backoff values and whether a sleep function is injected are implementation details, but tests must not sleep.
- Parse GitHub REST `Link` pagination only on collection operations; for GraphQL Discussion comment connections, inspect and preserve `pageInfo` (`hasNextPage` and cursor) under an explicit item/page cap. In either API, expose `next_page_available`/`pages_fetched` and `truncated` when the caller-selected cap is reached. Do not silently fetch an unbounded repository history or Discussion thread.
- Do not add a new configuration subsystem. If base URLs, timeouts, max pages, or retry limits need test/deployment overrides, add small validated non-secret fields to the existing `Settings` model with conservative defaults and document them. Otherwise keep them module constants/private constructor options. No new secret names are needed.

### Provider adapters

Proposed public capabilities are intentionally narrow and can use equivalent names:

| Adapter | Capabilities | Normalized behavior |
|---|---|---|
| `GitHubRestAdapter` | repository metadata; an issue/PR record; issue comments; PR review submissions; PR review comments; optionally a bounded issue/PR search/list needed for discovery | Preserve API HTML URL, `created_at`/`updated_at`/`closed_at`, author/context, review/body text where present, pagination state, and API state. A review submission and an inline review comment remain distinct returned records. Recognize an issue response that represents a PR from GitHub metadata; do not infer resolution. |
| `GitHubDiscussionsAdapter` | fetch/list a repository Discussion and its requested associated metadata/comments through a fixed GraphQL operation | Fetch Discussion comment connections with an explicit bounded page/item limit, and preserve `pageInfo`/truncation alongside discussion URL, timestamps, body/comment data where returned, GraphQL errors, and partial `data`. No arbitrary caller-provided operation strings. |
| `TavilyAdapter` | Search queries and Extract for one or more explicit original URLs | Search returns lead records with result URL/title/snippet and provider date/score only as provider metadata. Extract returns per-URL original content, author/date metadata where returned, and per-URL incomplete/inaccessible state. It never promotes snippets to excerpts. |

The adapters provide content/context to M4/M5, which remain responsible for source-claim correspondence, short faithful excerpts, observed/inferred/unknown distinctions, evidence class, and the M2 registry. Analysis will use the same surface to seek alternatives, fixes, and counterevidence; no automatic rerun is introduced.

### Observability and documentation

Use the existing safe logging boundary only for request lifecycle identifiers/status categories and retry attempts. Never log tokens, API keys, complete fetched pages, or full GraphQL request variables/responses at normal levels. Update the README with the local/offline test command and a concise statement that live tool use requires both configured credentials and later M4/M5 wiring; it is not a standalone evidence-verification claim. Preserve `.env.example` secrets as blank placeholders.

## 5. File change map

All paths are proposals for implementation after approval; exact module splitting may stay smaller if it remains clear.

| Path | Change | Purpose |
|---|---|---|
| `src/problem_discovery_agents/research_tools/__init__.py` | Create | Deliberately small public adapter/result exports. |
| `src/problem_discovery_agents/research_tools/models.py` | Create | Strict normalized source, page, search-lead, extract, pagination, retrieval-state, and safe-error types; distinct from M2 `EvidenceItem`. |
| `src/problem_discovery_agents/research_tools/http.py` | Create | Injected-client boundary, safe request execution, transient retry, status/error normalization, and no-secret logging helpers. |
| `src/problem_discovery_agents/research_tools/github.py` | Create | REST-first repository/issue/PR/comment/metadata and bounded-pagination access; fixed GraphQL Discussions capability if keeping it together remains readable. |
| `src/problem_discovery_agents/research_tools/tavily.py` | Create | Tavily Search lead and Extract original-content operations, including per-source partial failures. |
| `src/problem_discovery_agents/settings.py` | Update only if needed | Add narrowly scoped validated non-secret tool transport settings or factories, retaining the M1 sole-settings boundary and credential redaction. |
| `tests/test_research_tools_http.py` | Create | Retry classification, bounded retry exhaustion, safe normalized errors, injected client behavior, and no credential leakage. |
| `tests/test_github_tools.py` | Create | REST normalization for issue/PR, issue comment, PR review submission, and inline review-comment records; metadata/dates; missing body/content; REST `Link` and GraphQL Discussion-comment bounded pagination; GraphQL success/partial/error; and `401/403/429/5xx` fixtures. |
| `tests/test_tavily_tools.py` | Create | Search-as-lead behavior, Extract content normalization, missing date/content, per-URL partial retrieval, and provider error fixtures. |
| `tests/fixtures/research_tools/…` | Create | Minimal redacted GitHub REST/GraphQL and Tavily payloads representing expected and failure cases. |
| `README.md` | Update | Tool boundary, credential prerequisites, offline verification command, and explicit snippet/issue-state limitations. |
| `.env.example` | Update only if settings change | Document only approved non-secret transport options; never add actual credentials. |
| `docs/plans/M3_IMPLEMENTATION_PLAN.md` | Create | This proposed planning artifact; no runtime behavior. |

## 6. Ordered implementation tasks

1. Re-read M1 settings/M2 contracts and inspect the resolved package APIs before coding. Confirm the installed `httpx` and Tavily dependency compatibility; do not assume SDK response shapes or live provider access.
2. Define and test the provider-neutral normalized result/error/pagination records. Establish the invariant that a Tavily Search lead cannot be passed off as retrieved original content, and that all partial/inaccessible results retain a direct URL and limitation.
3. Add the injectable HTTP execution boundary with per-provider auth construction, timeout/retry policy, safe logging, and status classification. Keep local configuration errors distinct from normalized remote failures.
4. Implement GitHub REST operations for the bounded surface, including PR review submissions as well as inline review comments. Normalize absent metadata/body/review text, parse bounded `Link` pagination, and cover issue-vs-PR metadata without resolution inference.
5. Implement the fixed GitHub Discussions GraphQL operation(s), including bounded comment-connection traversal with `pageInfo`/truncation, partial `data` plus `errors`, malformed/error responses, and the same safe authentication/error policy. Keep arbitrary query execution private/out of scope.
6. Implement Tavily Search and Extract normalization. Test search snippets as discovery-only leads and Extract per-URL partial/inaccessible behavior without transforming either into M2 evidence records.
7. Make the smallest necessary settings/README/.env-example changes. Verify added settings are validated/redacted and no production module reads environment variables directly.
8. Add redacted fixtures and offline mocked tests for every acceptance/failure path. Run the focused tests plus the existing suite; correct regressions without expanding into agents or persistence.
9. Optionally, and only with authorized real credentials after unit tests pass, perform a manually initiated smoke check against one non-sensitive public resource. Record only capability/error outcome, never source content or secrets. Lack of authorization must not block M3 completion.

## 7. Test and verification plan

Unit tests use `httpx.MockTransport` (or an equivalent injected fake) and local fixtures only; they set placeholder secrets through `Settings` fixtures and make no outbound connection.

- GitHub REST: assert request method/path/header selection, normalized repository/issue-or-PR/issue-comment/PR-review-submission/inline-review-comment metadata and canonical URLs, nullable date/body handling, and bounded `Link` pagination including a visibly truncated result.
- GitHub GraphQL: assert the adapter sends only its fixed Discussion operation/variables; normalize a complete discussion, partial `data` with GraphQL errors, and no-data errors without dropping useful context. Exercise multi-page comment `pageInfo`, a configured cap, and visible truncation rather than silently returning only the initial connection page.
- Tavily: assert Search emits `lead` records with snippets separate from retrieved text/verification semantics; assert Extract preserves original URL, returned content/date where present, and one inaccessible URL beside one successful URL in a partial batch.
- Failure matrix for both providers: `401` → authentication failure, `403` → forbidden/access-limited, `429` → retryable/rate-limited then bounded exhausted result, and `5xx`/transport failure → retryable upstream failure then bounded exhausted result. Verify non-retryable statuses are not retried and tests do not wait.
- Missing/odd content: empty body, absent source date, null extraction text, malformed optional fields, absent pagination headers, and incomplete provider records become explicit nullable/partial values or an actionable parser contract error—never invented content/date.
- Security/configuration: missing settings still produce M1-style redacted actionable errors; request/error logging and normalized errors do not contain placeholder secret values; no adapter reads `os.environ` directly.
- Regression: run `uv run pytest`; retain passing M1/M2 contract, registry, validation, model-config, and settings tests. If a local tool command is added later, verify it against mocks only.

Post-implementation commands (exact test paths may follow the implemented names):

```text
uv run pytest tests/test_research_tools_http.py tests/test_github_tools.py tests/test_tavily_tools.py
uv run pytest
```

An opt-in live smoke test, if separately authorized, is supplementary only and must report provider connectivity/access limitation honestly. It is not an acceptance substitute for deterministic offline tests.

## 8. Acceptance matrix

| M3 acceptance check | Observable verification action | Expected result |
|---|---|---|
| Mocked tests verify request/response normalization | Run GitHub REST (including PR review submissions and inline review comments), bounded GitHub Discussions GraphQL comment pagination, Tavily Search, and Tavily Extract fixture tests. | Returned records retain original/canonical URL, content/context or lead snippet, dates when supplied, access time, and provider-specific provenance without copying into `EvidenceItem`; capped REST/GraphQL collections visibly expose incompleteness. |
| Missing source content is handled | Feed GitHub/Tavily fixtures with absent/empty body/text and unknown dates. | Result exposes nullable missing fields and a limitation/partial state; it invents neither excerpt nor date and does not call the material verified evidence. |
| Partial retrieval is handled | Return a mixed Tavily Extract batch and GraphQL partial data/errors; exercise a page-cap pagination response. | Successful material remains available, inaccessible/incomplete material remains explicitly identified by URL/error, and truncation/partial status is inspectable. |
| `401`, `403`, `429`, and `5xx` responses are handled | Mock each status for both adapter families and track attempts. | `401`/`403` surface safe actionable auth/access results without inappropriate retry; `429`/`5xx` retry only within the configured bound then return a safe rate-limit/upstream failure with status/limit context. |
| Source metadata is handled | Use fixtures with GitHub `created_at`/`updated_at`/`closed_at`/state and Tavily date/title/URL variations. | Known dates and state are preserved; unknowns stay null; update/issue-state metadata is not represented as proof of currency or resolution. |
| Unit tests work offline | Run the focused tests and full suite with no `.env`, network disabled, and only test placeholders/fakes. | All tests pass without GitHub, Tavily, or LLM credentials/network requests. |

## 9. Risks, assumptions and decision requests

### Risks and mitigations

- **Provider/API schema drift or GraphQL permissions:** isolate mappings in two small adapters, use fixtures for known shapes, and return explicit safe error/partial states. GraphQL access is limited to Discussions, not a fallback for all GitHub data.
- **Rate limits and unbounded collection retrieval:** bounded retries and page caps make limits visible rather than silently looping or hiding incomplete coverage.
- **Snippet/content overclaiming:** represent search leads and extracted content as different types; defer evidence verification/classification to M4/M5 and M2 contracts.
- **Resolution overclaiming:** preserve `state`, closure and update metadata as facts only; Analysis must inspect fixes/counterevidence before assigning problem status.
- **Secret/content leakage:** use only M1 settings, redacted fixtures, injected clients, and minimal safe logs. Never log credentials or entire retrieved pages by default.
- **Scope creep:** keep endpoints and normalized records constrained to the approved sources; no browser or community-specific API fallbacks.

### Assumptions and delegated choices

- A synchronous, injected `httpx` client is the simplest compatible boundary for later CrewAI tool callables and deterministic mocked tests. An async boundary is acceptable only if it does not force Flow/agent work into M3.
- Direct HTTP calls are recommended despite the Tavily SDK dependency, because the project needs consistent result/error semantics and transport mocks. The implementation may use the official SDK only if it preserves the same injected/offline-testable boundary and does not hide partial/error metadata.
- Exact endpoint subset, Pydantic versus dataclass result models, result enum names, timeout/backoff values, page caps, fixed GraphQL query fields, test fixture filenames, and exception text remain implementation choices constrained by the plan.
- M3 result models are retrieval records, not substitutes for the M2 authoritative evidence registry. M4/M5 own the explicit, source-supported conversion into evidence items.

### Unresolved blockers / decision requests

None block plan approval. The following are implementation verification tasks rather than policy decisions: confirm the installed Tavily API request/response contract and GitHub Discussions GraphQL permission/query shape against current official documentation or an authorized smoke check. If either provider cannot support the approved narrow operation with the configured credentials, implementation must report the concrete limitation and preserve transparent failure behavior; it must not silently add another vendor, browser automation, or an extra agent.

### Cross-milestone impact

M4 will expose the M3 adapters to the Research Agent for Pass 1/Pass 2 and create `ResearchOutput`/registry entries only after source inspection. M5 will reuse them for alternatives, fixes, and counterevidence and may append new M2 evidence entries. M6/M7/M8 consume provenance-rich artifacts but must not assume retrieval success proves source truth, independence, ongoing status, or demand.

## 10. Approval boundary

**Status: approved for M3 implementation on 2026-10-15.** This plan covers M3 only. It does not authorize live research-service calls or work on another milestone.
