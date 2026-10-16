"""Inspectable, atomic filesystem artifacts for one manual research run."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from .contracts import AnalysisOutput, EvaluationOutput, EvidenceRegistry, ResearchOutput
from .model_config import ModelConfigurationError
from .settings import ConfigurationError
from .validation import ContractValidationError


def safe_error_message(error: Exception) -> str:
    """Keep known contract details, but never persist arbitrary provider errors."""

    if isinstance(error, (ConfigurationError, ContractValidationError, ModelConfigurationError)):
        return str(error)
    return f"{type(error).__name__}: operation failed; inspect the failed stage and safe diagnostics."


class RunManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = "running"
    completed_stage: str | None = None
    failed_stage: str | None = None
    error: str | None = None
    request: dict[str, str | None]
    artifacts: list[str] = Field(default_factory=list)
    started_at: datetime
    finished_at: datetime | None = None
    diagnostics: dict[str, object] = Field(default_factory=dict)


class ArtifactWriter:
    """Own a unique run directory and only write already-validated records."""

    def __init__(self, root: Path, *, request: dict[str, str | None]) -> None:
        root.mkdir(parents=True, exist_ok=True)
        self.run_dir = root / f"run-{datetime.now(UTC):%Y%m%dT%H%M%SZ}-{uuid4().hex[:8]}"
        self.run_dir.mkdir()
        self._manifest = RunManifest(request=request, started_at=datetime.now(UTC))
        self._write_manifest()

    def write_research(self, output: ResearchOutput, diagnostics: dict[str, object]) -> None:
        self._write_json("research_output.json", output.model_dump(mode="json"))
        self._advance("research", diagnostics)

    def write_analysis(self, output: AnalysisOutput, diagnostics: dict[str, object]) -> None:
        self._write_json("analysis_output.json", output.model_dump(mode="json"))
        self._advance("analysis", diagnostics)

    def write_final(
        self, output: EvaluationOutput, registry: EvidenceRegistry, report_markdown: str,
        diagnostics: dict[str, object],
    ) -> None:
        self._write_json("evaluation_output.json", output.model_dump(mode="json"))
        self._write_json("evidence_registry.json", registry.model_dump(mode="json"))
        self._write_text("report.md", report_markdown)
        self._manifest.completed_stage = "evaluation"
        self._manifest.status = "succeeded"
        self._manifest.finished_at = datetime.now(UTC)
        self._merge_diagnostics(diagnostics)
        self._write_manifest()

    def fail(self, stage: str, error: Exception, diagnostics: dict[str, object]) -> None:
        self._manifest.status = "failed"
        self._manifest.failed_stage = stage
        self._manifest.error = safe_error_message(error)
        self._manifest.finished_at = datetime.now(UTC)
        self._merge_diagnostics(diagnostics)
        self._write_manifest()

    def _advance(self, stage: str, diagnostics: dict[str, object]) -> None:
        self._manifest.completed_stage = stage
        self._merge_diagnostics(diagnostics)
        self._write_manifest()

    def _merge_diagnostics(self, diagnostics: dict[str, object]) -> None:
        self._manifest.diagnostics = {**self._manifest.diagnostics, **diagnostics}

    def _write_manifest(self) -> None:
        self._write_json("run_manifest.json", self._manifest.model_dump(mode="json"))

    def _write_json(self, name: str, value: object) -> None:
        self._write_text(name, json.dumps(value, indent=2, sort_keys=True) + "\n")

    def _write_text(self, name: str, value: str) -> None:
        destination = self.run_dir / name
        temporary = destination.with_name(f".{destination.name}.{uuid4().hex}.tmp")
        temporary.write_text(value, encoding="utf-8")
        os.replace(temporary, destination)
        if name not in self._manifest.artifacts:
            self._manifest.artifacts.append(name)
