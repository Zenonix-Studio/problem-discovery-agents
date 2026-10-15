from __future__ import annotations

import json

import httpx
import pytest

from problem_discovery_agents.research_tools import GitHubDiscussionsAdapter, GitHubRestAdapter, RetrievalState
from problem_discovery_agents.settings import Settings


def _settings() -> Settings:
    return Settings(PDA_GITHUB_TOKEN="github-test-secret", PDA_TAVILY_API_KEY="tavily-test-secret", PDA_LLM_API_KEY="llm-test-secret")


def test_rest_normalizes_pull_request_and_review_records() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.path)
        assert request.headers["Authorization"] == "Bearer github-test-secret"
        if request.url.path.endswith("/issues/4"):
            return httpx.Response(200, request=request, json={"html_url": "https://github.com/o/r/pull/4", "title": "PR", "body": "reported friction", "state": "closed", "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-02T00:00:00Z", "closed_at": "2026-01-03T00:00:00Z", "user": {"login": "dev"}, "pull_request": {}})
        if request.url.path.endswith("/reviews"):
            return httpx.Response(200, request=request, json=[{"html_url": "https://github.com/o/r/pull/4#review", "body": "review body", "state": "APPROVED", "user": {"login": "reviewer"}}])
        return httpx.Response(200, request=request, json=[{"html_url": "https://github.com/o/r/pull/4#comment", "body": "inline", "user": {"login": "reviewer"}}])

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        adapter = GitHubRestAdapter(_settings(), client=client)
        issue = adapter.get_issue_or_pull_request("o", "r", 4)
        reviews = adapter.list_pull_request_reviews("o", "r", 4)
        comments = adapter.list_pull_request_review_comments("o", "r", 4)

    assert issue.metadata["is_pull_request"] is True
    assert issue.github_state == "closed"  # metadata only, never a resolution conclusion
    assert issue.created_at is not None
    assert issue.closed_at is not None
    assert reviews.items[0].request_kind == "pull_request_review"
    assert comments.items[0].request_kind == "pull_request_review_comment"
    assert seen == ["/repos/o/r/issues/4", "/repos/o/r/pulls/4/reviews", "/repos/o/r/pulls/4/comments"]


def test_rest_link_cap_is_visible() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, request=request, headers={"Link": '<https://api.github.com/next>; rel="next"'}, json=[{"html_url": "https://github.com/o/r/issues/1#issuecomment-1", "body": "comment"}])

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = GitHubRestAdapter(_settings(), client=client).list_issue_comments("o", "r", 1, max_pages=1)

    assert calls == 1
    assert result.retrieval_state is RetrievalState.PARTIAL
    assert result.pagination.truncated is True
    assert result.pagination.next_page_available is True


def test_rest_missing_body_and_dates_remain_explicitly_partial() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, request=request, json={"html_url": "https://github.com/o/r/issues/9", "title": "No body"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = GitHubRestAdapter(_settings(), client=client).get_issue_or_pull_request("o", "r", 9)

    assert result.text is None
    assert result.created_at is None
    assert result.retrieval_state is RetrievalState.PARTIAL
    assert result.limitations == ["Provider returned no text/body for this source."]


@pytest.mark.parametrize("status,category,attempts", [(401, "authentication", 1), (403, "forbidden", 1), (404, "not_found", 1), (429, "rate_limited", 3), (503, "upstream_failure", 3)])
def test_rest_failure_matrix(status: int, category: str, attempts: int) -> None:
    called = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        called += 1
        return httpx.Response(status, request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = GitHubRestAdapter(_settings(), client=client).get_repository("o", "r")

    assert result.error is not None
    assert result.error.category == category
    assert result.error.attempts == attempts
    assert called == attempts


def test_discussion_partial_data_and_comment_page_cap() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        body = json.loads(request.content)
        assert "query Discussion" in body["query"]
        assert body["variables"]["after"] is None
        return httpx.Response(200, request=request, json={"data": {"repository": {"discussion": {"url": "https://github.com/o/r/discussions/2", "title": "Discussion", "body": "root", "comments": {"nodes": [{"url": "https://github.com/o/r/discussions/2#discussioncomment-1", "body": "first", "author": {"login": "dev"}}], "pageInfo": {"hasNextPage": True, "endCursor": "cursor-1"}}}}}, "errors": [{"message": "partial"}]})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = GitHubDiscussionsAdapter(_settings(), client=client).get_discussion("o", "r", 2, max_pages=1)

    assert calls == 1
    assert result.items[0].request_kind == "discussion_comment"
    assert result.primary_source is not None
    assert result.primary_source.request_kind == "discussion"
    assert result.primary_source.text == "root"
    assert result.pagination.truncated is True
    assert result.retrieval_state is RetrievalState.PARTIAL
    assert result.limitations


def test_discussion_follows_comment_cursor_within_page_cap() -> None:
    cursors: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        after = body["variables"]["after"]
        cursors.append(after)
        node = {"url": f"https://github.com/o/r/discussions/2#comment-{len(cursors)}", "body": f"comment-{len(cursors)}"}
        return httpx.Response(200, request=request, json={"data": {"repository": {"discussion": {"url": "https://github.com/o/r/discussions/2", "title": "Discussion", "body": "root", "comments": {"nodes": [node], "pageInfo": {"hasNextPage": len(cursors) == 1, "endCursor": "cursor-1"}}}}}})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = GitHubDiscussionsAdapter(_settings(), client=client).get_discussion("o", "r", 2, max_pages=2)

    assert cursors == [None, "cursor-1"]
    assert [item.text for item in result.items] == ["comment-1", "comment-2"]
    assert result.pagination.pages_fetched == 2
    assert result.pagination.truncated is False
