# Optional Connected Provider Adapters — v0.2 PR 2

**Implemented:** SEC recent filing metadata and Twelve Data's minute-candle quote `close`, using existing async provider ports. **Not implemented:** current-company research/valuation workflow, historical price storage, financial XBRL normalization, quote caching, web/UI, public SaaS or real-time entitlement validation.

See [ADR 0005](../decisions/0005-provider-selection.md) for source comparison, licensing decisions and limitations.

## Requirements

- Python 3.11+; no additional required Python package or network service.
- **SEC:** operator supplies a real, contactable declaration such as `InvestIQ Research contact@example.org`; it must identify you, not a fictitious contact.
- **Twelve Data:** individual user obtains their own authorized API key and entitlement. Check [current provider plan and coverage](https://twelvedata.com/pricing) and [Terms of Use](https://twelvedata.com/terms). Never put a real key into the repository.
- External network access is **opt-in** by calling the adapters. Installing/importing the package or running ordinary tests does not send network requests.

## SEC EDGAR — filing listing

```python
import asyncio
from investiq_core.adapters.sec_edgar import SecEdgarFilingProvider
from investiq_core.market import IssuerId
from investiq_core.ports import FilingRequest

async def main():
    provider = SecEdgarFilingProvider(
        user_agent="My Research Project your-real-contact@example.org"
    )
    filings = await provider.list_filings(
        FilingRequest(IssuerId("SEC_CIK", "320193"), limit=5)
    )
    for filing in filings:
        print(filing.accession, filing.form, filing.filed_on, filing.publicly_available_at)

# Intentionally NOT called automatically:
# asyncio.run(main())
```

SEC endpoints use ten-digit zero-padded CIKs in the URL. The adapter verifies the response CIK. It returns only the `recent` part of the submissions feed and a requested number of records (up to 100); older archives are not paginated. Filing dates are retained as dates and `publicly_available_at` stays `None`. Data may change throughout the day. Default per-instance request pacing is one per second; hosted/multi-process systems need shared throttling as well. See [SEC API](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) and [fair access](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data).

## Twelve Data — BYOK price observation

```python
import asyncio
import os
from investiq_core.adapters.twelve_data import TwelveDataQuoteProvider
from investiq_core.evidence import InstrumentId
from investiq_core.market import QuoteKind
from investiq_core.ports import QuoteRequest

async def main():
    provider = TwelveDataQuoteProvider(api_key=os.environ["TWELVE_DATA_API_KEY"])
    # Replace ticker/venue/currency with a security covered by YOUR plan.
    quote = await provider.get_quote(
        QuoteRequest(InstrumentId("AAPL", "XNAS", "USD"), kind=QuoteKind.CLOSE)
    )
    print(
        quote.price, quote.currency, quote.event_at,
        quote.timeliness.value, quote.rights.snapshot.value
    )

# Run explicitly after setting a licensed personal API key:
# asyncio.run(main())
```

**Important constraints:**
- Only the `QuoteKind.CLOSE` request is supported. It represents the `/quote` latest **minute-candle** `close`, timestamped by `last_quote_at`. **Not** a verified tick-level last trade. Requesting a historic `as_of` price or `QuoteKind.LAST` fails explicitly.
- The returned symbol, `mic_code` and trading currency must match the requested venue-qualified `InstrumentId`; no automatic symbology fallback or currency conversion.
- Timeliness is deliberately `UNKNOWN`. Even if the provider advertises real-time access, no API response alone certifies this user's market/exchange entitlement. A `required_timeliness=REAL_TIME` request is denied rather than mislabeled.
- `is_market_open=false` marks a provider-reported closed session; a true value does not prove regular-session data, and does not make the data fresh.
- Market-data reuse rights default to `UNKNOWN`. **Do not cache, retain quote values in private snapshots, redistribute them or host public displays without the applicable license**. The adapter does none of these actions.
- The BYOK key is transmitted to Twelve Data in the provider-required HTTPS query parameter. The transport disables redirects and strips provider messages, URLs and query strings from exposed errors. Users must still safeguard environment variables and credentials in their own runtime.

## Failure behavior

Both adapters return `ProviderFailure` for HTTP/vendor data failures, using stable `code` values: `unauthorized`, `entitlement_denied`, `rate_limited`, `timeout`, `temporarily_unavailable`, `unsupported_instrument`, `unsupported_request`, `missing_data` and `invalid_response`.

No automatic retries or hidden quote fallback happen in PR 2. Retryable categories are only advisory for the future bounded retry policy. No real-network test runs in standard CI.

## Developer tests

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest -q
python -m build --sdist --wheel
investiq demo --output demo.json
investiq validate demo.json --basis recorded
```

Provider integration tests use fake HTTP responses with synthetic company IDs and quote values; **no live credentials are necessary**. PR 3 will coordinate providers with source-aware freshness and opt-in permitted caches.
