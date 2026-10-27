# ADR 0006 — Connected data access, scoped cache and bounded retry policy

**Status:** Accepted for InvestIQ v0.2 PR 3 (2026-10-27)  
**Depends on:** [ADR 0003](0003-connected-data-and-research-history.md), [ADR 0004](0004-provider-neutral-data-contracts.md), [ADR 0005](0005-provider-selection.md), [Engineering Blueprint](../engineering/engineering-blueprint.md).

## Decision

Implement `ConnectedDataService` as a provider-neutral **single-principal, on-demand application use case**. It composes existing `QuoteProvider` and `FilingProvider` protocols, validating normalized responses before returning them. It is **not** a company-research valuation engine, background streaming worker, SaaS backend or entitlement-verification authority.

### Current quote access

- Validate the request's venue-qualified security, quote kind, data capability, required timeliness and the provider identity on response. A provider cannot silently substitute a different venue, currency, kind or weaker time classification.
- Preserve `MarketQuote` source ID, original event/receipt timestamps, market session, rights and asserted timeliness. Derive `QuoteFreshness` **separately** using a caller-provided `max_age`. Missing policy yields `unknown`, never `live`.
- A stale quote obtained from a provider can be returned **explicitly marked STALE** so consumers see the source's actual state; it must not be cached or silently relabeled.
- A quote with an impossible future receipt relative to the caller's clock is rejected as invalid source data; UTC comparisons from ADR 0004 remain authoritative.
- No implicit quote conversion, corporate-action adjustment, price fallback, hidden snapshot, AI recommendation or automatic market refresh.

### Quote caching: permission first

- Ship a small bounded in-process `BoundedQuoteCache` with LRU eviction and per-entry TTL. It is optional for a given query; the service uses it only with an explicit positive source `MarketDataRights.cache`, known positive freshness policy, source age within that policy and valid quote/account identity.
- Keep the cache private to one `ConnectedDataService` and a single principal/provider account. Caller must bind an internal principal scope, and the quote's **provider entitlement scope** is included in the cache key. A key additionally includes the provider instance and complete typed request (venue-qualified instrument, kind, required timeliness and `as_of`).
- `QuoteCachePort` provides a narrow **interface** for a future shared cache, not an implementation, license grant or proof of multi-tenant isolation. Hosted implementations must derive principal and entitlement scopes from authenticated identity, verify grants on every applicable access, and coordinate revocation.
- Cache on/off, TTL, source freshness and data-license authorization are **distinct**. A recently retrieved delayed/EOD quote never becomes a real-time quote because it was a cache hit.
- Provide explicit `invalidate_quote` and `clear_cache` hooks. Changing a source key, entitlement, contract or principal requires clearing the cache. **No hosted/shared use is authorized by this simple in-process design.**
- In the initial Twelve Data adapter `MarketDataRights.cache` remains UNKNOWN. Therefore, its quotes are **never cached** by default, regardless of age or configured cache size. SEC filing metadata are not cached in PR 3; they have no independent caching-license contract.

### Bounded provider retries

- Retry only typed transient `ProviderFailure` categories (429/rate-limited, timeout, temporary provider outage), with configurable maximum 1–3 attempts, bounded exponential backoff and injected sleeper for deterministic tests.
- Honor provider `Retry-After` **as a minimum**. If the requested delay exceeds the allowed wait budget, surface the provider failure rather than retry too early.
- Never retry authorization/entitlement denials, unsupported instruments, invalid data, missing facts, ambiguous identity or quote semantics.
- Transport deadlines and SEC per-instance request pacing remain under provider adapters from PR 2. PR 3 does not introduce background polling or globally coordinated rate limiting.

### Filing listing

- Fetch filing references on demand and validate issuer identity and bounded response count. No attempt to infer a precise public availability time from a date-only SEC record.
- Do **not** make a financial-statement claim from this listing. Actual XBRL fact normalization, period reconciliation, arithmetic and provenance belong to PR 4 and later.
- No filing cache, public dataset replication, snapshot retention or redistribution is introduced.

## Alternatives

- **Cache every HTTP result:** rejected; vendor/exchange licenses and source freshness prohibit assumptions.
- **Use Redis/cloud service immediately:** rejected; no demonstrated scale or authenticated tenancy.
- **Retry indefinitely on rate limits:** rejected; harms provider fair access and can amplify outage costs.
- **Silent stale fallback:** rejected; invalidates investment-research provenance.
- **Single method to retrieve and value a company:** deferred; PR 4 needs actual normalized financial facts before valuation can be genuine.
- **Global provider failover:** rejected; incompatible market delay/session/adjustment and licensing semantics cannot be swapped silently.

## Consequences and release gates

Positive: robust on-demand connected source operations; a safe cache interface for legitimately cacheable synthetic/future feeds; real vendor quotes remain legally conservative. Tests cover rights, TTL, source staleness, isolation keys, LRU, invalidation, retry limits and filing cross-issuer validation.

Limitations: cache scope assumes a **single-principal client** and is not an authorization boundary for shared service users. Full entitlement revocation, credential change signals, authenticated shared cache, filings pagination, financial XBRL normalization and a research dashboard are not delivered. An in-process lock serializes a service instance's quote retrieval, favoring simplicity over parallel throughput; revisit with measured bottlenecks. No production provider performance or licensing rights were verified using live keys.

**Next outcome:** v0.2 PR 4 — current company analysis with qualified reported fundamentals, time-aligned prices and human-readable data-quality limitations.
