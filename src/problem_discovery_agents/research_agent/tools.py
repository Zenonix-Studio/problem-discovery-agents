"""Injectable M3-shaped tool boundary used by the M4 Research Agent."""

from __future__ import annotations

import re
from typing import Protocol

from ..research_tools.github import GitHubDiscussionsAdapter, GitHubRestAdapter
from ..research_tools.models import SearchResult, SourceRecord
from ..research_tools.tavily import TavilyAdapter


class ResearchTools(Protocol):
    def search(self, query: str) -> SearchResult: ...

    def extract(self, urls: list[str]) -> list[SourceRecord]: ...


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
                records.append(record.model_copy(update={"requested_url": url}))
            elif discussion and self._github_discussions is not None:
                result = self._github_discussions.get_discussion(
                    discussion["owner"], discussion["repository"], int(discussion["number"])
                )
                if result.primary_source is not None:
                    records.append(result.primary_source)
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
