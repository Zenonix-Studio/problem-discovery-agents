from __future__ import annotations

import pytest

from problem_discovery_agents.observability import RunUsage
from problem_discovery_agents.settings import ConfigurationError, load_settings


REQUIRED_ENV = {
    "PDA_GITHUB_TOKEN": "github-test-secret",
    "PDA_TAVILY_API_KEY": "tavily-test-secret",
    "PDA_LLM_API_KEY": "llm-test-secret",
}


def _set_required_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in REQUIRED_ENV.items():
        monkeypatch.setenv(name, value)


def test_default_shared_model_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_env(monkeypatch)

    settings = load_settings()

    assert settings.llm_provider == "openai"
    assert settings.llm_model == "gpt-5.4-mini"
    assert settings.llm_reasoning_effort == "medium"


def test_environment_overrides_model_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.setenv("PDA_LLM_MODEL", "another-model")
    monkeypatch.setenv("PDA_LLM_REASONING_EFFORT", "high")
    monkeypatch.setenv("PDA_LLM_BASE_URL", "https://example.test/v1")

    settings = load_settings()

    assert settings.llm_model == "another-model"
    assert settings.llm_reasoning_effort == "high"
    assert str(settings.llm_base_url) == "https://example.test/v1"


def test_missing_and_blank_secrets_are_aggregated_and_redacted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in REQUIRED_ENV:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("PDA_LLM_API_KEY", "   ")

    with pytest.raises(ConfigurationError) as raised:
        load_settings()

    message = str(raised.value)
    assert "PDA_GITHUB_TOKEN" in message
    assert "PDA_TAVILY_API_KEY" in message
    assert "PDA_LLM_API_KEY" in message
    assert "llm-test-secret" not in message


def test_invalid_provider_and_reasoning_effort_are_actionable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.setenv("PDA_LLM_PROVIDER", "other")
    monkeypatch.setenv("PDA_LLM_REASONING_EFFORT", "max")

    with pytest.raises(ConfigurationError) as raised:
        load_settings()

    message = str(raised.value)
    assert "PDA_LLM_PROVIDER" in message
    assert "PDA_LLM_REASONING_EFFORT" in message
    assert "other" not in message


def test_usage_does_not_estimate_unknown_values() -> None:
    usage = RunUsage()

    assert usage.input_tokens is None
    assert usage.estimated_model_cost_usd is None
    assert usage.search_retrieval_cost_usd is None
