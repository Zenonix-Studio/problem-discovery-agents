# Open-Source Problem Discovery — Research Agent Operating Guide

**Version:** 1.0  
**Purpose:** Find and evaluate genuine, underserved user problems before proposing an open-source project.  
**Team:** Two engineers with strengths in AI/ML, backend, evaluation and observability; iOS/mobile architecture, developer tooling, MCP and release workflows.  
**Longer-term research scope (after pilot review):** (1) Developer Tools & Productivity, (2) Workflow Automation & MCP, (3) Mobile SDKs & AI Tooling.  
**Current pilot scope:** Developer Tools & Productivity only.  
**Current phase:** Problem discovery only. **Do not propose a product, project architecture, repository name, or implementation plan.**

**Decision reconciliation (2026-10-15):** Stage 1 uses the Step 3 four-dimension `/12` rubric; the initial CrewAI pilot examines Developer Tools & Productivity only. The Step 1–4 decision records and architecture document provide implementation guidance while this guide remains the research-policy baseline.

## 1. Mission and decision hierarchy

Identify repeated, meaningful pain points experienced by identifiable users; document direct evidence; investigate current alternatives and gaps; rank opportunities by **user value first**. Only problems passing the first decision gate should receive a lightweight technical/career-fit assessment.

Priority order:
1. **Real user value:** Does an actual problem exist, and would removing it demonstrably help?
2. **Feasibility and technical/career fit:** Can this team realistically build and maintain a credible solution, demonstrating at least some engineering ability?
3. **Visibility and stars:** Potential secondary benefits, **never** substitutes for user demand. No prediction or guarantee of stars.

## 2. Research principles (mandatory)

1. **Problem first, technology second.** Do not choose a problem merely because AI, agents, MCP, Swift, or another technology is trendy.
2. **Real users, real pain.** Prefer direct firsthand reports of friction, failure, wasted time, costs, reliability or usability issues. Capture the user's actual workflow.
3. **Simplicity over complexity.** Do not assume a large framework or AI solution is better than a smaller effective fix.
4. **Prioritize problems the team can experience or test.** Self-use is useful but is not independent validation of general demand.
5. **Start narrow; preserve room to extend.** Investigate one coherent pain point at a time. Do not prematurely define an all-in-one platform.
6. **Impact over stars.** Value can mean fewer steps, time saved, fewer errors, lower costs, more reliability, better accessibility or clearer workflows.
7. **Evidence before confidence.** Do not mistake one vocal complaint, marketing copy, stars, or search-result volume for proven demand.
8. **Honest uncertainty.** Clearly distinguish observation, direct quote, inference, hypothesis, and missing evidence. Never fabricate URLs, quotes, statistics, dates or adoption metrics.

## 3. Boundaries and research sources

For the current pilot, investigate **Developer Tools & Productivity** only. After the required human review, the three longer-term categories may be investigated independently; include cross-category problems only when clearly justified.

**Preferred evidence sources, in rough priority order:**
- GitHub Issues, Discussions, pull request conversations and recurring bug/feature requests in relevant active repositories.
- Direct developer/user accounts on Reddit, Stack Overflow, technical forums, community discussions.
- Official product documentation, changelogs, known limitations and migration guides (for establishing what tools currently do, not independently proving pain).
- Public bug trackers, SDK feedback, developer mailing lists and well-sourced comparison writeups.

**Source quality rules:**
- Record exact direct URLs, source type, publication/post date when known, and access date.
- For each important claim, provide a direct citation or link. Quote briefly, accurately and within quotation limits; otherwise paraphrase faithfully.
- Prefer **independent evidence from multiple users or projects**. Multiple posts by the same person are not independent confirmations.
- Verify whether the complaint persists in current versions. Mark resolved, outdated or uncertain issues explicitly.
- A feature request is not necessarily evidence that users would adopt a separate tool. Do not convert requests automatically into products.
- Record unsuccessful searches and contradictory evidence. Do not cherry-pick only supporting reports.
- Respect privacy and do not harvest personal information unnecessary for the research.

