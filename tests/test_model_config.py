from __future__ import annotations

import pytest

from problem_discovery_agents.model_config import (
    ModelConfigurationError,
    build_shared_llm,
    crewai_model_name,
)
from problem_discovery_agents.settings import Settings


def _settings() -> Settings:
    return Settings(
        PDA_GITHUB_TOKEN="github-test-secret",
        PDA_TAVILY_API_KEY="tavily-test-secret",
        PDA_LLM_API_KEY="llm-test-secret",
    )


def test_builds_provider_qualified_model_with_reasoning_effort() -> None:
    received: dict[str, object] = {}

    def factory(**kwargs: object) -> object:
        received.update(kwargs)
        return object()

    settings = _settings()
    result = build_shared_llm(settings, llm_factory=factory)

    assert result is not None
    assert crewai_model_name(settings) == "openai/gpt-5.4-mini"
    assert received == {
        "model": "openai/gpt-5.4-mini",
        "api_key": "llm-test-secret",
        "reasoning_effort": "medium",
    }


def test_wrapper_rejection_is_safe_and_actionable() -> None:
    def rejected_factory(**kwargs: object) -> object:
        raise TypeError("unexpected parameter")

    with pytest.raises(ModelConfigurationError) as raised:
        build_shared_llm(_settings(), llm_factory=rejected_factory)

    assert "gpt-5.4-mini" in str(raised.value)
    assert "unexpected parameter" not in str(raised.value)
