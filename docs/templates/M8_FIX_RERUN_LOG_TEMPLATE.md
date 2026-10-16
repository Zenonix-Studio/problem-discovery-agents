# M8 Targeted Fix & Rerun Log

Create this record only after a completed M8 review has at least one failed acceptance criterion. It documents targeted correction and comparison; it does not authorize an automatic rerun, scope expansion, or architecture change.

## Original review

- Original run directory: `<path>`
- Original review record: `<path>`
- Failed criterion: `<Evidence Integrity / Research Quality / Analysis Quality / Evaluation Consistency / Report Usability>`
- Concrete example: `<Problem ID, Finding ID, Evidence ID/direct URL, report section, and observed issue>`
- Why this is a failure: `<brief rationale>`

## Targeted correction proposal

- Responsible boundary: `<prompt / tool or retrieval behavior / schema / validator / agent behavior>`
- Smallest proposed correction: `<change>`
- Scope check: `<why this does not add an agent, provider, category, database, dashboard, or automatic loop>`
- Separate implementation authorization received: `<yes/no; reference>`
- Separate live-rerun authorization and approved command/focus: `<yes/no; reference>`

## Rerun comparison

- Rerun directory: `<path>`
- Rerun review record: `<path>`
- Original issue resolved? `<yes/no/partially — evidence>`
- Remaining limitations: `<items>`
- Newly introduced issues: `<items or none observed>`
- Five-criterion verdict changes: `<criterion → original verdict → rerun verdict and rationale>`

## Follow-up decision

`<Stop after accepted review / retain failure for further scoped decision>`

Do not infer permission to expand scope from this log.
