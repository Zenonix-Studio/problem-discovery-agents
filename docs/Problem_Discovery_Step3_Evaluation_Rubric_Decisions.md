# Problem Discovery Workflow — Step 3 Decisions: Evaluation Rubric

**Status:** Agreed decisions for Step 3 (E1, E2, E3)  
**Date:** 2026-10-15  
**Purpose:** Decision record / handoff for later architecture sessions and the coding agent. This is **not** an implementation specification or a proposal for the eventual open-source product.

## 1. Governing context and boundaries

- `Problem_Discovery_Research_Agent_Guide.md` remains the baseline research policy; `Problem_Discovery_Workflow_Architecture_v1.md` defines minimal orchestration. Step 1 and Step 2 decision records govern research/evidence collection and analysis, respectively.
- **Explicit amendment agreed in Step 3:** Stage 1 uses **four scored dimensions, maximum 12 points**, not the five dimensions and 15-point thresholds in the earlier guide/architecture. This decision record governs Stage 1 scoring and thresholds; the guide and architecture were reconciled on 2026-10-15. Other research policies and Stage 2 constraints remain in effect.
- Goal: a minimal, manually run CrewAI Flow producing evidence-grounded developer problems for human review. First pilot category: **Developer Tools & Productivity**.
- Preserve **Research Agent (two passes) → Analysis Agent (single pass) → Evaluation Agent**, followed by human review. No new agent, controller, automated Analysis → Research loop, database, or dashboard.
- Stage 1 measures **user value before Stage 2 team fit**. Strong/promising Stage 1 candidates with a clear user benefit may enter Stage 2; low-priority or research-needed records do not. Ratings are prioritization aids, **not predictions of adoption, stars, or market demand**.
- Keep observations, inferences, contradictory evidence and unknowns separate. An Evaluation Agent must not invent measurements, sources, numerical benefits or certainty.

## 2. E1 — Score anchors (agreed)

**Decision: Four evidence-anchored Stage 1 dimensions, each scored 0–3.** `User Access / Validation` is **removed from the scored rubric**; it may remain a non-scored field for planning follow-up validation. Accessibility of users or test environments should not artificially lower the intrinsic user-value score.

| Dimension | What it evaluates | Maximum |
|---|---|---:|
| **Problem Reality** | Whether the described friction is substantiated by genuine firsthand user experience and independent technical confirmation | 3 |
| **Frequency / Recurrence** | How repeatedly the friction arises for users and across relevant users/projects | 3 |
| **Alternative Gap** | Whether existing capabilities, tools and workarounds demonstrably fail to meet the relevant need | 3 |
| **Meaningful Benefit** | Whether removing the friction would plausibly create significant, concretely evidenced user value | 3 |
| **Total** | **Only when all four dimensions are scoreable** | **12** |

### 2.1 Problem Reality

| Score | Anchor |
|---|---|
| **0** | Available credible evidence indicates the asserted problem does not apply in the relevant circumstances or no longer exists there. |
| **1** | At least one credible firsthand report describes the friction, but independent corroboration is absent. |
| **2** | At least two defensibly independent firsthand reports support the same underlying friction. |
| **3** | Independent firsthand reports **plus additional direct verification**, such as reproducible failure behavior, pertinent technical logs, or reliable test results substantiating the specific friction. |

**Rules:**
- **Extra verification is required for 3**; a high count of similar reports alone does not meet that anchor.
- Independence uses the Step 1 definitions (`independent`, `uncertain`, `dependent`); comments or repeated posts from one source must not be inflated into independent reports.
- An unverified claim or missing evidence is **not automatically a factual zero**. Use E3 where a defensible score is unavailable.
- Even a corroborated real problem does not establish demand for a new OSS product.

### 2.2 Frequency / Recurrence

