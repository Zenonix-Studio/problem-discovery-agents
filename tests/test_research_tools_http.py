from __future__ import annotations

import httpx

from problem_discovery_agents.research_tools.http import HttpExecutor


def test_retries_transient_status_without_sleeping() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503 if attempts < 3 else 200, request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = HttpExecutor(client, max_retries=2).request("github", "GET", "https://example.test", headers={})

    assert result.response is not None
    assert result.error is None
    assert attempts == 3


def test_authentication_error_is_not_retried_or_secret_bearing() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(401, request=request, text="secret-token")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = HttpExecutor(client, max_retries=2).request("github", "GET", "https://example.test", headers={"Authorization": "Bearer secret-token"})

    assert result.response is None
    assert result.error is not None
    assert result.error.category == "authentication"
    assert result.error.attempts == 1
    assert "secret-token" not in result.error.message
    assert attempts == 1


def test_rate_limit_respects_bounded_retry_after_with_injected_sleep() -> None:
    attempts = 0
    delays: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(429, request=request, headers={"Retry-After": "30"})
        return httpx.Response(200, request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = HttpExecutor(
            client,
            max_retries=1,
            max_retry_after_seconds=2,
            sleep=delays.append,
        ).request("github", "GET", "https://example.test", headers={})

    assert result.response is not None
    assert attempts == 2
    assert delays == [2]
