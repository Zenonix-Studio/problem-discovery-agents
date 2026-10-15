"""Small, provider-metadata-only run usage representation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class RunUsage:
    """Usage reported by a provider; absent values remain unknown, never estimated."""

    input_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_tokens: int | None = None
    estimated_model_cost_usd: float | None = None
    search_retrieval_cost_usd: float | None = None


def usage_from_metadata(metadata: object) -> RunUsage:
    """Read known provider fields without making absent values look measured."""

    def value(*names: str) -> int | float | None:
        for name in names:
            candidate = metadata.get(name) if isinstance(metadata, dict) else getattr(metadata, name, None)
            if isinstance(candidate, (int, float)) and not isinstance(candidate, bool):
                return candidate
        return None

    return RunUsage(
        input_tokens=_integer(value("input_tokens", "prompt_tokens")),
        output_tokens=_integer(value("output_tokens", "completion_tokens")),
        reasoning_tokens=_integer(value("reasoning_tokens")),
        estimated_model_cost_usd=_number(value("estimated_model_cost_usd", "cost_usd")),
        search_retrieval_cost_usd=_number(value("search_retrieval_cost_usd")),
    )


def summarize_usages(metadata_records: list[object]) -> dict[str, Any]:
    """Keep per-call availability and total a field only when it is complete."""

    usages = [usage_from_metadata(item) for item in metadata_records]
    fields = tuple(asdict(RunUsage()).keys())
    totals: dict[str, int | float | None] = {}
    for field in fields:
        values = [getattr(usage, field) for usage in usages]
        totals[field] = sum(values) if values and all(value is not None for value in values) else None
    return {"calls": [asdict(usage) for usage in usages], "totals": totals, "complete": {field: totals[field] is not None for field in fields}}


def _integer(value: int | float | None) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _number(value: int | float | None) -> float | None:
    return float(value) if value is not None else None