| Score | Anchor |
|---|---|
| **0** | Credible evidence indicates the reported event is exceptional or one-off in the stated context rather than a recurring friction. |
| **1** | The friction is reported, but evidence of recurrence is weak or limited. |
| **2** | There is evidence of repeat occurrences for affected users **or** comparable occurrences across distinct users. |
| **3** | Strong evidence shows regular recurrence across relevant independent users or projects, or a comparably well-substantiated sustained recurring burden in the stated segment. |

**Rules:**
- Consider both **frequency per affected user** and **reach across users/projects**. Neither the sheer number of reports nor a one-time event automatically implies frequent recurring burden.
- A few users experiencing the same interruption daily may represent a more recurring burden than many users each experiencing it once. Assess the documented pattern in context rather than applying a rigid user-count threshold.
- Do not invent occurrence rates, affected-user percentages or periods that are absent from the evidence.

### 2.3 Alternative Gap

| Score | Anchor |
|---|---|
| **0** | Credible evidence shows an existing relevant approach sufficiently meets the need in the stated context. |
| **1** | Alternatives exist and some limitations have been reported, but their actual effect on users remains weakly supported or uncertain. |
| **2** | Specific, evidenced shortcomings of current approaches negatively affect identifiable users' workflows. |
| **3** | Relevant alternatives have been examined and strong **firsthand user evidence** establishes significant, recurring unmet needs despite those approaches. |

**Rules:**
- **No alternative available** does not on its own imply a large gap; **several alternatives available** does not on its own imply there is no gap.
- A technical feature omission alone is insufficient for **3**. The reported limitation must be shown to matter to real users.
- Use Step 2's distinctions: `supported gap`, `unknown gap`, and `need substantially met`. A conjectured gap cannot be promoted as evidence.

### 2.4 Meaningful Benefit

| Score | Anchor |
|---|---|
| **0** | Credible evidence indicates the expected user benefit is negligible or not meaningful in the examined context. |
| **1** | Some benefit is plausible, but the user impact is limited or uncertain. |
| **2** | Concrete evidence shows noticeable user cost, delay, errors, productivity loss, reliability issues or similarly meaningful friction. |
| **3** | Strong evidence supports serious operational/user impact **and** a specific measurable outcome that removing the friction could improve. |

**Rules:**
- **Existing numeric impact measurements are not mandatory for 3.** Do require (1) directly supported concrete consequences and (2) an identifiable outcome that could be measured, such as deployment failure rate, repeated errors, time-to-complete or operational interruptions.
- Do not invent hypothetical improvement percentages, time savings or cost reductions. Distinguish an **outcome that is measurable in principle** from an **improvement already observed or quantified**.
- Value can arise from reliability, simplicity, time, cost, accuracy, accessibility or reduction in user risk; avoid defaulting to time saved alone.

### 2.5 Total and classification

**Decision: Replace the previous `/15` total and thresholds with `/12` thresholds.** The score is a transparent prioritization tool, not a validated probability of user demand.

| Fully scored Stage 1 total | Classification |
|---|---|
| **10–12** | `Strong` — candidate for deeper validation |
| **7–9** | `Promising` — meaningful potential with uncertainties to verify |
| **0–6** | `Low priority` — retain for reporting, including noteworthy severe niche exceptions |
| **One or more unscoreable dimensions** | `Research needed` — **no total score and no Strong/Promising/Low priority classification** |

Only `Strong`/`Promising` candidates **with a clearly articulable user benefit** are eligible for Stage 2. Do not use team capability, AI/iOS fit, likely stars or ease of access to users to alter Stage 1 scores. The separate Stage 2 qualitative fit labels remain `Strong / Partial / Weak / Unknown`.

## 3. E2 — Evidence-linked justification (agreed)

**Decision: Every scored dimension requires `Score + Rationale + Evidence References`.** Relevant counterevidence and uncertainty must be considered, not hidden.

**Required behavior:**

