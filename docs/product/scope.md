# InvestIQ Product Scope

> **Status:** Aligned to proposed [Product Strategy & Roadmap v3.0](product-roadmap.md) · **Date:** 2026-10-27
> **Current code:** v0.2.0 source release candidate; independent real-provider smoke and public release authorization remain outstanding.
> **Next product hypothesis:** v0.3 **AI Research Experience**, not another developer-first analytics release.

## Mission and intended user

Help a serious self-directed equity investor move from **question → sourced research → strongest challenge → deliberate thesis → subsequent reassessment** with substantially less manual prompting and clerical reconciliation. User-facing tools must be accessible without CLI, CIK/MIC, BYOK configuration or JSON knowledge for a supported consumer workflow. Developers retain the portable open-source Python library.

The competitive advantage is a hypothesis to **test** against a general LLM and existing investment research services, not a feature-based claim.

## What currently exists (v0.2 source)

- Portable Python domain calculations, attributed financial observations, type/rights/time contracts, reproducible synthetic offline CLI, five portable **instruction-only** AI skills and hash-linked history.
- Opt-in connected research: SEC annual US-GAAP facts and Twelve Data BYOK minute-candle CLOSE quote for explicitly verified issuer and listing; unknown plan timeliness remains unknown.
- Rights-gated private snapshots; prices without confirmed retention permission and their derivatives are not stored/replayed. No user accounts, web UI, model-powered research agent, automatic search, monitoring, portfolio or returns predictor.
- Live-provider rights/smoke are manual gates; synthetic CI is **not** provider/economic proof.

## Next intended outcome: v0.3

A nontechnical user selects a **supported** equity or asks a natural-language question; InvestIQ's **planned** model-neutral, bounded orchestrator invokes sourced tools and deterministic calculations to generate an integrated evidence-supported research answer with a specific counter-thesis, explicit information gaps, traceable source drill-down and responsive interactive experience. Follow-ups and scenarios remain grounded; saved theses are explicitly approved and source-rights-aware.

**Must prove:** low-friction task completion, source/financial reliability, usefulness versus general LLM/incumbent tools, AI privacy and cost/security guardrails. See [v0.3 PRD](ai-research-experience.md) and [validation](validation-plan.md).

## Later (conditionally validated) capabilities

- **v0.4:** opt-in investor preferences, watchlists, durable research memory, material change explanation, safe opt-in monitoring.
- **v0.5:** company discovery, trend/peer analytics, research rankings where inputs, evaluation and limitations support them.
- **v0.6+:** voluntary portfolio-context scenarios and evidence-backed quantitative experimentation only after required permissions, security and methodology.

## Out of scope / principles

No automatic trade execution, unsupported investment recommendations, guaranteed outperformance, unlicensed feed redistribution, default capture of private holdings, fabricated forecasts or silent changes to saved decisions. Current market facts come from legally permitted provider calls, not local stale copies. Historical thesis history is immutable, permissioned and separate. Actual hosting/distribution remains conditional and may be **assistant-native instead of standalone**.

Historical v0.1/v0.2 source behavior and release notes are unchanged by this scope document.
