"""Small, provider-metadata-only run usage representation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RunUsage:
    """Usage reported by a provider; absent values remain unknown, never estimated."""

    input_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_tokens: int | None = None
    estimated_model_cost_usd: float | None = None
    search_retrieval_cost_usd: float | None = None
