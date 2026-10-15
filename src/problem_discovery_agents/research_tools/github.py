"""REST-first GitHub retrieval and a fixed-query Discussions adapter."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx

from ..settings import Settings
from .http import HttpExecutor
from .models import CollectionResult, Pagination, RetrievalError, RetrievalState, SourceRecord


GITHUB_API_URL = "https://api.github.com"
GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"


def _now() -> datetime:
    return datetime.now(UTC)


def _date(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _text(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


class GitHubRestAdapter:
    """The deliberately bounded GitHub REST surface used by later agents."""

    def __init__(self, settings: Settings, *, client: httpx.Client, max_retries: int = 2) -> None:
        self._executor = HttpExecutor(client, max_retries=max_retries)
        self._headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {settings.github_token.get_secret_value()}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "problem-discovery-agents",
        }

    def get_repository(self, owner: str, repository: str) -> SourceRecord:
        return self._one("repository", f"/repos/{owner}/{repository}")

    def get_issue_or_pull_request(self, owner: str, repository: str, number: int) -> SourceRecord:
        return self._one("issue_or_pull_request", f"/repos/{owner}/{repository}/issues/{number}")

    def list_issue_comments(self, owner: str, repository: str, number: int, *, max_pages: int = 1, max_items: int = 100) -> CollectionResult:
        return self._collection("issue_comment", f"/repos/{owner}/{repository}/issues/{number}/comments", max_pages=max_pages, max_items=max_items)

    def list_pull_request_reviews(self, owner: str, repository: str, number: int, *, max_pages: int = 1, max_items: int = 100) -> CollectionResult:
        return self._collection("pull_request_review", f"/repos/{owner}/{repository}/pulls/{number}/reviews", max_pages=max_pages, max_items=max_items)

    def list_pull_request_review_comments(self, owner: str, repository: str, number: int, *, max_pages: int = 1, max_items: int = 100) -> CollectionResult:
        return self._collection("pull_request_review_comment", f"/repos/{owner}/{repository}/pulls/{number}/comments", max_pages=max_pages, max_items=max_items)

    def _one(self, kind: str, path: str) -> SourceRecord:
        requested_url = f"{GITHUB_API_URL}{path}"
        outcome = self._executor.request("github", "GET", requested_url, headers=self._headers)
        retrieved_at = _now()
        if outcome.error:
            return SourceRecord(provider="github", request_kind=kind, requested_url=requested_url, retrieved_at=retrieved_at, retrieval_state=_state_for(outcome.error), limitations=[outcome.error.message], error=outcome.error)
        payload = _json_object(outcome.response)
        return _record(kind, requested_url, payload, retrieved_at)

    def _collection(self, kind: str, path: str, *, max_pages: int, max_items: int) -> CollectionResult:
        if max_pages < 1 or max_items < 1:
            raise ValueError("max_pages and max_items must be at least one")
        requested_url = f"{GITHUB_API_URL}{path}"
        url: str | None = requested_url
        items: list[SourceRecord] = []
        pages = 0
        next_available = False
        while url and pages < max_pages and len(items) < max_items:
            outcome = self._executor.request("github", "GET", url, headers=self._headers, params={"per_page": min(max_items, 100)})
            pages += 1
            retrieved_at = _now()
            if outcome.error:
                return CollectionResult(items=items, retrieved_at=retrieved_at, retrieval_state=RetrievalState.PARTIAL if items else _state_for(outcome.error), pagination=Pagination(pages_fetched=pages, next_page_available=False, truncated=False), limitations=[outcome.error.message], error=outcome.error)
            payload = _json_list(outcome.response)
            remaining = max_items - len(items)
            items.extend(_record(kind, requested_url, row, retrieved_at) for row in payload[:remaining])
            link = outcome.response.links.get("next", {}).get("url")
            next_available = bool(link)
            url = link
            if len(payload) > remaining:
                next_available = True
                break
        truncated = next_available and (pages >= max_pages or len(items) >= max_items)
        return CollectionResult(items=items, retrieved_at=_now(), retrieval_state=RetrievalState.PARTIAL if truncated else RetrievalState.COMPLETE, pagination=Pagination(pages_fetched=pages, next_page_available=next_available, truncated=truncated), limitations=["Collection was capped; additional GitHub results remain available."] if truncated else [])


class GitHubDiscussionsAdapter:
    """Fetch one Discussion through a non-configurable GraphQL operation."""

    _QUERY = """query Discussion($owner: String!, $repository: String!, $number: Int!, $after: String) {
      repository(owner: $owner, name: $repository) {
        discussion(number: $number) { url title body createdAt updatedAt comments(first: 100, after: $after) { nodes { url body createdAt updatedAt author { login } } pageInfo { hasNextPage endCursor } } }
      }
    }"""

    def __init__(self, settings: Settings, *, client: httpx.Client, max_retries: int = 2) -> None:
        self._executor = HttpExecutor(client, max_retries=max_retries)
        self._headers = {"Authorization": f"Bearer {settings.github_token.get_secret_value()}", "User-Agent": "problem-discovery-agents"}

    def get_discussion(self, owner: str, repository: str, number: int, *, max_pages: int = 1, max_items: int = 100) -> CollectionResult:
        if max_pages < 1 or max_items < 1:
            raise ValueError("max_pages and max_items must be at least one")
        requested_url = f"https://github.com/{owner}/{repository}/discussions/{number}"
        cursor: str | None = None
        items: list[SourceRecord] = []
        pages = 0
        graph_errors: list[str] = []
        discussion: dict[str, Any] | None = None
        next_available = False
        while pages < max_pages and len(items) < max_items:
            variables = {"owner": owner, "repository": repository, "number": number, "after": cursor}
            outcome = self._executor.request("github", "POST", GITHUB_GRAPHQL_URL, headers=self._headers, json={"query": self._QUERY, "variables": variables})
            pages += 1
            if outcome.error:
                return CollectionResult(items=items, primary_source=_record("discussion", requested_url, discussion, _now()) if discussion else None, retrieved_at=_now(), retrieval_state=RetrievalState.PARTIAL if items else _state_for(outcome.error), pagination=Pagination(pages_fetched=pages), limitations=[outcome.error.message], error=outcome.error)
            payload = _json_object(outcome.response)
            errors = payload.get("errors")
            if isinstance(errors, list):
                graph_errors.extend("GraphQL returned an error alongside partial data." for _ in errors)
            data = payload.get("data")
            candidate = data.get("repository", {}).get("discussion") if isinstance(data, dict) and isinstance(data.get("repository"), dict) else None
            if not isinstance(candidate, dict):
                error = RetrievalError(provider="github", category="graphql", message="GitHub GraphQL returned no Discussion data.", retryable=False, attempts=1)
                return CollectionResult(items=items, primary_source=_record("discussion", requested_url, discussion, _now()) if discussion else None, retrieved_at=_now(), retrieval_state=RetrievalState.PARTIAL if items else RetrievalState.FAILED, pagination=Pagination(pages_fetched=pages), limitations=graph_errors or [error.message], error=error)
            discussion = candidate
            comments = candidate.get("comments") if isinstance(candidate.get("comments"), dict) else {}
            nodes = comments.get("nodes") if isinstance(comments.get("nodes"), list) else []
            remaining = max_items - len(items)
            items.extend(_record("discussion_comment", requested_url, node, _now()) for node in nodes[:remaining] if isinstance(node, dict))
            page_info = comments.get("pageInfo") if isinstance(comments.get("pageInfo"), dict) else {}
            next_available = bool(page_info.get("hasNextPage"))
            cursor = page_info.get("endCursor") if isinstance(page_info.get("endCursor"), str) else None
            if not next_available or len(nodes) > remaining:
                if len(nodes) > remaining:
                    next_available = True
                break
        primary_source = _record("discussion", requested_url, discussion, _now()) if discussion else None
        truncated = next_available and (pages >= max_pages or len(items) >= max_items)
        limitations = graph_errors + (["Discussion comments were capped; additional comments remain available."] if truncated else [])
        state = RetrievalState.PARTIAL if limitations else RetrievalState.COMPLETE
        return CollectionResult(items=items, primary_source=primary_source, retrieved_at=_now(), retrieval_state=state, pagination=Pagination(pages_fetched=pages, next_page_available=next_available, truncated=truncated), limitations=limitations)


def _state_for(error: RetrievalError) -> RetrievalState:
    return RetrievalState.INACCESSIBLE if error.category in {"authentication", "forbidden", "not_found"} else RetrievalState.FAILED


def _json_object(response: httpx.Response | None) -> dict[str, Any]:
    if response is None:
        raise RuntimeError("response is required")
    try:
        payload = response.json()
    except ValueError as error:
        raise ValueError("Provider returned invalid JSON for a required object response.") from error
    if not isinstance(payload, dict):
        raise ValueError("Provider returned an unexpected object response shape.")
    return payload


def _json_list(response: httpx.Response | None) -> list[dict[str, Any]]:
    if response is None:
        raise RuntimeError("response is required")
    try:
        payload = response.json()
    except ValueError as error:
        raise ValueError("Provider returned invalid JSON for a required list response.") from error
    if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
        raise ValueError("Provider returned an unexpected list response shape.")
    return payload


def _record(kind: str, requested_url: str, payload: dict[str, Any], retrieved_at: datetime) -> SourceRecord:
    user = payload.get("user") or payload.get("author")
    author = user.get("login") if isinstance(user, dict) and isinstance(user.get("login"), str) else None
    canonical = _text(payload.get("html_url")) or _text(payload.get("url"))
    text = _text(payload.get("body"))
    limitations = [] if text is not None else ["Provider returned no text/body for this source."]
    return SourceRecord(provider="github", request_kind=kind, requested_url=requested_url, canonical_url=canonical, source_type=kind, title=_text(payload.get("title")), text=text, author=author, created_at=_date(payload.get("created_at") or payload.get("createdAt")), updated_at=_date(payload.get("updated_at") or payload.get("updatedAt")), closed_at=_date(payload.get("closed_at")), github_state=_text(payload.get("state")), retrieved_at=retrieved_at, retrieval_state=RetrievalState.PARTIAL if limitations else RetrievalState.COMPLETE, limitations=limitations, metadata={"is_pull_request": isinstance(payload.get("pull_request"), dict), "review_state": _text(payload.get("state"))})
