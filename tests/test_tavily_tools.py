from __future__ import annotations

import httpx
import pytest

from problem_discovery_agents.research_tools import RetrievalState, TavilyAdapter
from problem_discovery_agents.settings import Settings


def _settings() -> Settings:
    return Settings(PDA_GITHUB_TOKEN="github-test-secret", PDA_TAVILY_API_KEY="tavily-test-secret", PDA_LLM_API_KEY="llm-test-secret")


def test_search_returns_discovery_leads_not_source_content() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer tavily-test-secret"
        return httpx.Response(200, request=request, json={"results": [{"url": "https://example.test/post", "title": "A post", "content": "search snippet", "published_date": "2026-01-01T00:00:00Z", "score": 0.8}]})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = TavilyAdapter(_settings(), client=client).search("developer friction")

    lead = result.leads[0]
    assert lead.snippet == "search snippet"
    assert "discovery lead" in lead.limitations[0]


def test_extract_preserves_partial_per_url_results() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, request=request, json={"results": [{"url": "https://example.test/ok", "raw_content": "original page content", "title": "Original", "published_date": "2026-01-01T00:00:00Z"}]})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        records = TavilyAdapter(_settings(), client=client).extract(["https://example.test/ok", "https://example.test/missing"])

    assert records[0].retrieval_state is RetrievalState.COMPLETE
    assert records[0].text == "original page content"
    assert records[1].retrieval_state is RetrievalState.PARTIAL
    assert records[1].requested_url == "https://example.test/missing"


@pytest.mark.parametrize("status,category,attempts", [(401, "authentication", 1), (403, "forbidden", 1), (429, "rate_limited", 3), (500, "upstream_failure", 3)])
def test_tavily_failure_matrix(status: int, category: str, attempts: int) -> None:
    called = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        called += 1
        return httpx.Response(status, request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = TavilyAdapter(_settings(), client=client).search("friction")

    assert result.error is not None
    assert result.error.category == category
    assert called == attempts
