"""Tavily Search leads and Extracted original-page retrieval."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx

from ..settings import Settings
from .http import HttpExecutor
from .models import RetrievalState, SearchLead, SearchResult, SourceRecord


TAVILY_API_URL = "https://api.tavily.com"


def _now() -> datetime:
    return datetime.now(UTC)


def _date(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


class TavilyAdapter:
    def __init__(self, settings: Settings, *, client: httpx.Client, max_retries: int = 2) -> None:
        self._executor = HttpExecutor(client, max_retries=max_retries)
        self._headers = {"Authorization": f"Bearer {settings.tavily_api_key.get_secret_value()}", "Content-Type": "application/json", "User-Agent": "problem-discovery-agents"}

    def search(self, query: str, *, max_results: int = 5) -> SearchResult:
        if not query.strip() or max_results < 1:
            raise ValueError("query must be nonblank and max_results must be at least one")
        outcome = self._executor.request("tavily", "POST", f"{TAVILY_API_URL}/search", headers=self._headers, json={"query": query, "max_results": max_results})
        retrieved_at = _now()
        if outcome.error:
            return SearchResult(query=query, retrieved_at=retrieved_at, retrieval_state=RetrievalState.INACCESSIBLE if outcome.error.category in {"authentication", "forbidden"} else RetrievalState.FAILED, limitations=[outcome.error.message], error=outcome.error)
        payload = _object(outcome.response)
        results = payload.get("results") if isinstance(payload.get("results"), list) else []
        leads = [SearchLead(original_url=row["url"], title=row.get("title") if isinstance(row.get("title"), str) else None, snippet=row.get("content") if isinstance(row.get("content"), str) else None, published_at=_date(row.get("published_date")), score=row.get("score") if isinstance(row.get("score"), (int, float)) else None, retrieved_at=retrieved_at) for row in results if isinstance(row, dict) and isinstance(row.get("url"), str)]
        return SearchResult(query=query, leads=leads, retrieved_at=retrieved_at, retrieval_state=RetrievalState.PARTIAL if len(leads) != len(results) else RetrievalState.COMPLETE, limitations=["Some provider search records lacked an original URL."] if len(leads) != len(results) else [])

    def extract(self, urls: list[str]) -> list[SourceRecord]:
        if not urls or any(not url.strip() for url in urls):
            raise ValueError("urls must contain one or more nonblank URLs")
        outcome = self._executor.request("tavily", "POST", f"{TAVILY_API_URL}/extract", headers=self._headers, json={"urls": urls})
        retrieved_at = _now()
        if outcome.error:
            state = RetrievalState.INACCESSIBLE if outcome.error.category in {"authentication", "forbidden", "not_found"} else RetrievalState.FAILED
            return [SourceRecord(provider="tavily", request_kind="extract", requested_url=url, retrieved_at=retrieved_at, retrieval_state=state, limitations=[outcome.error.message], error=outcome.error) for url in urls]
        payload = _object(outcome.response)
        rows = payload.get("results") if isinstance(payload.get("results"), list) else []
        by_url = {row.get("url"): row for row in rows if isinstance(row, dict) and isinstance(row.get("url"), str)}
        records: list[SourceRecord] = []
        for url in urls:
            row = by_url.get(url)
            if row is None:
                records.append(SourceRecord(provider="tavily", request_kind="extract", requested_url=url, retrieved_at=retrieved_at, retrieval_state=RetrievalState.PARTIAL, limitations=["Provider returned no extraction result for this requested URL."]))
                continue
            text = row.get("raw_content") if isinstance(row.get("raw_content"), str) else None
            limitations = [] if text else ["Provider returned no extracted original-page text."]
            records.append(SourceRecord(provider="tavily", request_kind="extract", requested_url=url, canonical_url=row.get("url"), source_type="web_page", title=row.get("title") if isinstance(row.get("title"), str) else None, text=text, created_at=_date(row.get("published_date")), retrieved_at=retrieved_at, retrieval_state=RetrievalState.COMPLETE if text else RetrievalState.PARTIAL, limitations=limitations))
        return records


def _object(response: httpx.Response | None) -> dict[str, Any]:
    if response is None:
        raise RuntimeError("response is required")
    try:
        value = response.json()
    except ValueError as error:
        raise ValueError("Tavily returned invalid JSON.") from error
    if not isinstance(value, dict):
        raise ValueError("Tavily returned an unexpected response shape.")
    return value
