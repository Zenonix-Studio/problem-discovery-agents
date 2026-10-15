# Problem Discovery Workflow — Step 2 Decisions: Analysis Rules

**Status:** Agreed decisions for Step 2 (A1, A3, A4, A5)  
**Date:** 2026-10-14  
**Purpose:** Decision record / handoff for later architecture sessions and the coding agent. This is **not** an implementation specification or a proposal for the eventual open-source product.

## 1. Governing context and boundaries

- `Problem_Discovery_Research_Agent_Guide.md` remains the **authoritative research policy**. `Problem_Discovery_Workflow_Architecture_v1.md` defines minimal orchestration; `Problem_Discovery_Step1_Research_Tools_Evidence_Quality_Decisions.md` records prior research and evidence-quality decisions.
- Goal: a **minimal, manually run CrewAI Flow** to surface evidence-grounded, underserved developer problems, not a comprehensive market-research system.
- First pilot scope: **Developer Tools & Productivity**; the other two categories await manual pilot review.
- Preserve three agents: Research (two passes), Analysis (one pass), Evaluation (Stage 1 user value before Stage 2 team fit). **No additional agent or automatic Analysis → Research feedback loop.**
- Analysis must remain **solution-neutral**: investigate problems and alternatives, not pitch a product or design the eventual open-source repository.
- The Analysis Agent's output retains source/finding IDs and uncertainty. Evidence of a recurring pain is **not** evidence of demand for a new tool.

## 2. A1 — Clustering (agreed)

**Decision: Flexible, reasoned semantic clustering.** No rigid similarity thresholds or mandatory all-criteria matching.

The Analysis Agent compares findings in context, asking:

1. **User task/workflow:** Are users trying to accomplish substantially the same task?
2. **Underlying friction/failure mechanism:** Do reports describe substantially the same obstacle, rather than merely mentioning the same technology?
3. **Consequences:** Are the reported effects similar (e.g., time wasted, repeated errors, unreliable results)?

The **underlying friction** is especially important: a shared tool or setting, or a similar consequence alone, does not justify a merge. Conversely, different terminology or platforms do not require a split when the underlying problem is credibly shared.

**Required behavior:**

- Cluster duplicate or closely related findings into distinct **solution-neutral** problem statements; do not confuse symptoms with a common cause unless the evidence supports that cause.
- For each merge, record a concise **clustering rationale** and links to constituent Research Finding IDs and their evidence.
- Guard against **over-merging** (different problems grouped just because they involve the same stack) and **over-splitting** (the same mechanism split because authors use different language).
- When equivalence is uncertain, do **not** force a merge; retain separate findings/problems and note the ambiguity.

**Illustrative distinction (not a research finding):** Difficult-to-interpret CI failure messages and time-consuming manual CI log investigation may share a root friction; slow builds caused by ineffective dependency caching should not automatically join that cluster.

## 3. A3 — Alternatives & workarounds (agreed)

**Decision: Evidence-based, bounded alternatives research that explicitly investigates why users do not use, cannot use, or remain dissatisfied with existing approaches.**

For each analyzed problem, examine relevant alternatives in three groups:

| Type | What to investigate |
|---|---|
| **Built-in capabilities** | Does the existing platform/framework already address the task or friction? |
| **Existing tools** | Which directly relevant open-source or commercial tools address it, and how well? |
| **User workarounds** | What manual steps, scripts, adaptations, or workflow changes do affected users actually employ? |

**Required behavior:**

- Record **what each relevant alternative solves**, as well as **which limitations are actually evidenced**.
- Go beyond checking existence: seek firsthand explanations of **why users avoid an alternative, cannot adopt it, or still experience friction with it**.
- Investigate concrete adoption or usefulness barriers *when supported*, such as complexity, cost, integration/compatibility, reliability, missing functionality or poor workflow fit. **Do not assert these barriers simply because they seem plausible.**
- Distinguish:
  - **Supported gap:** direct user reports or verifiable limitations establish a specific shortcoming for the relevant context.
  - **Unknown gap:** alternatives exist or have been inspected, but their inadequacy has not been demonstrated.
  - **Need substantially met:** credible evidence indicates an available approach sufficiently handles the described need in the relevant context.
- Preserve linked URLs and evidence provenance for findings about alternatives and gaps. Report unknowns plainly; neither popularity nor a list of competitors proves adequacy or inadequacy.
- Keep the search **bounded and relevant**; no fixed minimum number of competitor tools. The purpose is to reach a defensible judgment about the problem, not an exhaustive market survey.

**Interpretation:** The existence of an alternative does not itself invalidate a user problem. But a purported opportunity must not be based on a **speculated** alternative gap.

## 4. A4 — Counterevidence (agreed)

**Decision: Lightweight but mandatory counterevidence check for every candidate analyzed problem.**

The Analysis Agent must make a proportionate attempt to challenge each candidate rather than only accumulating supporting reports. Check:

