"""Non-network construction of the shared CrewAI LLM configuration."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .settings import Settings


class ModelConfigurationError(RuntimeError):
    """The locally installed provider wrapper rejects configured parameters."""


LLMFactory = Callable[..., Any]


def crewai_model_name(settings: Settings) -> str:
    """Map the supported provider/model pair to CrewAI's provider-qualified name."""

    return f"{settings.llm_provider}/{settings.llm_model}"


def _default_llm_factory(**kwargs: Any) -> Any:
    """Import CrewAI lazily so settings-only operations remain lightweight."""

    from crewai import LLM

    return LLM(**kwargs)


def build_shared_llm(settings: Settings, *, llm_factory: LLMFactory | None = None) -> Any:
    """Construct (but never invoke) the configured LLM wrapper.

    This checks the installed wrapper's constructor contract only. Remote model
    availability and credential validity need an explicitly authorized live check.
    """

    factory = llm_factory or _default_llm_factory
    kwargs: dict[str, Any] = {
        "model": crewai_model_name(settings),
        "api_key": settings.llm_api_key.get_secret_value(),
        "reasoning_effort": settings.llm_reasoning_effort,
    }
    if settings.llm_base_url is not None:
        kwargs["base_url"] = str(settings.llm_base_url)

    try:
        return factory(**kwargs)
    except Exception as error:
        raise ModelConfigurationError(
            "The installed CrewAI/provider wrapper rejected the configured model "
            f"({kwargs['model']}) or reasoning effort ({settings.llm_reasoning_effort}). "
            "Check the installed package documentation/version and choose a supported "
            "configuration; no provider request was made."
        ) from error