1. **Score:** Give one integer from 0 to 3 **only if supported by the available evidence**.
2. **Rationale:** Briefly explain why that specific score anchor applies, distinguishing observation from inference. Address material contradictory evidence and uncertainty relevant to the judgment.
3. **Evidence references:** Link the rationale to existing, stable Evidence IDs that resolve through the Research/Analysis handoff to original direct URLs and their supported claims. Never cite an invented ID or rely exclusively on a search snippet.
4. **Counterevidence:** If the Analysis Agent recorded fixes, sufficient alternatives, contrary user accounts or restricted applicability, include their bearing on the score. Evidence for a problem's existence must not override credible evidence that it has been resolved.
5. **No false certainty:** Report missing proof, uncertain independence and unresolved current status explicitly. Do not turn a lack of located counterevidence into positive validation.

**Illustrative example (not an actual research finding):**

- Dimension: `Problem Reality`; score: `2/3`.
- Rationale: Two independent developers report the same CI debugging friction; no reproducible failure or additional technical verification has been established.
- Supporting evidence IDs: `EV-001`, `EV-004` (illustrative placeholders only; real records require actual source links).

**Deterministic Python checks:** validate required structure, score range and referenced ID existence/consistency. They can enforce arithmetic and Stage 2 gates, but **cannot certify the semantic truth of a source, its interpretation, independence, or the quality of a rationale**. Retain human pilot review.

The same transparency principle applies to Stage 2 qualitative judgments: state the reason and the observed team capability, cost, maintenance or demonstration constraint behind each assessment rather than asserting fit without basis. Specific Stage 2 data fields remain a Step 4 contract decision.

## 4. E3 — Insufficient evidence (agreed)

**Decision: Flexible partial scoring, without a misleading total.** Evaluate every dimension that can be supported; flag the others as `Research needed` while keeping their known evidence and precise gaps.

### 4.1 When evidence is insufficient

Use `Research needed` for an individual dimension when, for example:

- There is no accessible, directly relevant firsthand evidence for claims requiring firsthand confirmation.
- Source access or retrieved content cannot substantiate the particular claim; search snippets alone do not establish firsthand evidence.
- Material uncertainty or unresolved contradiction prevents selecting a defensible 0–3 anchor.
- Essential information about recurrence, existing alternatives or impact is missing, and choosing a score would amount to guessing.

These are **judgment criteria**, not automatic rules that each unknown or single-source problem must always be rejected. A **single credible firsthand report** can still support a limited `Problem Reality` score of 1 when that anchor is satisfied.

### 4.2 Partial scoring behavior

- Preserve any dimension-specific **defensible 0–3 scores**, rationales and source references.
- Mark an unscoreable dimension as `Research needed`, not `0`.
- **If at least one of the four dimensions is unscoreable, omit the `/12` total and the Stage 1 Strong/Promising/Low priority classification.** Overall Stage 1 outcome is `Research needed`.
- Report **which evidence is missing and what targeted research or validation could resolve it**. Do not trigger an automatic Research Agent rerun.
- **Stage 2 remains gated off** while overall Stage 1 is `Research needed`, even if already scored dimensions appear favorable.
- Do not discard an otherwise valuable problem merely because one dimension currently lacks evidence. Retain it visibly as inconclusive for human review.

**Illustrative example (not an actual research finding):**

| Dimension | Assessment |
|---|---|
| Problem Reality | 3 |
| Frequency / Recurrence | 2 |
| Alternative Gap | `Research needed` |
| Meaningful Benefit | 3 |
| **Overall Stage 1** | **`Research needed` — no `8/12` total or priority label** |

The missing Alternative Gap evidence must be investigated in a future validation step, not silently treated as 0 or inferred from absence of known tools.

## 5. Evaluation handoff, traceability and reporting

The Evaluation Agent consumes `AnalysisOutput` plus the research guide and, **only for Stage-2-eligible candidates**, the team's skills/CVs. Conceptual evaluation outputs should retain:

