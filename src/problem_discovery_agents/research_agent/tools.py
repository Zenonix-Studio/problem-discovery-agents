"""Injectable M3-shaped tool boundary used by the M4 Research Agent."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Protocol

from ..research_tools.github import GitHubDiscussionsAdapter, GitHubRestAdapter
from ..research_tools.models import CollectionResult, RetrievalState, SearchResult, SourceRecord
from ..research_tools.tavily import TavilyAdapter


class ResearchTools(Protocol):
    def search(self, query: str) -> SearchResult: ...

    def extract(self, urls: list[str]) -> list[SourceRecord]: ...


# Provisional starting values for the comment text handed on with a GitHub source.
MAX_COMMENTS = 100
COMMENT_TEXT_CAP = 1500
COMMENTS_TOTAL_CAP = 12000

_GITHUB_OBJECT_URL = re.compile(
    r"^https://github\.com/(?P<owner>[^/]+)/(?P<repository>[^/]+)/(?:issues|pull)/(?P<number>\d+)/?$"
)
_GITHUB_DISCUSSION_URL = re.compile(
    r"^https://github\.com/(?P<owner>[^/]+)/(?P<repository>[^/]+)/discussions/(?P<number>\d+)/?$"
)


class M3ResearchTools:
    """Minimal bridge to the approved M3 adapters, with no credential reads.

    GitHub object URLs use the authenticated REST/GraphQL adapters when they
    are supplied. Other URLs, including discovery leads, use Tavily Extract.
    """

    def __init__(
        self,
        *,
        tavily: TavilyAdapter,
        github_rest: GitHubRestAdapter | None = None,
        github_discussions: GitHubDiscussionsAdapter | None = None,
    ) -> None:
        self._tavily = tavily
        self._github_rest = github_rest
        self._github_discussions = github_discussions

    def search(self, query: str) -> SearchResult:
        return self._tavily.search(query)

    def extract(self, urls: list[str]) -> list[SourceRecord]:
        records: list[SourceRecord] = []
        web_urls: list[str] = []
        for url in urls:
            issue = _GITHUB_OBJECT_URL.match(url)
            discussion = _GITHUB_DISCUSSION_URL.match(url)
            if issue and self._github_rest is not None:
                record = self._github_rest.get_issue_or_pull_request(
                    issue["owner"], issue["repository"], int(issue["number"])
                )
                record = record.model_copy(update={"requested_url": url})
                records.append(self._with_comments(record, lambda: self._github_rest.list_issue_comments(
                    issue["owner"], issue["repository"], int(issue["number"]), max_pages=1, max_items=MAX_COMMENTS
                )))
            elif discussion and self._github_discussions is not None:
                result = self._github_discussions.get_discussion(
                    discussion["owner"], discussion["repository"], int(discussion["number"])
                )
                if result.primary_source is not None:
                    records.append(self._with_comments(result.primary_source, lambda: result))
                else:
                    records.append(
                        SourceRecord(
                            provider="github",
                            request_kind="discussion",
                            requested_url=url,
                            retrieved_at=result.retrieved_at,
                            retrieval_state=result.retrieval_state,
                            limitations=result.limitations or ["GitHub returned no discussion source."],
                            error=result.error,
                        )
                    )
            else:
                web_urls.append(url)
        if web_urls:
            records.extend(self._tavily.extract(web_urls))
        return records


    @staticmethod
    def _with_comments(record: SourceRecord, fetch: Callable[[], CollectionResult]) -> SourceRecord:
        """Attach comment text beside the body; a comment failure never fails extraction."""

        if not (record.text and record.text.strip()):
            return record
        try:
            comments = fetch()
        except ValueError as error:
            return _noted(record, None, [f"Comments could not be retrieved: {error}"])
        if comments.error is not None and not comments.items:
            return _noted(record, None, [f"Comments could not be retrieved: {comments.error.message}"])
        text, notes = _format_comments(comments)
        return _noted(record, text, notes)


def _noted(record: SourceRecord, comments_text: str | None, notes: list[str]) -> SourceRecord:
    limitations = [*record.limitations, *(note for note in notes if note not in record.limitations)]
    return record.model_copy(update={"comments_text": comments_text, "limitations": limitations})


def _format_comments(comments: CollectionResult) -> tuple[str | None, list[str]]:
    """Chronological blocks with attribution, bounded per comment and in total."""

    items = [item for item in comments.items if item.text and item.text.strip()]
    blocks: list[str] = []
    used = 0
    cut = 0
    for item in items:
        text = item.text.strip()
        cut += len(text) > COMMENT_TEXT_CAP
        when = item.created_at.date().isoformat() if item.created_at else "undated"
        block = f"[{item.author or 'unknown'}, {when}, {item.canonical_url or item.requested_url}]\n{text[:COMMENT_TEXT_CAP]}"
        if used + len(block) + 2 > COMMENTS_TOTAL_CAP:
            break
        blocks.append(block)
        used += len(block) + 2
    notes = list(comments.limitations)
    if cut:
        notes.append(f"Some comments were cut to {COMMENT_TEXT_CAP} characters.")
    if len(items) > len(blocks):
        notes.append(
            f"{len(items) - len(blocks)} comment(s) were omitted after the {COMMENTS_TOTAL_CAP}-character comment budget."
        )
    return ("\n\n".join(blocks) or None), notes
