# Problem Discovery Workflow — Architecture Decisions (v1)

**Status:** Agreed architecture and Step 1–4 decisions; ready for coding-agent handoff (implementation pending)  
**Originally agreed:** 2026-10-14  
**Last reconciled:** 2026-10-15  
**Purpose:** Handoff/reference for a separate coding agent and future design sessions. This is **not** an implementation or a specification for the eventual open-source product.

## 1. Goal and source of truth

Build a **minimal, manually run CrewAI research workflow** to discover real, underserved developer problems and produce a trustworthy, evidence-grounded shortlist for human review. The workflow is only a research aid; **developing the harness must not become the main project**.

The existing `Problem_Discovery_Research_Agent_Guide.md` is the **authoritative research policy**: scope, evidence standards, Stage 1/Stage 2 evaluation, report sections and stopping criteria. This architecture document describes how to coordinate that research; where it is silent, the original guide governs.

Non-negotiables:
- **Problem first, solution later.** Current phase is *problem discovery only*: no product pitches, architecture for the eventual OSS product, repository names or implementation plans for that product.
- Prioritize **real user value**, then feasibility/team fit, then visibility/stars (secondary; no star predictions).
- Preserve direct, traceable evidence, independence of reports, uncertainty, unresolved searches, recent fixes and contradictory evidence. Never invent facts, sources, quotes or metrics.
- Keep scope and engineering effort minimal; expand tooling only if a specific research-quality issue requires it.

## 2. Research scope and pilot

The full guide covers three independent categories:
1. Developer Tools & Productivity
2. Workflow Automation & MCP
3. Mobile SDKs & AI Tooling

**First pilot:** only **Developer Tools & Productivity**; extend to the other two after manually reviewing pilot quality.

Provisional *workload caps*, not quotas or measures of demand: Pass 1 may surface up to ~8–10 signals; Pass 2 investigates up to ~4–5; seek two independent firsthand reports per signal where feasible. Fewer findings are acceptable; weak evidence must never be fabricated to fill a quota.

## 3. Minimal architecture

**Orchestration:** CrewAI **Flow** controls sequence and handoffs. Three specialized agents carry out the substantive work. Keep one straightforward execution path; no independent controller agent, elaborate crews, dashboard, database, continuous monitoring, or custom harness framework.

```text
Research Guide + category scope
             |
             v
Research Agent (two passes)
  1) Broad Discovery
  2) Evidence Deepening
             |
       ResearchOutput
             v
Analysis Agent (single pass)
  Clustering -> alternatives -> counterevidence -> gaps
             |
       AnalysisOutput
             v
Evaluation Agent + deterministic Python rules
  Stage 1: User Value (all eligible records)
       |-- insufficient evidence -> Research needed
       |-- low priority -> retain in report, no Stage 2
       `-- strong/promising with clear user benefit
                         |
                         v
               Stage 2: Team Fit
                         |
                         v
             Final research report
                         |
                 Human review/decision
