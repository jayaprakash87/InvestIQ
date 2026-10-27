# ADR 0005 — SEC EDGAR filings and Twelve Data quote adapters for v0.2 PR 2

**Status:** Accepted for the adapter implementation (2026-10-27)  
**Depends on:** [ADR 0003](0003-connected-data-and-research-history.md), [ADR 0004](0004-provider-neutral-data-contracts.md)  
**Scope:** Optional provider adapters, configuration and deterministic offline verification. This is **not** a provider entitlement grant, a release of real-time quotes, a cache or a hosted service.

## Decision

Implement two small provider-specific adapters with no added required runtime dependencies:

1. **SEC EDGAR submissions:** `SecEdgarFilingProvider` uses `https://data.sec.gov/submissions/CIK##########.json` with a declared contact User-Agent and per-instance 1-second default request interval. It requires an explicitly known SEC CIK, validates returned CIK, and reads the `filings.recent` arrays into provider-neutral `FilingReference` instances. `filed_on` is a calendar date, **not** a verified intraday public-release time. `publicly_available_at` remains `None`. Archived filing-page pagination and XBRL financial fact normalization are excluded from PR 2.

2. **Twelve Data quotes (BYOK):** `TwelveDataQuoteProvider` calls documented `/quote` with a private, explicitly supplied key. Returns **`QuoteKind.CLOSE` only**, representing the latest minute-candle close with `last_quote_at` (minute-candle timestamp). It does not pretend that this is a tick-level last trade. It requires the response symbol, ISO MIC, and trading currency to exactly match the requested `InstrumentId`. Missing timestamp, unsupported kind, unrecognized currency, malformed price and contradictory provider identities fail closed.

### Timeliness and data rights

The endpoint description and provider plan **do not constitute per-request proof of market-data entitlement**. The adapter reports `QuoteTimeliness.UNKNOWN` with no delay duration regardless of `is_market_open`; requests explicitly requiring real-time/delayed/EOD are rejected until an entitlement-verification model exists. A successful HTTP response **cannot** upgrade UNKNOWN to REAL_TIME.

The default `MarketDataRights` remains unknown for caching, snapshot retention, and redistribution; these operations are **not automatically allowed**. An opaque BYOK scope is derived from a one-way key fingerprint for future isolation, not from the raw key and not as permission to share data. Personal key ownership does not authorize a public hosted InvestIQ feed. No adapter caches or stores quote bodies.

### Transport, resilience and source limits

- Uses a bounded `urllib` HTTPS JSON client executed off the async event loop, with a 10-second default request timeout, a 2-MB response cap, redirect refusal and sanitized failures. The transport accepts test doubles; routine tests never access the internet.
- SEC deliberately limits **one provider instance** to one request per second by default, well below the SEC's published 10-requests-per-second fair-access threshold. It **does not guarantee shared-IP or multi-instance compliance**; a future shared deployment must coordinate throttling globally.
- Requests are **single-attempt**, not hidden multi-retry loops. HTTP 401/403, 404, 429 and 5xx, timeouts, malformed responses and vendor error bodies map to typed `ProviderFailure` outcomes. Future PR 3 decides bounded retry/backoff and caching policy after measured quota requirements.
- Twelve Data places the API key in the HTTPS query string as documented by its API. Never include request URLs, provider error payloads, or credentials in public exceptions, logs, attribution references or fixtures; follow credential security policy. Provider HTTPS infrastructure necessarily receives the key.
- No automatic provider fallback. A provider error never causes a real-time quote request to silently return delayed or made-up data.

## Options evaluated

| Candidate | Fit for first open-source connected research | Decision |
| --- | --- | --- |
| SEC EDGAR submissions | Public issuer filing metadata; no key; contact User-Agent and fair-access limit required | **Implement** filing metadata adapter |
| SEC Companyfacts | Useful for fundamentals, but requires careful taxonomy/units, filing revisions and period selection | **Later** financial facts normalization, not PR 2 |
| Twelve Data | Documented quote fields incl. symbol/MIC/currency/last minute timestamp; BYOK and subscription-specific rights | **Implement** conservative `CLOSE`/unknown-timeliness adapter |
| Alpha Vantage GLOBAL_QUOTE | Default quote delivery is EOD; the documented latest trading day need not be a precise trade timestamp | Defer; cannot satisfy exact market timestamp without further contract |
| Financial Modeling Prep | Broad quote/fundamental endpoints, BYOK; plan/redistribution terms and response time semantics need separate validation | Alternative future provider; avoid unnecessary first-release vendor matrix |
| Mandatory licensed central feed | Would require hosted commercial/exchange contracts and entitlement enforcement | Reject for initial open-source adapter delivery |

## Licensing and operating requirements

- SEC: comply with declared automated User-Agent, fair access and source attribution. Do not present its availability or acceptance time as the public disclosure timestamp unless separately verified.
- Twelve Data: access must be **within user's own plan and applicable exchange terms**. Published terms restrict caching and redistribution without permission, and free-tier commercial use; some market data and external display require additional authorization. BYOK is not equivalent to redistributable data.
- Avoid storing paid provider responses in public synthetic fixtures and avoid paid data in default CI.
- Current prices may be dynamic and the market closed. Even a connected adapter does not guarantee fresh or complete research data. The UI/application service layer (PR 3/4) must show source timeliness/rights and age separately.

## Consequences and exit criteria

**Positive:** first real network-capable, entitlement-cautious adapters; public-library core remains independent, using testable `Protocol` ports and optional network transport. No cloud, server, brokerage, LLM or secrets needed to install the package.

**Limitations:** No automatic issuer-CIK resolution, SEC Companyfacts or statement normalizer, market-calendar verification, quote timeliness certification, global market completeness, historical prices, cache, research view or snapshots. A single `CLOSE` price and recent filing references **do not yet produce a complete company dossier**.

**PR 2 acceptance:** deterministic synthetic tests for SEC mapping, quote identity, precision, timestamps, key redaction, entitlement refusal, HTTP error mapping, limits, missing/invalid data, plus package/CLI regression. Documentation must distinguish verified facts from planned features and record the exact external source terms.

**Next:** PR 3 builds freshness-aware source access/normalization and bounded caching **only with explicit data rights**. A genuine user-connected company workflow and method-correct real-world calculations follow in PR 4/5.

## Primary external references

- SEC: <https://www.sec.gov/search-filings/edgar-application-programming-interfaces> and <https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data>
- SEC declared User-Agent: <https://www.sec.gov/about/webmaster-frequently-asked-questions>
- Twelve Data quote: <https://twelvedata.com/docs> (`/quote`)
- Twelve Data licensing: <https://twelvedata.com/terms> and <https://support.twelvedata.com/en/articles/5332349-commercial-and-personal-usage>
- Twelve Data current plan/credits: <https://twelvedata.com/pricing>
- Alpha Vantage alternative: <https://www.alphavantage.co/documentation/>
- FMP alternative: <https://site.financialmodelingprep.com/developer/docs/quickstart>
