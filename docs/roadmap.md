# InvestIQ — Roadmap Summary

> **Status:** Proposed [Product Roadmap v3.0 through v1.0](product/product-roadmap.md) (2026-10-27); not automatically approved or merged. [ADR 0009](decisions/0009-ai-first-product-pivot.md) records the change.

**Purpose:** Build a **general-purpose, AI-first, open-source, local-first investment research system**, proven initially with individual equity research and then expanded to independent users. Its scope does not privilege any stock, industry, thematic universe or personal research history. Preserve the tested financial Python core and strict source/freshness/rights rules. Never assume an InvestIQ cloud account or worldwide real-time data coverage is necessary.

**Product capability foundation:** source-connected research, business/financial analysis, comparisons, explainable screening/scoring, scenario underwriting, research continuity, opt-in portfolio context and source/data/model governance.

| Release | Status / user outcome |
| --- | --- |
| **v0.1.1** | Released offline synthetic research toolkit |
| **v0.2.0** | Source release candidate: BYOK SEC + Twelve Data connected CLI and lawful private snapshots/replay; pending live-provider/manual release gates |
| **v0.3 — NEXT** | **Personal AI Research Desk:** local UI, simple company selection, guided provider/model connection, one complete sourced AI company-analysis and bear-case workflow |
| **v0.4** | Business, fundamentals and economically valid peer comparisons |
| **v0.5** | Sector/value-chain research universes, trend, explainable configurable factors and coverage-aware rankings |
| **v0.6** | Bear/base/bull underwriting, reverse valuation, hypothetical hurdle return/entry conditions |
| **v0.7** | Opt-in watchlists, thesis history and source/assumption change review/monitoring |
| **v0.8** | Private optional portfolio context, thematic allocation overlaps and risk scenarios |
| **v0.9** | Installable, testable, documented external open-source beta; reliable guided onboarding |
| **v1.0** | Stable open-source equity research workspace: complete supported research-to-decision-to-reassessment journey |

**Milestone policy:** Each stage must be usable for its **own** end-to-end task; later functionality is conditional on personal/independent validation and lawful providers. Source-rights integrity, deterministic finance, model grounding, privacy and stable history are hard gates. No stock-return guarantees, trading bot, paid-hosting requirement or compulsory portfolio import.

[Read the detailed release gates](product/product-roadmap.md#6-roadmap-to-v10--progressive-independently-usable-releases) · [v0.3 PRD](product/ai-research-experience.md) · [personal and independent-user test plan](product/validation-plan.md) · [engineering requirements](engineering/engineering-blueprint.md)