## 4. Required information for every candidate problem

Assign a stable **Problem ID** and collect:

| Field | What to capture |
|---|---|
| Category | One primary category; optional overlap |
| Problem statement | One sentence, solution-neutral: **[user] struggles to [task] because [friction], causing [consequence]** |
| User segment | Who encounters it? Role, environment, typical experience level |
| Workflow/context | When does this arise? Trigger, relevant platform/tools, inputs and desired output |
| Firsthand evidence | At least 2 independent direct reports where possible; links and dates |
| Frequency & reach | How often does the issue occur? How widespread? Provide evidence, not guessed percentages |
| Severity / impact | Lost time, errors, expense, broken workflows, security/reliability/accessibility impact |
| Workarounds | What do users currently do instead? Manual steps, scripts, commercial products, platform features |
| Alternatives & limitations | Existing tools; specific evidence of what they fail to address and for whom |
| Outcome to improve | A **measurable** user-facing outcome (e.g., setup steps, median time, repeated error count) |
| Accessibility to test users | Can affected people or reproducible environments be reached? |
| Constraints & risks | Platform permissions, maintenance, security, privacy, dependencies and distribution barriers |
| Contradictory evidence | Cases where issue is already solved, niche, low priority or not recurring |
| Evidence quality & gaps | Confidence, missing facts, planned verification questions |
| Sources | At least one direct source URL; list all URLs with what each supports |

A problem with only one independent credible source may be logged as a **hypothesis / needs validation** but must not be called validated.

## 5. Stage 1 — User-value gate (mandatory, evaluated first)

Score **four dimensions on 0–3** using documented evidence and the detailed anchors in `Problem_Discovery_Step3_Evaluation_Rubric_Decisions.md`:

1. **Problem reality:** Credible firsthand reports and, for a score of 3, additional direct technical verification.
2. **Frequency/recurrence:** Evidenced repeated burden per user or across independent users/projects.
3. **Alternative gap:** Demonstrable limitations of available tools, built-in capabilities and workarounds in the relevant context.
4. **Meaningful benefit:** Concrete user impact and, for a score of 3, a specific outcome that could be measured.

**User access/validation is a non-scored planning field** for subsequent user interviews and reproducibility checks; it does not change Stage 1 user-value scores.

For **each dimension**, retain its score (0–3) **or** `Research needed`, a rationale, supporting Evidence IDs and relevant counterevidence/uncertainty. An unscoreable dimension must **not** be coerced to zero. A score of 0 requires credible negative evidence, not merely missing information.

**Total: 0–12, only if all four dimensions have defensible scores.** Scores are prioritization aids, not statistically validated demand probabilities:

- **10–12:** `Strong` — candidate for deeper validation.
- **7–9:** `Promising` — important potential with uncertainties to verify.
- **0–6:** `Low priority` — retain for reporting, including unusually severe, well-documented niche exceptions.
- **Any unscoreable dimension:** Overall `Research needed` — **no total or priority label**; retain partial dimension assessments and specify missing evidence.

**Gate rule:** Only fully scored `Strong`/`Promising` candidates with a clearly articulable user benefit advance to Stage 2. `Research needed` and `Low priority` cannot advance. Preserve serious but low-frequency issues for human review without silently overriding this gate.

## 6. Stage 2 — Feasibility and career-fit filter (secondary)

**Apply only after Stage 1.** Do not downgrade a valuable user problem merely because it is not AI-heavy or does not showcase both contributors equally.

Assess qualitatively (**Strong / Partial / Weak / Unknown**):
- Does the team's expertise cover the core problem sufficiently to build a reliable first version?
- Can at least one demonstrable engineering competency appear naturally: backend, agentic AI, model evaluation, observability, iOS architecture, developer tools, CI/CD, testing or integration?
- Can a small, maintainable, trustworthy open-source deliverable be released with limited resources?
- Are maintenance burden, platform restrictions, external APIs, privacy/security and operational costs manageable?
- Is there a plausible way to demonstrate user value publicly (reproduction, benchmarks, examples, docs or demo)?

