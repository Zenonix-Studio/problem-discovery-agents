# Fix Plan — Fetch GitHub Comments in `extract` (targeted M8 correction, direction amendment §6.7)

**Status: proposed, not yet approved.** Small, single-boundary correction approved in principle by `DIRECTION_AMENDMENT.md` §6.7. No production code, test or live call until this plan is approved. The optional live checks in §6 are read-only GitHub calls and a paid Analysis-only run; each needs separate explicit authorization.

## 1. Problem and evidence

Thread resolutions and workarounds live in comments, but the pipeline never reads them. Verified by reading the code:

- `research_agent/tools.py` `M3ResearchTools.extract` routes GitHub issue/PR URLs to `get_issue_or_pull_request` and keeps only the issue body (`record.text`). `GitHubRestAdapter.list_issue_comments` exists (M3) but nothing calls it (the only callers of the GitHub adapters in `src/` are the two lines in `tools.py`).
- Discussions: `GitHubDiscussionsAdapter.get_discussion` already fetches up to 100 comments, but `extract` keeps only `result.primary_source`. The comments in `result.items` are discarded.
- Evidence from M8 run `…b2adce4a`: EV-006's extract was the issue body only (1,601 chars) while the three workarounds sit in the thread; EV-002/005/008 had the cause or answer on the page, not in the body excerpt.
- Consumers: Research builds the stored excerpt and Pass 2 `InspectedSignal.source_excerpt` from `record.text` (first 25 words). Analysis passes `record.text` (cap 4,000 chars, `CONTEXT_TEXT_CAP`) to `finalize`. So today no model ever sees a comment.

**Root cause:** the extract boundary drops comment content that the adapters can already provide. Not a model-capability claim.

## 2. Scope

### Included
- New optional field `SourceRecord.comments_text: str | None = None` (`research_tools/models.py`). The issue body stays in `text`, unchanged. Reason for a separate field instead of appending to `text`: Research's excerpt, "has text" check and verification semantics all read `record.text` and must not change; and Analysis's body cap would cut comments off at the end of a long thread.
- `M3ResearchTools.extract` fetches comments for GitHub URLs and fills `comments_text`:
  - Issues and pull requests: `list_issue_comments` (conversation comments; covers PRs because GitHub serves them from the issues endpoint), first page, up to 100 comments.
  - Discussions: `result.items` already returned by `get_discussion`.
- One shared formatter: each comment becomes a block with its attribution (author login, created date, comment URL from `canonical_url`) followed by its text, in chronological order. Per-comment text cap and a total comments budget (provisional constants in `tools.py`: 1,500 chars per comment, 12,000 chars total). When comments are omitted or cut, `record.limitations` states how many were omitted or truncated.
- Failure handling: a failed comment fetch never fails extraction. The body record stays as it is and a limitation records that comments could not be retrieved.
- Analysis (`analysis_agent/service.py`): context and new-source records handed to `finalize` carry `comments_text` under its own cap (`CONTEXT_COMMENTS_CAP`, provisional 12,000 chars), separate from `CONTEXT_TEXT_CAP`.
- `FINALIZE_INSTRUCTIONS`: one sentence: when a resolution or workaround comes from a comment, name the comment URL from `comments_text` in the observation text; do not claim anything the supplied comments do not show.
- Tests (§5), written first.

### Non-goals
- No change to the evidence registry contract, the excerpt policy (25 words / 280 chars, from the body), statuses, Stage 1/2, Flow order, agent count.
- No pull request review comments or review threads (`list_pull_request_reviews` / `…_review_comments`), no Discussion comment replies (the existing GraphQL query does not request `replies`), no pagination beyond one page, no bot filtering.
- Research Pass 2 is not changed: its model only sees the 25-word excerpt, so comment content reaches the **Analysis** stage only. Giving Research comment content would be a separate decision.
- Tavily/web pages are untouched (they return whatever the page text contains).

## 3. Proposed approach

