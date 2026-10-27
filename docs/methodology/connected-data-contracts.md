# Connected Market, Provider and Financial Contracts — v0.2 PR 1

> **Implementation:** provider-neutral contracts only. **No current/live prices, provider adapters, cache, hosted API, or online research UX are implemented in this PR.**  
> **Architecture decision:** [ADR 0004](../decisions/0004-provider-neutral-data-contracts.md).  
> **Existing source contract:** [Research Evidence Contract](evidence-contract.md).

## Identity and as-of mapping

Use `IssuerId(namespace, value)` for the legal/reporting entity and existing `InstrumentId(ticker, venue, trading_currency)` for a listed instrument. `IssuerListing` adds a sourced, dated mapping of issuer to security/share-class representation. It is not historical symbology automatically sourced or verified.

`resolve_issuer(listings, instrument=..., on=...)` matches the full venue-qualified identity and effective date, rejecting missing/overlapping results. External adapter mapping must obtain and validate actual reporting identifiers and changes of listings.

## Market quote model

| Field | Meaning / caveat |
| --- | --- |
| `quote_id`, `source_reference` | Attributed ID and original provider/response reference; not verified market truth |
| `instrument`, `provider_symbol`, `provider` | Exchange/venue instrument, vendor symbol and attributed source |
| `kind`, `price`, `currency` | Last/bid/ask/open/close, exact positive Decimal, same trading currency. FX must be explicit |
| `event_at`, `received_at` | Time of underlying market event vs time provider result was received; timezone-aware; neither fabricated |
| `session` | `pre_market`, `regular`, `after_hours`, `closed`, `halted`, `unknown`; asserted by provider/verified adapter |
| `timeliness` | `real_time`, `delayed`, `end_of_day`, `historical` or `unknown`; provider/plan asserted, not self-certified |
| `delay_seconds` | Optional positive known delay for a delayed quote or zero for asserted real-time; never guessed |
| `adjustment` | `unadjusted`, `split_adjusted`, `total_return_adjusted`, `unknown` |
| `entitlement_scope` | Opaque scope used by future authorization/cache layers; **not a credential** |
| `rights` | Separate cache, snapshot retention and redistribution rights, default `unknown` |

### Provider labels are distinct from freshness

`assess_quote_freshness(quote, now=..., max_age=...)` returns `within_policy`, `stale`, or `unknown`. A caller must select `max_age` from provider/plan, asset class, trading session and intended purpose. With no age policy, the only valid conclusion is unknown.

Example: a 30-second-old **end-of-day** record may be `within_policy` for a 60-second check while the provider's timeliness remains `end_of_day` and the session remains `closed`. **Do not display it as live.** A one-day-old quote retrieved a second ago remains stale under a short policy.

Market calendars, quote permissions, actual market-session checks, vendor delay verification and symbol-to-security authentication are external adapters/services in later PRs.

## Financial statements and filings

`FilingReference` identifies issuer, accession, form, `filed_on` *calendar date*, retrieval time and optional separately verified public release time. The absence of `publicly_available_at` must be represented as unknown; no invented timezone/intraday value is allowed.

The seed `SEED_METRICS` catalog defines reporting *concepts*, their unit and whether they describe a duration or instant. It does not supply sector/accounting mappings. Period normalization, adjustments, original versus amended filing vintages, split basis, capex cash-flow sign, FX, issuer entity scope and comparable EPS are not implicitly resolved. Ingestion must reject ambiguous context rather than select an arbitrary provider fact.

## Provider request and failure contracts

Two independent async ports are defined in `investiq_core.ports`:
- `QuoteProvider.get_quote(QuoteRequest)` returns `MarketQuote`. A request may specify `required_timeliness`; adapters must deny if their plan cannot provide it, rather than silently return delayed data.
- `FilingProvider.list_filings(FilingRequest)` returns a bounded tuple of `FilingReference`.

`ProviderCapabilities` advertises `quotes`, `price_history`, `filings`, `fundamentals`, `estimates`, `fx`, `news` without claiming an entitlement.

`ProviderFailure` distinguishes unauthorized, entitlement denied, rate limited, timeout, temporarily unavailable, unsupported/ambiguous security, missing and invalid data. Only rate-limits, timeouts and temporary unavailability are retryable; future adapters must implement bounded retry/deadline rules and safe error reporting.

## Synthetic use example (no network)

```python
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from investiq_core.evidence import InstrumentId
from investiq_core.market import (
    MarketQuote, MarketSession, QuoteKind, QuoteTimeliness,
    assess_quote_freshness
)

event = datetime(2026, 10, 26, 15, tzinfo=UTC)
q = MarketQuote(
    quote_id="synthetic:quote1",
    instrument=InstrumentId("DEMO", "XNAS", "USD"),
    provider="FictionalFeed",
    provider_symbol="DEMO",
    source_reference="synthetic:response",
    kind=QuoteKind.LAST,
    price=Decimal("75.00"),
    currency="USD",
    event_at=event,
    received_at=event + timedelta(seconds=1),
    session=MarketSession.REGULAR,
    timeliness=QuoteTimeliness.DELAYED,
    entitlement_scope="synthetic:plan",
    delay_seconds=900,
)
assert q.timeliness == QuoteTimeliness.DELAYED
assert q.rights.allows("snapshot") is False
status = assess_quote_freshness(
    q, now=event + timedelta(seconds=5), max_age=timedelta(seconds=10)
)
assert status.value == "within_policy"  # NOT a live-data label!
```

All names/prices here are **entirely synthetic**.

## Acceptance and deferred work

The PR 1 contract suite uses no external network, credentials or vendor datasets. Tests cover exact price/currency, source rights, delayed vs EOD semantics, stale retrieved-but-old quotes, issuer ambiguity/effective dates, fiscal concept types, date-only filings, request validation and transient versus denied provider errors.

**Still not built:** provider APIs and permission enforcement, provider normalization, CIK lookup, license verification, market session calendar, cache TTL policy, web/CLI current research view, storage, data-quality reconciliation and report generation. Implement these in v0.2 PR 2 onward under [Roadmap v2.0](../product/product-roadmap.md).
