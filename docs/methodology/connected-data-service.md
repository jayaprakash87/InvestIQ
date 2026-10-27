# Connected Data Service — v0.2 PR 3

> **Implemented:** provider-neutral on-demand quote/filing retrieval; attribution/time/identity validation; bounded retries; opt-in, rights-gated, private in-process quote caching.  
> **Not implemented:** sourced XBRL financial metric normalization, share-price valuation orchestration, saved theses, public UI, shared cloud data services, complete historical filings or streaming feeds.

Read [ADR 0006](../decisions/0006-connected-data-service.md) and [Engineering Blueprint](../engineering/engineering-blueprint.md).

## Using the service

```python
import asyncio
from datetime import timedelta
import os

from investiq_core.adapters.sec_edgar import SecEdgarFilingProvider
from investiq_core.adapters.twelve_data import TwelveDataQuoteProvider
from investiq_core.application.connected_data import ConnectedDataService
from investiq_core.evidence import InstrumentId
from investiq_core.market import IssuerId, QuoteKind
from investiq_core.ports import FilingRequest, QuoteRequest

async def main():
    service = ConnectedDataService(
        quote_provider=TwelveDataQuoteProvider(api_key=os.environ["TWELVE_DATA_API_KEY"]),
        filing_provider=SecEdgarFilingProvider(
            user_agent=os.environ["INVESTIQ_SEC_USER_AGENT"]
        ),
        principal_scope="local-single-researcher",
    )
    # Choose a listing covered by your permitted market-data subscription.
    outcome = await service.quote(
        QuoteRequest(InstrumentId("AAPL", "XNAS", "USD"), kind=QuoteKind.CLOSE),
        max_age=timedelta(minutes=30),
    )
    print(
        outcome.quote.price,
        outcome.quote.event_at.isoformat(),
        outcome.quote.timeliness.value,
        outcome.freshness.value,
        outcome.from_cache,
    )
    filings = await service.filings(FilingRequest(IssuerId("SEC_CIK", "320193"), limit=5))
    for filing in filings.filings:
        print(filing.form, filing.filed_on, filing.publicly_available_at)

# Invoke explicitly with legally obtained API credentials and a real SEC contact:
# asyncio.run(main())
```

No network call occurs at import or during package installation. The example does not run automatically.

**Quote result semantics:** `QuoteResult.quote.timeliness` describes the provider-declared feed (often UNKNOWN for Twelve Data BYOK); `QuoteResult.freshness` is **only** an age assessment under the `max_age` supplied by the caller. A quote can be within a 30-minute age policy and still be delayed or from a closed market. If the age policy is absent, freshness is UNKNOWN and no cached quote is served.

**Caching:** `BoundedQuoteCache` stores only a `MarketQuote` explicitly granting `rights.cache=ALLOWED`, with a positive `max_age` and age within policy. It never infers permission from HTTP success. Since Twelve Data returns UNKNOWN rights, its quotes cannot be cached in the current implementation. A bounded request-to-entitlement index cannot outgrow the cache, and an invalidation generation rejects in-flight responses retrieved under revoked access. It does not cache SEC filings. `clear_cache()` is required on credential/entitlement/account changes; `invalidate_quote(request)` invalidates an individual key. The optional `QuoteCachePort` is a future shared-cache interface, **not** a supported hosted authorization mechanism.

**Retries:** a retry policy has 1–3 attempts and bounded backoff. It respects HTTP 429 Retry-After delta-seconds **and HTTP-date** as a minimum and fails immediately if the delay exceeds its configured cap. Permission denials and invalid data never cause retries. The service does not silently fall back to delayed prices or alternate venues.

**Limitations:** this is a **single-principal, per-provider-account service**. A public multi-user service needs verified identity, entitlement checks, secure key management and isolated caches before deployment. A cached source value cannot be legally retained in a thesis unless it separately grants `rights.snapshot`. Filings are references, not normalized financial facts; do not claim a complete company research report yet.

## Offline validation

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest -q
python -m build --sdist --wheel
```

All new tests use synthetic provider data, clocks, permission states and sleeper fakes. No live market credentials or restricted vendor responses are necessary.
