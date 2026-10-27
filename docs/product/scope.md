# InvestIQ — Product Scope and User Journey

> **Proposed alignment:** [Product Strategy & Roadmap v3.0 through v1.0](product-roadmap.md) · **Date:** 2026-10-27
> **Research basis:** [Existing investment research requirements](research-foundations.md)
> **Current code:** v0.2.0 source release candidate; connected API rights/provider smoke and public tag approval remain separate gates.

## Mission

Create an **AI-first, open-source, local-first equity investment research workspace** that the original researcher actually uses, then make it usable by anyone with an authorized provider/model configuration within supported coverage. Its primary job is to **discover and evaluate companies, compare meaningful peers, underwrite valuation and entry conditions, document a falsifiable investment thesis, and revisit new evidence** with far less manual prompting and spreadsheet reconciliation.

**AI coordinates research; sourced tools retrieve market/filing facts; deterministic functions calculate; the investor decides.** This is neither a generic chatbot nor an automated stock adviser/brokerage.

## User and release strategy

1. **v0.3 personal first:** usable local task UI, guided provider/model setup or no-key synthetic demo, integrated sourced research, specific bear case and explicit private thesis save for a limited supported US-accounting universe.
2. **v0.4–v0.6 analytical depth:** company economics, financial trends/peers, research universes and explainable scores, transparent return-hurdle/entry sensitivity.
3. **v0.7–v0.8 personal continuity:** opt-in watchlists, material changes, versioned research, optional private portfolio concentration/risks and multi-currency when supported.
4. **v0.9–v1.0 external ready:** independently installable and usable open-source product, documented supported markets/providers, safely replaceable personal context, scenario/workspace export, stable contracts and actual external tests.

The repository is already public and MIT-licensed. **External-use readiness is a usability/quality achievement, not a business-model conversion or postponement of open source.**

## Actual v0.2 source release candidate

Implemented: portable Python research/valuation/evidence primitives; five *instruction-only* AI skill files; synthetic offline CLI; SEC US-GAAP annual Companyfacts plus Twelve Data BYOK minute-candle quote; issuer listing/rights/freshness contracts; limited sourced analysis; user-triggered, rights-aware private immutable snapshots/replay.

Not implemented: AI/LLM runtime, local/browser task UI, stock lookup wizard, company/peer full financial trends, research universes/rankings, DCF/entry threshold engine, alerts, portfolios, model claim-to-source semantic evaluation or multiuser hosted service. Provider-plan timeliness and ability to retain quotes remain UNKNOWN without independent rights confirmation.

## Non-negotiable boundaries

- Provider API is the present-price/facts source, with explicit timestamps, delay/session, fiscal periods, currency, share class, changes and gaps. Local research history is **not** a static current data feed.
- Save research and any user positions only with explicit informed permission and lawful input retention; omit restricted quote-derived results from offline replay.
- Open-source core/app must work locally without a centralized InvestIQ account; authentic provider/model access **may require BYOK, payment or a validated local alternative**, always disclosed. No-key demo uses only synthetic data.
- Personal holdings, account credentials, prior workbook prices or subjective stock-buy recommendations are never embedded in public fixtures or defaults.
- No guarantee of global data coverage, investment gains, stock-selection accuracy, personalized trade instructions, trade execution, brokerage account management or licensed hosted redistribution.

See the [full roadmap](product-roadmap.md) for releases and v1.0 exit checklist, the [v0.3 PRD](ai-research-experience.md), and [validation plan](validation-plan.md).
