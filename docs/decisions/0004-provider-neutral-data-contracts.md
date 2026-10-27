# ADR 0004 — Provider-neutral financial market contracts before integrations

**Status:** Accepted for InvestIQ v0.2 PR 1 (2026-10-27).  
**Implements:** [Product Roadmap v2.0](../product/product-roadmap.md) and [ADR 0003](0003-connected-data-and-research-history.md).  
**Scope:** typed library contracts and synthetic tests only. No provider, exchange data, server, shared cache or real quote is delivered by this decision.

## Problem

v0.1.1 provides source-aware `FinancialObservation`, `InstrumentId` and thesis-history contracts, but no issuer-to-listing mapping, market-quote time/price/delay semantics, rights/entitlement metadata or provider failure interface. Integrating a source directly into valuation calculations would conceal stale/delayed data and create lock-in.

## Decision

### 1. Keep identities separate

`IssuerId(namespace, value)` identifies a reporting entity; `InstrumentId(ticker, venue, trading_currency)` remains a *traded instrument*. `IssuerListing` maps them with inclusive effective date range, source reference and verification time. `resolve_issuer` fails on missing or overlapping mappings: ticker-only joins are prohibited.

An identifier is a user/provider assertion, not verified registry truth. Adapter onboarding later must authenticate and normalize CIK/LEI/other schemes.

### 2. Preserve exact quote semantics

`MarketQuote` is an immutable positive finite Decimal amount tied to its listing currency, quote type (last/bid/ask/open/close), price adjustment basis, provider/source ID and provider symbol.

An event/market timestamp and actual receipt timestamp are distinct timezone-aware values. The quote carries source-declared market session, entitlements, asserted timeliness (`real_time`, `delayed`, `end_of_day`, `historical`, `unknown`) and delay in seconds *only when meaningful and supplied*. Source classification is not independently proven by the struct.

`assess_quote_freshness(quote, now, max_age)` evaluates a caller-selected policy against event time. It returns `unknown` without a policy, and never upgrades EOD/delayed/unknown source classification to real-time. Even a within-policy quote could be from a closed market. No universal TTL or stock-exchange-hours assumptions.

### 3. Data reuse fails closed

`MarketDataRights(cache, snapshot, redistribute)` defaults each to `unknown`, not granted. An adapter must supply actual permission under the relevant contract; a permission to fetch a quote is **not** permission to cache it, retain it in a user's research snapshot or publicly redistribute it.

Source/license/entitlement scope is preserved as a record attribute. Rights are enforced by future application/cache layers; these value objects do not constitute a license or enforce access to an API.

### 4. Use stable, narrow provider ports

`QuoteProvider` and `FilingProvider` are small asynchronous `Protocol` boundaries; requests include venue-qualified identity and optional stricter timeliness. `ProviderCapabilities` advertises what a provider can serve but does **not** guarantee a user's subscription enables it. A provider must deny a timeliness request if it cannot honor it.

`ProviderFailureCode` distinguishes access-denied, entitlement-denied, rate-limit, timeout, temporary outage, missing data, unsupported/ambiguous instrument and invalid source response. Retryability is derived only from transient categories. Raw credentials/URLs must never be included in public error text.

No concrete provider or networking dependency is added in PR 1.

### 5. Filing and metric semantics start narrow

`FilingReference` preserves issuer, accession, form and source with a date-only `filed_on`. The verified `publicly_available_at` remains optional and distinct; a filing *date* cannot be converted into a fabricated intraday release timestamp.

`MetricDefinition` seeds financial reporting concepts with units and instant/duration distinctions (revenue, earnings, diluted EPS, cash flow, capex, cash/debt and share count). A catalog does **not** mean that raw vendor/XBRL tags are comparable or auto-normalized. Mapping must prove issuer, period, accounting scope, sign, share class, currency and restatement basis before any derived valuation.

## Alternatives rejected

- **Vendor SDK types as domain objects:** hidden vendor dependency and poor portability.
- **Single universal `FinancialObservation` for trades and statements:** conflates market event and fiscal/publication semantics.
- **Guess fresh from response receipt:** inaccurate for old/EOD/delayed quotes.
- **Assume fetched data can be cached/shared:** legally unsafe.
- **Build a cloud cache, SQLite company master or frontend before contract tests:** unnecessary speculative architecture.
- **Choose global market hours or expiry duration:** venue/plan-specific and frequently wrong.

## Consequences

This PR introduces `market.py`, `fundamentals.py`, `ports.py`, deterministic contract tests and methodological documentation while preserving the v0.1.1 exported API/bundle schema.

**PR 2** must select lawful provider(s), implement adapters honoring quote and filing contracts, document fair-access and licensing, and test negative cases with no real credentials in standard CI. Contract classes are not financial-data verification or runtime entitlement enforcement on their own.

Static typing direction: choose **mypy** for an incremental future CI baseline, starting with market/provider modules; this ADR does not claim that mypy already runs or is a PR 1 gate.