- Stable Problem ID, linked Research Finding IDs and existing Evidence IDs/direct URLs.
- Four Stage 1 dimension judgments, each with a score **or** `Research needed`, evidence-linked rationale and material opposing evidence/gaps.
- An overall Stage 1 label and `/12` total **only when fully scoreable**; otherwise the overall `Research needed` outcome with no total.
- Stage 2 qualitative judgments **only for eligible Strong/Promising candidates** with a clear user benefit.
- Specific unresolved validation questions, including **user access/reproducibility as non-scored planning context** when known.
- All relevant rejected, outdated, contradicted and inconclusive problems for transparent final reporting.

The final Markdown report must preserve the guide's main reporting purposes: executive summary, landscape within the examined category, ranked comparison for fully scored candidates, shortlist cards, inconclusive/rejected observations, sources and next validation actions. `Research needed` records should be clearly shown **without fabricating ranks or totals**. These are **conceptual handoff requirements**, not final Pydantic field names or persistence choices.

## 6. Deterministic enforcement and pilot review implications

**Deterministic rules (not just agent instructions) must:**

- Accept scores only in `{0, 1, 2, 3}` for scored dimensions; treat an unscoreable result separately rather than coercing to zero.
- Require all four dimensions to have defensible scores before summing to `/12` and applying the agreed thresholds.
- Block Stage 2 unless Stage 1 is fully scored `Strong` or `Promising` **and** the user benefit is explicitly articulable.
- Check presence and consistency of required rationale/evidence-reference fields and referenced IDs, as far as machine-checkable.
- Preserve unresolved evidence gaps and intermediate judgments for human review.

**Pilot manual review should check:**

- Whether scores meet the documented anchors and are traceable to actual firsthand sources.
- Whether Problem Reality 3 includes technical verification **beyond** independent firsthand reports.
- Whether Frequency weighs recurrence and reach without treating report volume as a frequency estimate.
- Whether Alternative Gap 3 includes strong firsthand support, rather than only inferred missing features.
- Whether Meaningful Benefit 3 shows concrete impact and a measurable outcome without fabricated numeric gains.
- Whether opposing evidence and resolved/outdated cases meaningfully affect scoring.
- Whether partial scoring, absence of totals and Stage 2 gating work correctly.
- Whether `User Access / Validation` is tracked for follow-up if useful **but not counted in Stage 1**.

## 7. Reconciliation of earlier documents (completed)

At the time of this Step 3 decision, the earlier guide and architecture specified **five** Stage 1 dimensions, `/15`, and the old thresholds (`12–15`, `8–11`, `0–7`). The Step 3 change superseded those exact scoring provisions. The following reconciliation was completed on 2026-10-15 before implementation or pilot execution:

1. `Problem_Discovery_Research_Agent_Guide.md` — updated the Stage 1 dimension list, `/12` scoring text, category thresholds, and report tables/examples.
2. `Problem_Discovery_Workflow_Architecture_v1.md` — updated the Stage 1 dimension list, sum/threshold rules, decision roadmap wording, and references to scored dimensions.
3. Later data contracts, validators, prompts, reports, and tests must use the four-dimension `/12` rubric and retain User Access / Validation as a **non-scored** validation-planning field where relevant.

The original decision context is preserved here as provenance; the guide and architecture now use the four-dimension `/12` rubric.

## 8. Historical open decisions (resolved by Step 4)

At the time of this Step 3 decision, the following remained open. They are retained for provenance only; Step 4 and the architecture handoff status resolve them.

- **Step 4 (M1):** LLM/provider selection, model allocation across agents and practical cost/latency/structured-output tradeoffs.
- **Step 4 (M3):** final Pydantic field names/types, schema details, ID formats, storage naming, error semantics and validation implementation.
- **Step 4 (M6):** concrete pilot acceptance samples, review procedure and run-level checks.
- Exact prompts, search/tool-call counts, provider parsing, low-level Flow wiring, retry policies or code/file organization; delegate implementation mechanics to the coding agent within the approved constraints.

**Historical next step:** Step 4 — Implementation Contracts. This step is complete; see the Step 4 decision record.