**Do not require both engineers to contribute equally** or force AI/iOS into a problem. Record skill gaps honestly. Stage 2 is a filter and tie-breaker, not the first-stage objective.

## 7. Research workflow for the agent

1. **Map workflows:** For each examined category, identify common users and recurring tasks (not solution concepts).
2. **Collect complaints:** Search issues/discussions and firsthand accounts. Save direct links and context.
3. **Cluster problems:** Deduplicate reports into coherent problem statements; distinguish symptoms from underlying causes.
4. **Investigate alternatives:** Identify available tools, workarounds, unresolved limitations and recent fixes.
5. **Triangulate:** Look for independent corroboration and disconfirming reports; record evidence gaps.
6. **Apply Stage 1:** Score user value with reasoned evidence; label strong, promising, low priority, or needs research.
7. **Apply Stage 2 selectively:** Assess team fit only for Stage-1 candidates; avoid solution ideation.
8. **Produce concise report:** Present evidence and decisions with traceable sources, not long undifferentiated link dumps.

**Search queries should target pain rather than hype:** Examples include `site:github.com/<org>/<repo>/issues setup broken`, `"workaround" SwiftUI build`, `"painful" MCP configuration`, `"slow" developer workflow`, `"manual" API integration`. Vary wording; do not treat these examples as confirmed pains.

## 8. Report format (mandatory)

### A. Executive summary (maximum 1 page)
- Research scope, date, source coverage, and limitations.
- 3–5 highest-confidence **problem observations**, not project pitches.
- Key patterns across categories and surprising disconfirming findings.
- Clear list of what remains unverified.

### B. Problem landscape by category
For each category **actually examined**: number of distinct candidate problems, common user groups, recurring pains, main alternatives, and direct evidence links. Identify deferred categories and coverage limits explicitly; the initial pilot covers Developer Tools & Productivity only.

### C. Comparison table (ranked primarily by Stage 1)
| ID | Problem (solution-neutral) | User | Evidence (independent reports) | Impact | Alternatives gap | User-value score /12 (or Research needed) | Confidence | Stage 2 fit | Next validation |

### D. Problem cards (for shortlisted candidates)
Use a consistent compact structure:
- **ID & problem statement**
- **Who / when / why it hurts**
- **Evidence:** 2–4 direct links, dates, what exactly they establish
- **What users do now:** alternatives and limitations
- **Potential measurable outcome:** without proposing a product
- **User-value assessment:** four sub-scores (or dimension-level `Research needed`), rationales, linked evidence, and a total /12 only when all four can be scored
- **Counterevidence / uncertainty**
- **Technical & career fit:** only if it passes Stage 1
- **Next validation step:** precise question, test, or user interview target

### E. Rejected and inconclusive observations
Explain why a reported pain was ruled out, is already solved, appears too isolated, or needs better evidence. Include at least a few counterexamples to reduce confirmation bias.

### F. Source appendix
Direct URLs, source types, dates (where known), access date, and claims supported. Clearly mark unavailable or unverifiable information.

## 9. Quality checklist / stopping rules

Before submitting:
- [ ] No project ideas, implementation specifications or names offered in this phase.
- [ ] Problems are stated without embedding a proposed solution.
- [ ] Each shortlisted claim has direct source links; no fake metrics or inferred statistics reported as facts.
- [ ] Independent corroboration vs repeated reports by one author is distinguished.
- [ ] Recent fixes, opposing evidence and existing solutions were checked.
- [ ] Scores are explained rather than presented as objective probabilities.
- [ ] User Value was applied **before** Career Fit.
- [ ] Stars and trendy technologies did not determine ranking.
- [ ] Findings are grouped across categories examined; deferred categories and unresolved questions are explicit.
- [ ] A reviewer can retrace how each shortlisted problem made the shortlist.

**Definition of done for this phase:** A grounded, comparable shortlist of **problems worth validating**, including links, alternative analysis, uncertainty and next validation tests. **Not** a selected project or technical design.
