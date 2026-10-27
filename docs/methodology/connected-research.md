# Connected current company research — v0.2 PR 4

> **Available via Python (opt-in):** SEC Companyfacts annual GAAP observations, provider-sourced Twelve Data quote, separate quote freshness and cautious annual P/E/scenarios. **Not yet shipped:** a public web UI, research-save/replay workflow, automatic issuer/share-class resolution, historical backtesting, or a full company fundamentals dashboard.

For rationale and limits see [ADR 0007](../decisions/0007-connected-research-analysis.md), [provider adapters](provider-adapters.md), and [connected data service](connected-data-service.md).

## Example (no automatic request)

```python
import asyncio
import os
from datetime import UTC, date, datetime, timedelta
from investiq_core.adapters.sec_companyfacts import SecCompanyFactsProvider
from investiq_core.adapters.sec_edgar import SecEdgarFilingProvider
from investiq_core.adapters.twelve_data import TwelveDataQuoteProvider
from investiq_core.application.connected_data import ConnectedDataService
from investiq_core.application.connected_research import (
    CompanyResearchRequest, ConnectedResearchService
)
from investiq_core.evidence import InstrumentId
from investiq_core.market import IssuerId, IssuerListing

async def main():
    clock = lambda: datetime.now(UTC)
    sec_contact = os.environ["INVESTIQ_SEC_USER_AGENT"]
    data = ConnectedDataService(
        quote_provider=TwelveDataQuoteProvider(api_key=os.environ["TWELVE_DATA_API_KEY"]),
        filing_provider=SecEdgarFilingProvider(user_agent=sec_contact),
        principal_scope="single-local-researcher",
    )
    research = ConnectedResearchService(
        data=data, fundamentals=SecCompanyFactsProvider(user_agent=sec_contact)
    )
    # An issuer/listing relation must be independently verified and sourced.
    listing = IssuerListing(
        issuer=IssuerId("SEC_CIK", "320193"),
        instrument=InstrumentId("AAPL", "XNAS", "USD"),
        effective_from=date(2020, 1, 1),
        source_reference="your-verified-issuer-listing-reference",
        verified_at=clock(),
    )
    result = await research.analyze(
        CompanyResearchRequest(listing=listing, max_quote_age=timedelta(minutes=30))
    )
    print(result.quote.quote.price, result.quote.freshness.value)
    print([(f.metric, f.value, f.period_end, f.accession) for f in result.annual_facts])
    print(result.annual_pe_proxy, result.warnings)  # None until share basis is verified

# Call explicitly, only with a real SEC contact and your entitled market-data key:
# asyncio.run(main())
```

**Annual reported P/E opt-in:** Only after independently checking the fiscal diluted EPS belongs to the traded share class, quotation currency and split-adjustment convention should an analyst set `analyst_confirmed_share_basis=True` and provide an explicit nonempty `share_basis_rationale`. The code does not independently prove that assertion. It also requires positive EPS, a correctly dated quote after the filing and a sufficiently fresh quote. This ratio is **quote price divided by last reported annual diluted EPS**, not a forward or TTM P/E.

**Optional scenarios:** Supply `scenario_years` and a tuple of `ValuationScenario` with growth, terminal multiples and subjective weights. These calculations use the existing deterministic engine, are approximate price-only conditional scenarios, and are withheld when reported inputs are unsuitable. There are no prepopulated growth assumptions or buy/sell ratings.

**Source limits:** SEC Companyfacts observations are annual US-GAAP 10-K/10-K/A facts under selected tags. Missing or conflicting concepts remain missing. Filing dates are calendar dates without verified intraday public availability; the current adapter deliberately excludes same-day filings. The latest revised vintage is **not** a historically replayable snapshot. A price quote's `timeliness=UNKNOWN` and `rights.cache/snapshot=UNKNOWN` do not change merely because it was successfully fetched. Current analysis performs no automatic persistence or redistribution.

**Network and CI:** imports and tests do not issue web requests. Live access is opt-in and subject to SEC fair access and Twelve Data plan/exchange terms. Tests use synthetic in-memory XBRL and market data. The SEC adapter allows up to 8 MB per Companyfacts response while other provider defaults remain bounded.
