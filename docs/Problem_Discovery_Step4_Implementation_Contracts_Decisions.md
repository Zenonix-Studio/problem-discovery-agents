# Problem Discovery Workflow — Step 4 Decisions: Implementation Contracts

**Status:** Agreed decisions for Step 4 (M1, M3, M6)  
**Date:** 2026-10-15  
**Purpose:** Coding-agent handoff for a minimal problem-discovery research pilot; **not** an implementation of the eventual open-source product.

## 1. Governing policy and scope

- Research policy: `Problem_Discovery_Research_Agent_Guide.md`; architecture: `Problem_Discovery_Workflow_Architecture_v1.md`.
- Prior detailed decisions: `Problem_Discovery_Step1_Research_Tools_Evidence_Quality_Decisions.md`, `Problem_Discovery_Step2_Analysis_Rules_Decisions.md`, `Problem_Discovery_Step3_Evaluation_Rubric_Decisions.md`.
- **Step 3 governs Stage 1:** four dimensions, 0–3 each, total **/12** only when fully scoreable; **10–12 Strong, 7–9 Promising, 0–6 Low priority**, otherwise overall **Research needed** with no total. `User Access / Validation` is non-scored follow-up context.
- Pilot category: **Developer Tools & Productivity**. Minimal manually run CrewAI Flow: **Research Agent (two passes) → Analysis Agent (single pass) → Evaluation Agent → human review**. No new agents, automated research feedback loop, database, dashboard or elaborate harness. Problem discovery only; no eventual OSS product design.

## 2. M1 — Model configuration (agreed)

- Start with **one strong model shared by all three agents**, with distinct instructions, responsibilities and tool access.
- **Initial configured model:** `gpt-5.4-mini`, **reasoning effort:** `medium`. This is an agreed **starting configuration**, not evidence that this model will outperform alternatives; verify actual provider/model availability and parameter compatibility during implementation.
- **Provider and model must be configurable** without editing agent logic; permit later per-agent overrides if the pilot shows a specific quality/cost need, but do not introduce differing models now.
- Balance research quality with API cost. Record run-level token usage and estimated API cost where the provider exposes usable metadata; identify unknown components rather than inventing usage numbers. Assess search/retrieval provider expenses separately where relevant.
- Tool-use and structured-output reliability are quality criteria for the pilot, not assumed guarantees.
- **Step 1 tool decisions remain unchanged:** GitHub REST (issues/PRs/comments), selective GitHub GraphQL (Discussions), Tavily Search and Tavily Extract. Authentication and exact CrewAI integration are coding-agent choices.

## 3. M3 — Evidence registry and data contracts (agreed)

### 3.1 Central evidence registry and stable IDs

- Maintain one authoritative **JSON evidence registry** keyed by stable, unique Evidence IDs (illustratively `EV-001`, `EV-002`). Database not required.
- Research creates evidence records. Analysis may add evidence for alternatives, fixes or counterevidence into **the same registry**. Downstream records **reference IDs**, not copied evidence objects.
- Keep unique Research Finding IDs and Problem IDs, and trace Evaluation → Problem → Finding/Evidence → original direct URL. A source appearing more than once should not silently inflate independent corroboration.
- Preserve original evidence, distinction between observed/inferred/unknown, uncertainties, sources and access dates. Registry mutation/merge persistence specifics may be delegated but must not silently overwrite conflicting IDs.

### 3.2 EvidenceItem conceptual minimum

| Field | Meaning |
|---|---|
| `evidence_id` | Stable unique reference |
| `source_url` | Direct original source URL |
| `source_type` | GitHub Issue/Discussion/PR, forum, documentation, etc. |
| `published_at` | Source/post date, nullable when unknown |
| `accessed_at` | Date evidence was accessed/checked |
| `source_excerpt` | **Short verbatim excerpt**, nullable if unavailable/unverifiable; never invented; respect quotation limits |
| `observation` | What original retrieved content actually supports |
| `interpretation` | Explicitly separate inference, optional |
| `evidence_class` | Firsthand, documentation, technical verification, etc. |
| `independence` | `independent`, `dependent`, `uncertain` |
| `independence_rationale` | Reason for relationship assessment |
| `verification_status` | `verified`, `partial`, `unverified` (source/content checking, **not** issue resolution) |
| `limitations` | Retrieval gaps, unknown context/date, etc. |

The coding agent defines exact Pydantic types, optionality and practical enum naming while preserving semantics. Source verification is distinct from Analysis's determination of whether a reported issue is currently fixed. Unverified/inaccessible material cannot be presented as verified firsthand proof.

### 3.3 ResearchOutput

Three top-level conceptual sections:
- `findings`: stable Finding IDs, category, user segment, workflow/context, solution-neutral friction hypotheses and linked Evidence IDs.
- `evidence_registry`: authoritative evidence items.
- `research_coverage`: examined and unexamined workflows, unsuccessful searches, limitations and research gaps.

Research does not propose solutions, scores or validation claims. Approximate Pass 1/Pass 2 workload caps are **not quotas**.

### 3.4 AnalysisOutput

