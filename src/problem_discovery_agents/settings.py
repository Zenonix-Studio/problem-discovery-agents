"""External configuration for the research pilot.

No agent or tool should read environment variables directly.  This module is
the single boundary for credentials and the shared model configuration.
"""

from __future__ import annotations

from typing import Literal

from pydantic import AnyHttpUrl, Field, SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigurationError(RuntimeError):
    """Safe, actionable configuration validation failure."""


ReasoningEffort = Literal["none", "low", "medium", "high", "xhigh"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]


class Settings(BaseSettings):
    """Environment-backed settings with the approved shared-model defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    github_token: SecretStr = Field(validation_alias="PDA_GITHUB_TOKEN")
    tavily_api_key: SecretStr = Field(validation_alias="PDA_TAVILY_API_KEY")
    llm_api_key: SecretStr = Field(validation_alias="PDA_LLM_API_KEY")
    llm_provider: Literal["openai"] = Field(
        default="openai", validation_alias="PDA_LLM_PROVIDER"
    )
    llm_model: str = Field(
        default="gpt-5.4-mini", min_length=1, validation_alias="PDA_LLM_MODEL"
    )
    llm_reasoning_effort: ReasoningEffort = Field(
        default="medium", validation_alias="PDA_LLM_REASONING_EFFORT"
    )
    llm_base_url: AnyHttpUrl | None = Field(
        default=None, validation_alias="PDA_LLM_BASE_URL"
    )
    log_level: LogLevel = Field(default="INFO", validation_alias="PDA_LOG_LEVEL")
    record_provider_usage: bool = Field(
        default=True, validation_alias="PDA_RECORD_PROVIDER_USAGE"
    )

    @field_validator("github_token", "tavily_api_key", "llm_api_key", mode="before")
    @classmethod
    def _require_nonblank_secret(cls, value: object) -> object:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("must be set to a nonblank value")
        return value

    @field_validator("llm_model", mode="before")
    @classmethod
    def _require_nonblank_model(cls, value: object) -> object:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("must be set to a nonblank value")
        return value.strip()

    @field_validator("llm_base_url", mode="before")
    @classmethod
    def _treat_blank_base_url_as_unset(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value


def _format_validation_error(error: ValidationError) -> str:
    details = []
    for item in error.errors():
        location = ".".join(str(part) for part in item["loc"])
        details.append(f"{location}: {item['msg']}")
    joined = "; ".join(details)
    return (
        "Invalid configuration. Set the listed PDA_* variables in the environment "
        f"or a local .env file: {joined}"
    )


def load_settings() -> Settings:
    """Load settings, never including secret values in surfaced errors."""

    try:
        return Settings()
    except ValidationError as error:
        raise ConfigurationError(_format_validation_error(error)) from None


def validate_runtime_configuration() -> Settings:
    """Validate local configuration without contacting a provider or research tool."""

    return load_settings()