1. `models.py`: add `comments_text` (optional, default `None`; `SourceRecord` stays frozen, `extra="forbid"`).
2. `tools.py`: after fetching the primary record, call the comment source, build `comments_text` via a small `_format_comments(items) -> tuple[str | None, list[str]]`, and attach it with `record.model_copy(update=...)`, appending any new limitations. `requested_url` stays as today (`model_copy(update={"requested_url": url})` is already used there).
3. `analysis_agent/service.py`: `_capped` and the context-record dict include `comments_text[:CONTEXT_COMMENTS_CAP]`.
4. `prompts.py`: the single finalize sentence.
5. Constants documented as starting values.

## 4. File change map

| Path | Change |
| --- | --- |
| `src/problem_discovery_agents/research_tools/models.py` | Add `SourceRecord.comments_text`. |
| `src/problem_discovery_agents/research_agent/tools.py` | Fetch and format comments for issues/PRs and Discussions; limitations; failure tolerance. |
| `src/problem_discovery_agents/analysis_agent/service.py` | Pass `comments_text` under its own cap to `finalize`. |
| `src/problem_discovery_agents/analysis_agent/prompts.py` | One sentence in `FINALIZE_INSTRUCTIONS`. |
| `tests/test_research_agent.py` | Extend the existing fake GitHub REST adapter with `list_issue_comments`; add extract tests. |
| `tests/test_analysis_agent.py` | Add the cap/prompt tests. |

## 5. Tests (offline, fakes only; shown failing on current code first)

- **Issue comments reach the record:** extracting an issue URL returns `text` = body (unchanged) and `comments_text` containing each comment's author, date, comment URL and text in order. Fails today (field missing).
- **Pull request URL** uses the same issue-comments call.
- **Discussion:** comments from `get_discussion(...).items` appear in `comments_text` (today they are discarded).
- **Failure tolerance:** a failed comment fetch leaves the body record intact, `comments_text` is `None`, and a limitation says comments could not be retrieved; no exception.
- **Budget:** a comment over the per-comment cap is truncated, and a thread over the total budget stops early with a limitation naming how many comments were omitted.
- **No comments:** zero comments gives `comments_text = None` and no extra limitation.
- **Research unchanged:** `source_excerpt`, evidence IDs and the "has text" decision are identical with and without comments (comments do not leak into excerpts).
- **Analysis:** `finalize` receives `comments_text` truncated to `CONTEXT_COMMENTS_CAP`, independent of `CONTEXT_TEXT_CAP`; the prompt contains the comment-URL sentence.
- Full suite (`uv run pytest`) stays green (141 today).

## 6. Verification

1. Offline: new tests failing first, then the full suite; report results as run.
2. Optional read-only check (needs authorization; GitHub API only, no model cost): extract the EV-006 issue URL from run `…b2adce4a` and confirm the three workaround comments appear in `comments_text` with their URLs.
3. Optional Analysis-only probe (needs authorization; paid model + search calls) on the saved Research output of `…b2adce4a`: for P-005 (EV-006) check that alternatives now cite the workarounds and the observation names comment URLs; compare with the current record.

## 7. Risks and open decisions

- **Cost:** `comments_text` adds up to ~12,000 chars (~3,000 tokens) per source in `finalize`; with 6–20 sources this can add tens of thousands of tokens per run. Real cost is not measured yet; the caps are starting values.
- **Truncation order:** comments stay chronological and the budget cuts from the end, so in a very long thread the final resolution comment can be omitted. The limitation line says so. Upgrade path if it happens: keep the first and last comments, drop the middle.
- **Traceability:** the registry keeps one URL per source (the issue/discussion). A comment's URL appears only in the model's observation text, not as a registry field. A deterministic check of that text is out of scope; the reviewer verifies it in the human review. Changing the registry to store comment-level URLs would be a separate contract decision.
- **Research does not see comments** (see non-goals); only Analysis and the later report do.
- **GitHub rate limits:** one extra call per issue/PR (authenticated limit is far above a run's use).
- **Decisions requested:** (1) approve the separate `comments_text` field (recommended) or append to `text` instead. (2) Approve the provisional caps (1,500 / 12,000 chars for the fetch, 12,000 for Analysis context). (3) Accept comment attribution in text only, not in the registry.

## 8. Approval boundary

Wait for explicit approval before any code, test or live call.