- `problems`: each has stable Problem ID, constituent Finding IDs, solution-neutral problem statement, user/workflow context, clustering rationale, linked supporting Evidence IDs and independence context, alternatives/built-in capabilities/workarounds with supported or unknown gaps, counterevidence references, currency/resolution findings, research gaps and status.
- `status` values: `corroborated`, `needs_validation`, `outdated`, `contradicted`. Corroboration is **not** validated product demand.
- Any **new evidence** is appended/merged into the shared registry with stable IDs; do not duplicate the full `ResearchOutput` in `AnalysisOutput`.
- Analysis is single-pass; there is **no** automatic Research rerun.

### 3.5 EvaluationOutput

Per analyzed problem:
- `problem_id`.
- `stage1_scores`: exactly four named dimensions, each containing defensible score `0..3` **or** `null`/`Research needed`, short rationale, existing Evidence ID references and counterevidence/uncertainty.
- `stage1_total`: integer **0..12 only if all four dimensions scoreable**; otherwise `null`.
- `stage1_status`: `Strong`, `Promising`, `Low priority` or `Research needed` (determined by Python rules).
- `stage2_assessment`: **only** for Stage-1-eligible `Strong`/`Promising` records with clearly articulable user benefit. Qualitative dimensions use `Strong / Partial / Weak / Unknown` with rationales; otherwise absent/null.
- `validation_gaps`: remaining evidence gaps, next verification actions and (if useful) non-scored user-access/reproducibility planning.

Evaluation Agent also produces **one Markdown research report** compliant with the guide; no separate Report Writer Agent. Structured intermediary outputs are JSON.

### 3.6 Deterministic validation and failure policy

**Fail Fast** for actual contract violations; surface an actionable error rather than quietly dropping evidence or computing unsupported rankings:
- Uniqueness of IDs in their type namespace; referenced Evidence, Finding and Problem IDs must exist.
- Required fields present/nonblank, enums within permitted values, score range `{0,1,2,3}` for scored dimensions.
- Distinguish legitimately nullable unknown dates/excerpts/inferences from broken contracts.
- Compute total and Stage 1 label **in code**; no total if any dimension unscoreable. Enforce Stage 2 eligibility deterministically.
- Check presence/consistency of score rationales and their evidence refs; Python does **not** prove a source's semantic truth, independence or score quality.
- Real-world missing/contradictory evidence is **not** itself a schema failure: preserve as `Research needed` or explicit uncertainty according to Step 3.

Exact class names, JSON file names, persistence shape, exception classes and CrewAI wiring remain coding-agent implementation details.

## 4. M6 — Pilot acceptance and review (agreed)

### 4.1 Full Review

On the **first Developer Tools & Productivity pilot**, manually inspect **every produced problem record**, its referenced evidence and excerpt/source context, clustering and contrary evidence, score justification and report conclusions. This is an audit of generated records, not a requirement to exhaustively research the whole internet.

### 4.2 Five Pass/Fail criteria

Record **Pass / Fail + short rationale** for each; no new numerical meta-score:

| Criterion | Pass requirement |
|---|---|
| **Evidence Integrity** | Direct URLs and accessible original content actually support claims; independence, limitations and unknowns reported accurately. |
| **Research Quality** | Firsthand user friction sought; workflow coverage, failed searches and independent support/gaps transparently captured. |
| **Analysis Quality** | Defensible solution-neutral clusters; relevant alternatives, user workarounds, current fixes and counterevidence checked or gaps flagged. |
| **Evaluation Consistency** | Evidence-linked four-dimension `/12` rubric, partial-score rules and deterministic Stage 2 gate applied correctly. |
| **Report Usability** | Markdown report permits humans to tell which problems warrant validation, why, on what evidence and with which remaining uncertainties. |

Automated data-integrity tests supplement, not replace, this review. **No quota of Strong candidates:** few findings, or no Strong problems, is not automatically a failed pilot if they were investigated and reported faithfully.

### 4.3 If pilot fails: Targeted Fix & Rerun

1. Record the failed criterion and concrete examples.
2. Fix the specific responsible agent behavior, retrieval, prompt, schema or validator without expanding scope by default.
3. Rerun the pilot and review the outputs.
4. Compare whether the failure was corrected and whether new quality issues emerged.

Do not add an agent, platform, monitoring system or feedback loop as the default response to poor pilot quality.

## 5. Coding-agent handoff and intentionally delegated choices

Implement the **smallest working** manually invoked CrewAI Flow consistent with Steps 1–4. Preserve inspectable intermediate JSON, authoritative evidence registry and final Markdown. Choose practical Pydantic class/enum declarations, Flow/Task wiring, credential loading, sensible error messages, minimal retries, directory layout and filenames. Do not invent new research-policy decisions, model performance claims, hard quotas or additional infrastructure.

**Document reconciliation:** On 2026-10-15 the research guide and architecture were updated to reflect the Step 3 four-dimension `/12` Stage 1 rubric. The Step 3 decision record remains the authoritative detail for the exact scoring anchors; the historical Step 1 and Step 2 decision records were preserved without rewriting their provenance.
