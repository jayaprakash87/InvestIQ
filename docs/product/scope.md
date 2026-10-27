# InvestIQ Product Scope

> **Released:** v0.1.1 open-source, offline synthetic research toolkit.  
> **Approved planned next release:** **v0.2 — Connected Company Research.** The v0.2 capabilities below are **not yet implemented**. See [canonical product roadmap v2.0](product-roadmap.md).

## Mission

Offer connected, source-aware equity research that **refreshes data with truthful timestamps** yet **preserves reproducible decisions**. Make it usable as an open-source library/CLI and optionally self-hosted or delivered through appropriately licensed managed services.

## Intended users

Independent investment researchers, educators, analysts and developers. No private investment profile, brokerage account or managed investment service is necessary.

## What v0.1.1 does today

Offline deterministic valuation calculations; precision-aware financial observations and source dates; structurally checked research outputs; five portable AI research skills; linked thesis history; installable CLI generating and validating a fictional research bundle; release build/tests and open-source governance.

**It does not ingest current real company financials or quotes.** The offline demo is explicitly fictional.

## v0.2 implemented user journey

1. Choose a supported instrument/issuer with verified identity, venue, share class and currency.
2. Request the latest permitted provider quotation and available financial statements; display actual timestamps, source and real-time/delayed/EOD/unknown classification, not invented freshness.
3. Reconcile source metadata, units, fiscal periods, amendments and entitlement into normalized evidence with clear gaps/errors.
4. Calculate a traceable research view from supported metrics; refresh price-dependent outputs when legitimate newer quotes arrive, without changing saved theses.
5. Explicitly save a dated research snapshot with legally retainable inputs and a versioned research rationale.
6. Replay the snapshot from its stored evidence/reference, offline when retention rights allow. Never substitute today's prices during historical replay.

## v0.2 minimum deliverables and caveats

Provider-agnostic data and entitlement contract; one permitted market-price provider adapter and one valid filing/fundamental adapter (e.g. SEC filings for US issuers), time-aware refresh and safe bounded cache, a source-linked connected research view, a user-triggered snapshot storage adapter and an end-to-end documented CLI demonstration with real supported source data.

**A cloud deployment is optional.** Start with direct API access and an in-process cache/BYOK. Shared cloud cache and managed durable research storage become optional deployment adapters only after terms, measured operational need and security are understood.

## v0.2 deliberately out of scope

Global guaranteed real-time quotes, large historical market data store, streaming warehouse, stock trades, fund management, brokerage synchronization, automatic buy/sell advice, AI-fabricated fundamentals, multi-tenant hosted SaaS, subscriptions and predictive accuracy claims.

## Acceptance

A real-company example must report its original provider, permitted delay/session metadata and financial source; stale quotes must not appear live; a user must be able to refresh price-sensitive analysis without rewriting an old thesis and subsequently replay a lawfully saved decision. Provider failure, missing data, rate limits, symbol/FX mismatch, source-revision errors and entitlement-denied behavior must be covered by tests. The published package, CLI, docs, privacy and data-use rights must remain sound.

For the order of six outcome PRs, constraints on usage rights, provider evaluation and later v0.3–v1.0 releases, refer to the [canonical roadmap](product-roadmap.md).
