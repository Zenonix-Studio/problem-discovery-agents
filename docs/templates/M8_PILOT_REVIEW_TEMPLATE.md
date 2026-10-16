# M8 Pilot Review Record

Copy this file to `<run-directory>/m8_review.md` only after a successful M7 run. Fill every placeholder with observed review evidence; do not infer missing evidence or replace human inspection with test output.

## Run identity and artifact inventory

- Run directory: `<path>`
- Reviewer(s) and review date(s): `<names and dates>`
- Exact authorized command: `<command; no secret values>`
- Category: `Developer Tools & Productivity`
- Workflow focus: `<none or approved focus>`
- Manifest status and timestamps: `<status, started_at, finished_at>`
- Artifact inventory: `<list each required file and its presence>`
- Coverage, retrieval, date, and access limitations: `<observed limitations>`

Required successful-run artifacts: `research_output.json`, `analysis_output.json`, `evaluation_output.json`, `evidence_registry.json`, `report.md`, and `run_manifest.json`.

## Record-by-record audit

Add one row for every `Problem ID` in `analysis_output.json`, regardless of status, score, or Stage 2 eligibility. If no problem records exist, write `No problems generated` and complete the run-level criteria below without inventing a row.

| Problem ID | Finding IDs | Evidence IDs and direct URLs inspected | Source/excerpt, verification, independence, and limitations | Clustering; alternatives/workarounds; fixes/current status; counterevidence | Four Stage 1 assessments, total/status, and Stage 2 gate | Report treatment; unresolved uncertainty; record-level finding |
| --- | --- | --- | --- | --- | --- | --- |
| `<P-...>` | `<F-...>` | `<EV-... — URL>` | `<observed>` | `<observed>` | `<observed>` | `<observed>` |

## Five acceptance criteria

Use exactly `Pass` or `Fail`; provide a brief evidence-based rationale. A passing criterion is not product-demand validation.

| Criterion | Verdict (`Pass` / `Fail`) | Brief rationale and concrete examples/IDs |
| --- | --- | --- |
| Evidence Integrity — direct URLs/content substantiate claims; independence, limitations, and unknowns are accurate. | `<Pass or Fail>` | `<evidence>` |
| Research Quality — firsthand friction, workflow coverage, failed searches, and independent-support gaps are transparent. | `<Pass or Fail>` | `<evidence>` |
| Analysis Quality — solution-neutral clusters, alternatives/workarounds, current fixes, and counterevidence are checked or gaps flagged. | `<Pass or Fail>` | `<evidence>` |
| Evaluation Consistency — evidence-linked four-dimension `/12` rubric, partial-score rules, and deterministic Stage 2 gate are correct. | `<Pass or Fail>` | `<evidence>` |
| Report Usability — report supports human validation decisions with evidence and remaining uncertainty. | `<Pass or Fail>` | `<evidence>` |

## Unresolved uncertainty and next validation

- Source access/integrity gaps: `<items>`
- Coverage and research gaps: `<items>`
- Analysis/current-resolution gaps: `<items>`
- Unscoreable dimensions and targeted validation questions: `<items>`
- Other limitations: `<items>`

## Final disposition

`<Accepted for human use as a research pilot / Failed pending targeted correction>`

State why. Acceptance does not validate demand, select/build an OSS product, authorize another research category, or replace future human judgment.