```

**No automated feedback loop** from Analysis to Research in v1. Unresolved evidence gaps are reported honestly. Agent judgments are separated from deterministic rule enforcement.

## 4. Agent contracts and responsibilities

### Research Agent — two-pass discovery

**Input:** selected category, Research Agent Guide and research constraints.

- **Pass 1 (Broad Discovery):** identify user segments and recurring workflows; search GitHub Issues/Discussions/PR conversations, community discussions and relevant documentation for firsthand friction signals. Avoid idea/trend searches.
- **Pass 2 (Evidence Deepening):** revisit researchable signals; seek additional *independent* direct evidence and necessary context. A candidate for further research has an identifiable user/workflow, at least one relevant direct source, and concrete investigable friction; this is **not** validation or Stage 1 scoring.
- Record dates where known, direct links, what each source supports, observation vs inference, and unsuccessful searches / research gaps.

**Output (`ResearchOutput`, structured JSON/Pydantic):** findings with stable IDs, category, user segment, workflow/context, solution-neutral friction hypothesis, evidence items (source URL/type/date, observation and evidence classification), and research gaps.

**Must not:** propose solutions, assign Stage 1 scores, assert demand/validation or manufacture data.

### Analysis Agent — one-pass critical analysis

**Input:** ResearchOutput plus research guide.

- Cluster duplicate/related signals into distinct, **solution-neutral** problems without conflating symptoms with causes.
- Investigate existing alternatives, built-in capabilities and user workarounds, including specific limitations.
- Investigate contrary evidence and issue currency (closed vs actually fixed, recent versions, niche/isolated cases); distinguish independent people/projects from duplicate reports.
- Record unresolved questions and evidence gaps. **Do not automatically ask Research Agent to run again.**

**Output (`AnalysisOutput`, structured JSON/Pydantic):** stable problem IDs and source finding IDs; problem statement in guide format `[user] struggles to [task] because [friction], causing [consequence]`; user/workflow, linked supporting evidence, independence information, alternatives with source links, linked counterevidence, uncertainty and status.

**Indicative statuses:** `corroborated`, `needs_validation`, `outdated`, `contradicted`. *Corroborated* means independent observations support the pain; it does **not** mean product demand has been validated. Preserve `needs_validation` rather than dropping potentially important but under-evidenced issues.

**Must not:** invent evidence, assume feature requests mean tool adoption, propose projects, assign Stage 1 scores or rate team fit.

### Evaluation Agent — evidence-based assessment and reporting

**Input:** AnalysisOutput, research guide and team skills/CVs for Stage 2 only.

**Stage 1 (user value, always first):** LLM proposes **evidence-linked rationales and 0–3 scores, or `Research needed`,** for **four dimensions**:
1. Problem reality
2. Frequency / recurrence
3. Alternative gap
4. Meaningful benefit

**User access / validation is non-scored planning context.** Deterministic rules require all four dimensions to be scoreable before calculating **/12**: **10–12 Strong**, **7–9 Promising**, **0–6 Low priority**. If **any** dimension is unscoreable, overall Stage 1 is **Research needed** without a total, retaining defensible partial scores and evidence gaps. Missing evidence is not the same as a factual zero. Scores are prioritization aids, not demand probabilities. For detailed anchors and evidence-reference requirements, see `Problem_Discovery_Step3_Evaluation_Rubric_Decisions.md`.

**Stage 2 (only Stage-1 strong/promising candidates with an articulable user benefit):** assess core capability, demonstrable engineering skill, maintainable small OSS scope, practical constraints/costs and ability to demonstrate user value. Use qualitative **Strong / Partial / Weak / Unknown** ratings. Do not force equal contribution by both engineers, or AI/iOS into every problem.

**Deterministic enforcement:** code—not merely agent instructions—performs totals, thresholds, basic source/structure checks and the Stage 2 eligibility gate. Source counts alone do not prove evidence sufficiency; a single credible source may remain a hypothesis needing validation.

**Final output:** guide-compliant Markdown research report, including executive summary, landscape by category (within examined scope), Stage-1-ranked comparison, shortlisted problem cards, rejected/inconclusive findings, source appendix, uncertainty and next validation actions. The Evaluation Agent also synthesizes the report; **no separate Report Writer agent** in v1.

## 5. Data flow and traceability

At implementation time, define small Pydantic contracts (names are illustrative, not final code):
- `ResearchOutput` -> `ResearchFinding` -> `EvidenceItem`
- `AnalysisOutput` -> `AnalyzedProblem` -> alternatives, counterevidence, missing evidence
- `EvaluationOutput` -> Stage 1 breakdown, Stage 2 assessments (where permitted), report inputs

Every important claim should remain traceable to a direct URL and original finding/evidence ID; don't reduce the handoff to unsupported prose. Keep observed facts, model inferences and missing information distinct. Output intermediate **JSON** files and one final **Markdown** report so the two engineers can inspect results without extra infrastructure.

## 6. Pilot acceptance criteria

Manually review the initial run for:
- Whether linked sources actually substantiate the claimed user experience, including source independence and date/currency.
- Whether problem statements are solution-neutral and clustering neither over-merges nor artificially fragments issues.
- Whether alternatives, workarounds, recent fixes and counterevidence were genuinely checked.
- Whether evidence gaps remain explicit and scores can be traced to supporting findings.
- Whether Stage 1 precedes Stage 2, deterministic gates behave correctly, and no invalid source/count silently becomes “validated.”
- Whether the final report is useful for **human** prioritization, even if few candidates emerge.

No requirement to discover a particular number of “strong” opportunities. The output is a shortlist of **problems worth further validation**, not a selected OSS project.

## 7. Explicitly deferred implementation choices

To decide in a later session / by agreement before coding agent execution:
- Research tool access: web search, page retrieval and GitHub-specific access; how live URLs/status are verified.
- LLM/model/provider choices, cost/time limits, retries and structured-output reliability.
- Final Pydantic field schemas, error handling and file naming.
- CrewAI Flow wiring and tool configuration, after the above are fixed.

**Responsibility split:** This design session defines decisions and the handoff document; the **coding agent writes the code**. Keep implementation minimal and avoid adding features without an observed research-quality need.


## 8. Decision roadmap (completed; retained for traceability)

The following questions were addressed **in order of impact on research quality** in the Step 1–4 decision records. The questions are retained as decision provenance, not outstanding approvals. Keep the coding agent responsible for low-level framework wiring and file organization.

### Step 1 — Research tools & evidence quality (R1, R2, R4, R6)

- **R1 — Sources and tools:** Which tools will Research use for searching and retrieving GitHub Issues/Discussions, user communities, documentation and live pages? What access limits matter?
- **R2 — Search strategy:** How will Pass 1 generate and vary pain-oriented search queries; how will it avoid solution/trend-driven searches?
- **R4 — Independent corroboration:** How will Pass 2 seek additional reports, distinguish independent authors/projects and record uncertainty when identity or independence is unclear?
- **R6 — Source verification:** How will direct links, source context, dates, accessibility and current issue/resolution status be checked without inventing evidence?

**Decision outcome:** An approved minimal research-tool set and evidence verification rules. Preserve the previously agreed Two-Pass Research approach; do not introduce extra agents.

### Step 2 — Analysis rules (A1, A3, A4, A5)

- **A1 — Clustering:** What observable criteria justify merging reports into one underlying problem rather than keeping them separate?
- **A3 — Alternatives:** Which tools, built-in capabilities and workarounds must be checked, and what counts as evidence of a specific gap?
- **A4 — Counterevidence:** What deliberate searches should attempt to disconfirm a candidate problem, including updates or fixes?
- **A5 — Status classification:** How are resolved/outdated, contradicted, isolated and under-evidenced problems handled and retained for reporting?

**Decision outcome:** Simple, repeatable analysis criteria and linked evidence-gap reporting. Analysis remains single-pass with **no automatic research feedback loop**.

### Step 3 — Evaluation rubric (E1, E2, E3)

- **E1 — Score anchors:** What does a defensible 0, 1, 2 or 3 mean for each of the four Stage 1 user-value dimensions?
- **E2 — Evidence-linked justification:** What evidence and citations must accompany every score and qualitative judgment?
- **E3 — Insufficient evidence:** Under what conditions must the evaluation return **Research needed** rather than guessing or interpreting missing evidence as zero?

**Decision outcome:** A concrete Stage 1 rubric and rules for missing evidence. Use the Step 3 `/12` thresholds and Stage 2 gating; the LLM proposes justified judgments while deterministic code computes totals and enforces eligibility.

### Step 4 — Implementation contracts (M1, M3, M6)

- **M1 — Model configuration:** Which LLM/provider(s) will be used, and is a single model sufficient for all three agents given quality, cost and structured-output needs?
- **M3 — Data contracts:** What are the final required Pydantic input/output fields, status values, IDs and provenance links across agent handoffs?
- **M6 — Pilot acceptance:** How will the first Developer Tools & Productivity run be manually checked for correct sources, clustering, opposing evidence, scoring and actionable uncertainty?

**Decision outcome:** The minimal specification needed for the coding agent to implement the pilot.

### Deliberately delegated or postponed

Implementation-specific CrewAI Flow/Task wiring, filenames, directory layout, basic retry/error-handling mechanics and similar low-level choices can be delegated to the coding agent, provided they respect the constraints and approved data contracts above. Time/search budgets should be set only as needed for the pilot; avoid turning them into a broader platform project.

**Handoff status (2026-10-15):** Steps 1–4 agreed. See `Problem_Discovery_Step4_Implementation_Contracts_Decisions.md` for model/configuration, data-contract and pilot-review choices. Next action is coding-agent implementation followed by a manually reviewed pilot; avoid reopening settled decisions without a concrete issue.