1. **Currency:** Is the reported friction still relevant in current versions/contexts, or tied to an older release?
2. **Resolution:** Was a reported issue actually fixed? Inspect closure reasons, linked PRs/releases and credible confirmations where accessible.
3. **Contrary experience:** Are there credible accounts showing existing capabilities or tools successfully address the problem?
4. **Scope:** Is the issue broad within its stated user segment, or restricted to a specific configuration, version or unusual usage pattern?

**Rules:**

- `open` is not proof that the issue persists; `closed` is not proof of a fix. Distinguish `wontfix`, duplicates, stale closures and evidenced fixes.
- Cite and retain counterevidence even if it weakens an otherwise interesting candidate.
- **No counterevidence found ≠ problem confirmed.** When source access, current status or contradictory accounts cannot be verified, record the uncertainty.
- Stop unproductive searches rather than retrying indefinitely. Unanswered questions are reported to human reviewers, **not** sent into an automated research feedback loop.

This check is a **minimum critical review**, not a requirement to exhaustively disprove every hypothesis.

## 5. A5 — Problem status classification (agreed)

**Decision: Retain the four indicative statuses already proposed in the architecture.** Do not introduce new status types, numeric confidence engines or complex decision trees in v1.

| Status | Meaning and use |
|---|---|
| `corroborated` | Distinct, defensibly independent firsthand observations support the same underlying friction. This **does not** imply proven demand for a new product or tool. |
| `needs_validation` | A plausible problem has limited corroboration or material unresolved uncertainty. **Retain it for review**, not as a rejected problem. |
| `outdated` | Evidence supports that the report relates to a superseded version/context or an issue already resolved. |
| `contradicted` | Credible counterevidence substantially challenges the claimed friction, its scope or the purported unmet need. |

**Required behavior:**

- Assign a short **classification rationale** with linked supporting and counterevidence IDs.
- Do not silently label a problem `outdated` merely because an issue is closed, or `corroborated` merely because multiple comments/upvotes appear.
- Keep **evidence relationship classifications** from Step 1 (`independent`, `uncertain`, `dependent`) distinct from these **problem-level statuses**.
- Retain rejected, contradicted, outdated and inconclusive observations in the report with clear reasons; avoid selective reporting.
- When evidence is insufficient to support a confident category, use the existing `needs_validation` status and explicitly describe the uncertainty rather than inventing evidence.

## 6. Analysis handoff and traceability

The Analysis Agent remains **single-pass**. Its structured `AnalysisOutput` should preserve, at minimum, the conceptual information already specified in the architecture:

- Stable **Problem ID** and constituent Research Finding IDs.
- Solution-neutral problem statement in the guide's form: **[user] struggles to [task] because [friction], causing [consequence]**.
- User segment, workflow and context.
- Source-linked supporting evidence and independence assessments, plus clustering rationale.
- Existing alternatives, built-in approaches, workarounds, documented limitations and remaining unknowns.
- Source-linked counterevidence, currency/resolution findings and gaps.
- One of the four problem statuses and its evidence-linked classification rationale.

These are **conceptual handoff requirements**, not final Pydantic field names or schemas. Preserve observations, inferences and unknowns as distinct categories of information. The Evaluation Agent, **not Analysis**, will later propose Stage 1 scores and conduct Stage 2 filtering where permitted.

## 7. Pilot review implications

During the first pilot's manual review, check that:

- Clusters reflect common underlying friction, not just shared keywords, technology or impact.
- Merge/split decisions are explainable and traceable to the original evidence.
- Existing capabilities, relevant tools and actual user workarounds were considered; claimed gaps have direct support.
- Reasons users avoid or find alternatives inadequate were **investigated**, or an explicit evidence gap was recorded.
- Every candidate received a proportionate counterevidence check; old/closed issues were not casually assumed to remain unsolved or to be fixed.
- Status labels reflect supporting and contrary evidence; `corroborated` was not presented as product demand validated.
- Weak, outdated and inconclusive observations were retained transparently rather than discarded to make the shortlist look stronger.

## 8. Historical open decisions (resolved by later records)

At the time of this Step 2 decision, the following remained open. They are retained for provenance only; Steps 3 and 4, the architecture handoff status, and `AGENTS.md` resolve them.

- **Step 3:** exact 0–3 scoring anchors, citation requirements for scores (E2), and when to return **Research needed** for insufficient evidence (E3). The historical five-dimension wording was superseded by the four-dimension `/12` rubric.
- **Step 4:** provider/model configuration, final Pydantic fields, enumerations beyond the agreed conceptual statuses, deterministic validators and pilot acceptance details.
- Exact prompt wording, search counts, tool-call budgets, retry behavior, Flow wiring, storage layout or filenames for runtime artifacts; delegate implementation mechanics to the coding agent consistent with these decisions.

**Historical next step:** Step 3 — Evaluation Rubric. This step is complete; see the Step 3 decision record.
