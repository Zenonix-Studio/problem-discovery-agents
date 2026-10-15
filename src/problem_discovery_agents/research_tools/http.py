"""Small injected HTTP boundary with bounded, credential-safe failures."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from time import sleep as default_sleep
from typing import Any, Callable

import httpx

from .models import RetrievalError


@dataclass(frozen=True)
class HttpOutcome:
    response: httpx.Response | None
    error: RetrievalError | None


class HttpExecutor:
    """Execute provider requests without exposing secrets in result errors."""

    def __init__(
        self,
        client: httpx.Client,
        *,
        max_retries: int = 2,
        max_retry_after_seconds: float = 5,
        sleep: Callable[[float], None] = default_sleep,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        if max_retries < 0:
            raise ValueError("max_retries must be zero or greater")
        if max_retry_after_seconds < 0:
            raise ValueError("max_retry_after_seconds must be zero or greater")
        self._client = client
        self._max_retries = max_retries
        self._max_retry_after_seconds = max_retry_after_seconds
        self._sleep = sleep
        self._now = now

    def request(
        self,
        provider: str,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any] | None = None,
        params: dict[str, str | int] | None = None,
    ) -> HttpOutcome:
        attempts = 0
        while True:
            attempts += 1
            try:
                response = self._client.request(
                    method, url, headers=headers, json=json, params=params
                )
            except httpx.TransportError:
                if attempts <= self._max_retries:
                    continue
                return HttpOutcome(None, self._error(provider, "transport", None, attempts))

            if response.status_code < 400:
                return HttpOutcome(response, None)
            retryable = response.status_code == 429 or response.status_code >= 500
            if retryable and attempts <= self._max_retries:
                retry_after = self._retry_after_seconds(response)
                if retry_after:
                    self._sleep(retry_after)
                continue
            return HttpOutcome(
                None,
                self._error(
                    provider,
                    self._category(response.status_code),
                    response.status_code,
                    attempts,
                    self._retry_after_seconds(response),
                ),
            )

    def _retry_after_seconds(self, response: httpx.Response) -> float | None:
        """Return a bounded numeric Retry-After delay without blocking tests."""

        value = response.headers.get("Retry-After")
        if value is None:
            return None
        try:
            seconds = float(value)
        except ValueError:
            try:
                retry_at = parsedate_to_datetime(value)
            except (TypeError, ValueError):
                return None
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=UTC)
            seconds = (retry_at - self._now()).total_seconds()
        if seconds < 0:
            return None
        return min(seconds, self._max_retry_after_seconds)

    @staticmethod
    def _category(status: int) -> str:
        if status == 401:
            return "authentication"
        if status == 403:
            return "forbidden"
        if status == 404:
            return "not_found"
        if status == 429:
            return "rate_limited"
        if status >= 500:
            return "upstream_failure"
        return "request_failed"

    @staticmethod
    def _error(
        provider: str,
        category: str,
        status: int | None,
        attempts: int,
        retry_after_seconds: float | None = None,
    ) -> RetrievalError:
        messages = {
            "authentication": "Provider authentication was rejected.",
            "forbidden": "Provider access is forbidden or limited.",
            "not_found": "The requested source was not found.",
            "rate_limited": "Provider rate limit persisted after bounded retries.",
            "upstream_failure": "Provider server failure persisted after bounded retries.",
            "transport": "Transport failure persisted after bounded retries.",
            "request_failed": "Provider request failed.",
        }
        return RetrievalError(
            provider=provider,
            category=category,
            message=messages[category],
            http_status=status,
            retryable=category in {"rate_limited", "upstream_failure", "transport"},
            attempts=attempts,
            retry_after_seconds=retry_after_seconds,
        )
