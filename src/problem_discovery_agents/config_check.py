"""Local configuration check; intentionally performs no external calls."""

from __future__ import annotations

from .model_config import ModelConfigurationError, build_shared_llm
from .settings import ConfigurationError, validate_runtime_configuration


def main() -> int:
    try:
        settings = validate_runtime_configuration()
        build_shared_llm(settings)
    except (ConfigurationError, ModelConfigurationError) as error:
        print(f"Configuration check failed: {error}")
        return 1

    print(
        "Configuration check passed: settings and the local CrewAI wrapper accepted "
        "the shared model configuration. No external request was made."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
