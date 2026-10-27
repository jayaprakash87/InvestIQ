# ADR 0007 — Current SEC annual facts and price-linked analysis

**Status:** Accepted for v0.2 PR 4 · 2026-10-27  
**Depends on:** [ADR 0004](0004-provider-neutral-data-contracts.md), [ADR 0005](0005-provider-selection.md), [ADR 0006](0006-connected-data-service.md).

## Decision and scope

Add a narrowly qualified **current-company analysis** path without pretending that SEC filing references alone are financial statements. Extend the provider-neutral data contract with immutable `AnnualMetricFact` records, an `AnnualMetricsRequest`, and `FundamentalsProvider`. Implement an opt-in `SecCompanyFactsProvider` using SEC's official `/api/xbrl/companyfacts/CIK##########.json` endpoint and the same contact User-Agent/per-instance pacing as the existing EDGAR adapter.

Deliver `ConnectedResearchService.analyze` as a transient, source-linked company view: requested venue-specific quote, provider-declared timeliness, separately computed freshness, latest supported annual facts, data-quality warnings, an optional **reported annual P/E proxy**, and optional user-defined EPS scenarios through the existing deterministic valuation engine.

This is **not** a TTM or forward P/E model, an analyst consensus feed, an enterprise accounting normalizer, a historical backtest or a persistent research snapshot.

## Financial normalization rules

1. **Entity and instrument identity:** require a sourced, effective-dated issuer-to-listing mapping; match the quote's full ticker, MIC, currency and kind. No ticker-to-CIK guesses.
2. **Exact values:** the transport parses JSON fractional numbers directly as `Decimal`, not binary float. A custom provider submitting Python floats as reported financial facts is rejected.
3. **Narrow source tags:** use curated `us-gaap` 10-K/10-K/A annual facts for diluted EPS, reported revenue, net income and operating cash flow only. These are raw reported concepts, not verified business-unit comparables or normalized free cash flow.
4. **Year basis:** duration must be 330–395 calendar days inclusive; ignore 10-Q rows, shorter year-to-date periods, missing/invalid fiscal context and unsupported XBRL units. Never sum 3-, 6- or 9-month cash-flow data to invent an annual figure.
5. **Temporal vintage:** distinguish fiscal start/end, exact SEC accession and calendar filing date. A same-day filing is **excluded** when evaluating current information because the API's date does not prove the intraday public release instant. Prefer the latest filed vintage for the latest annual fiscal period. Conflicting alternative tags with identical filing-day priority result in a missing metric, not a random selection. This is **not sufficient** for timestamp-accurate historical replay.
6. **No implicit FX or share adjustment:** reported diluted EPS and quote must be in the same currency and quote must follow the EPS filing date. Issuer-wide diluted EPS can differ from a particular security's economic share basis. Annual P/E is withheld until an analyst explicitly asserts compatible share-class and split-adjustment basis **with a rationale**.
7. **Nonpositive EPS:** do not calculate P/E or EPS-driven scenario returns when earnings are zero or negative. Missing cannot become zero.
8. **Stale quotes:** the current valuation is withheld when the quote violates the caller's age policy. Timeliness UNKNOWN (as in Twelve Data) is preserved and shown as a warning; a fresh retrieval cannot relabel it real-time.
9. **Scenario assumptions:** no scenario probabilities, growth or terminal multiples are invented. If the caller supplies all of them and the valuation is eligible, delegate to the existing `evaluate_scenarios` function and clearly label subjective, price-only, approximate calculations. The annual reported EPS anchor is **not** a forward earnings forecast.
10. **Source and reuse rights:** preserve quote and annual fact provenance in the transient output. The current Twelve Data source does not grant caching or snapshot retention; the analysis does not automatically save or export a provider price.

## Architecture and operational controls

The `SecCompanyFactsProvider` is a small optional adapter, not a mandatory service. SEC Companyfacts can exceed the default 2-MB limit of other provider responses; cap this specific request at **8 MB**. It shares the SEC 1-request-per-second *per-instance* pacing logic but does not claim shared-IP global quota enforcement. Transport and parser tests use synthetic fixture data without external network or real market data.

The application composes the `ConnectedDataService` and `FundamentalsProvider`. No framework, cloud database, background processing or cache for financial XBRL data is added. A user may refresh the **current** price-sensitive analysis without overwriting any thesis history.

## Alternatives rejected

- Treat SEC submissions lists as full reported numbers.
- Select the latest raw XBRL `val` without fiscal period, taxonomy, accession, form or unit checks.
- Calculate a forward or TTM multiple from one SEC annual EPS observation.
- Infer ticker/CIK and share class from matching company names.
- Accept mismatched currency/negative EPS or hide quote age.
- Auto-generate rankings, upside targets or scenario probabilities.
- Save current licensed market observations as thesis history before vendor retention rights and PR 5 storage.

## Acceptance, limitations and next step

Deterministic tests cover exact Decimal parsing, foreign issuer/CIK rejection, fiscal-year validation, same-day disclosure exclusion, conflicting-revenue ambiguity, missing/negative EPS, FX, stale quote, expired listing, unverified share basis, user-supplied scenarios and price-driven refresh.

**Current restrictions:** SEC US-GAAP annual 10-K facts only, no general 20-F/IFRS support, no quarter/TTM rollup, no vendor-verified EPS share-class compatibility, no authentic quote-adjustment guarantee, and no verified official release *time* in the financial fact feed. Even a supported company can return missing data or no valuation. No live entitlement claim or premium feed redistribution is implied.

**Next:** v0.2 PR 5 defines private, explicit save/replay and legally retainable evidence manifests; until then this result is a transient connected view.

Official sources: [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces), [SEC fair access](https://www.sec.gov/about/webmaster-frequently-asked-questions).
