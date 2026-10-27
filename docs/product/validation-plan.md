# InvestIQ — Product Validation and Distribution Decision

> **Status:** Proposed research protocol · **Date:** 2026-10-27 · **No tests conducted or outcomes claimed.**
> See [Roadmap v3.0](product-roadmap.md) and [v0.3 PRD](ai-research-experience.md).

## Decision to make

Is the incremental value of InvestIQ's **research → challenge → explicit decision → eventual reassessment** greater than asking a general-purpose LLM or using an existing research tool? Does that value justify a standalone application, or should InvestIQ distribute primarily as an assistant-native integration/toolkit?

## Competing prototypes

- **A: Standalone task UI** — one natural-language question, bounded research orchestration, evidence drawer and scenario controls. May start with synthetic data strictly labeled as prototype; never market it as a live-data product.
- **B: Assistant/skill/MCP tool integration** — same evidence, source, valuation and privacy contracts delivered in an existing conversational host where technically permitted.
- **C: Control** — general-purpose LLM and at least one incumbent stock research tool, under the same stated coverage, data access and time constraints.

Do **not** build A and B as complete production systems in parallel; use thin comparable prototypes first, minimize sunk cost and choose a primary channel based on results.

## Study setup

1. Recruit independent equity investors with varied research skill, including nontechnical users; record experience, workflow, research horizon and current preferred tools with consent.
2. Give the same scripted company/compare/thesis-revisit research tasks and the same known-as-of information boundaries. Counterbalance tool order to reduce learning effects.
3. Include contradictions, stale data, ambiguous symbols, missing financials, inapplicable valuations and misleading bullish narratives.
4. Capture user steps, prompts, time-to-first-useful-answer, successful task completion, uncorrected financial/source errors, perceived trust and follow-up quality.
5. Separately have reviewers assess citation-faithfulness, arithmetic, risk/contradiction quality, calibration and handling of missing evidence. Reviewers should not know the generating tool where practicable.
6. Test decision-memory/revisit usefulness on a later session or scripted changed-evidence replay (mark simulated evidence as synthetic).
7. Compare product willingness-to-switch/pay, qualitative objections, API/model/provider costs per successful result and actual rights/compliance barriers. No performance claims from unblinded anecdotes.

## Metric definitions (thresholds require observed baseline)

| Metric | Measurement |
| --- | --- |
| First-task activation | Fraction of eligible users completing an evidence-supported research task without developer/CLI setup |
| Time and friction | Median task time, manual prompts, corrections and navigation steps |
| Grounded correctness | Unsupported material claims, incorrect values/units/periods, citation-to-claim mismatches per study |
| Challenge quality | Specific, testable bear-case conditions vs generic risk boilerplate |
| Research continuity | Correctly identify source/assumption changes vs untouched historical thesis; value on revisit |
| Preference/retention | Independently reported preferred workflow, intention to return and observed follow-up use where feasible |
| Economics | Provider/data rights, model calls, inference and compute cost per successfully completed task |

**Proposed hard safety gates:** no fabricated official-looking prices/returns; no unauthorized source-data retention; no silent cross-instrument or time-travel valuation; no unapproved persistent personal context. Define comparative benefit and economics thresholds after the baseline, not retrospectively.

## Decision options

- **Proceed standalone** only if accessible UI and repeat-use benefit outperform alternatives enough to justify licensing/operations.
- **Proceed assistant-first** if existing host distribution achieves comparable value at materially lower acquisition/engineering burden.
- **Narrow niche** if only a specific company segment, technique or user category values the workflow.
- **Stop** if source coverage, quality, commercial rights or user preference fail and a plausible corrective experiment is absent.

Publish the decision record with sample sizes, task definitions, dates, limitations and adverse findings. No implied PMF, alpha or adviser authorization.
