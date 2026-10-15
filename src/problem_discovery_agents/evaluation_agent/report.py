"""Pure report context construction and structural completeness checks for M6."""

from __future__ import annotations

import re

from ..contracts import AnalysisOutput, EvaluationOutput, EvidenceRegistry, ResearchOutput

REQUIRED_HEADINGS = (
    "## Executive summary", "## Examined landscape", "## Comparison",
    "## Shortlisted problem cards", "## Rejected and inconclusive observations",
    "## Source appendix", "## Validation questions",
)

REQUIRED_REPORT_CONTENT = (
    "Problem Reality", "Frequency / Recurrence", "Alternative Gap", "Meaningful Benefit",
    "Alternatives", "Counterevidence", "Potential measurable outcome", "Stage 2",
    "Next validation",
)


def build_report_context(
    research: ResearchOutput, analysis: AnalysisOutput, evaluation: EvaluationOutput,
    registry: EvidenceRegistry,
) -> dict[str, object]:
    return {
        "research_coverage": research.research_coverage.model_dump(mode="json"),
        "problems": [problem.model_dump(mode="json") for problem in analysis.problems],
        "evaluations": evaluation.model_dump(mode="json"),
        "evidence_registry": registry.model_dump(mode="json"),
    }


def validate_report_markdown(
    markdown: str, evaluation: EvaluationOutput, registry: EvidenceRegistry,
) -> None:
    missing = [heading for heading in REQUIRED_HEADINGS if heading not in markdown]
    missing_content = [label for label in REQUIRED_REPORT_CONTENT if label not in markdown]
    problem_ids = [record.problem_id for record in evaluation.evaluations]
    missing_problems = [problem_id for problem_id in problem_ids if problem_id not in markdown]
    cited_ids = set(re.findall(r"\bEV-[A-Za-z0-9_-]+\b", markdown))
    known_ids = set(registry.by_id())
    unknown_ids = sorted(cited_ids - known_ids)
    urls = set(re.findall(r"https?://[^\s)>]+", markdown))
    known_urls = {str(item.source_url) for item in registry.evidence}
    unknown_urls = sorted(url.rstrip(".,") for url in urls if url.rstrip(".,") not in known_urls)
    errors: list[str] = []
    if missing:
        errors.append("missing required headings: " + ", ".join(missing))
    if missing_content:
        errors.append("missing required report content: " + ", ".join(missing_content))
    if missing_problems:
        errors.append("missing evaluated Problem IDs: " + ", ".join(missing_problems))
    if unknown_ids:
        errors.append("references unknown Evidence IDs: " + ", ".join(unknown_ids))
    if unknown_urls:
        errors.append("references URLs absent from authoritative registry: " + ", ".join(unknown_urls))
    if errors:
        raise ValueError("Invalid Evaluation report: " + "; ".join(errors))
