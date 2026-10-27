"""Connected-data service tests: deterministic providers and clocks only."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from investiq_core.application.connected_data import (
    BoundedQuoteCache,
    ConnectedDataService,
    QuoteCacheKey,
    RetryPolicy,
)
from investiq_core.evidence import InstrumentId
from investiq_core.fundamentals import FilingReference
from investiq_core.market import (
    IssuerId,
    MarketDataRights,
    MarketQuote,
    MarketSession,
    Permission,
    QuoteFreshness,
    QuoteKind,
    QuoteTimeliness,
)
from investiq_core.ports import (
    DataCapability,
    FilingRequest,
    ProviderCapabilities,
    ProviderFailure,
    ProviderFailureCode,
    QuoteRequest,
)

INSTRUMENT = InstrumentId("DEMO", "XNAS", "USD")
ISSUER = IssuerId("SEC_CIK", "0000123456")
NOW = datetime(2026, 10, 27, 14, tzinfo=UTC)
QUOTE_REQUEST = QuoteRequest(INSTRUMENT, kind=QuoteKind.CLOSE)


def sample_quote(
    *,
    rights: MarketDataRights | None = None,
    event_at: datetime = NOW,
    received_at: datetime = NOW,
    timeliness: QuoteTimeliness = QuoteTimeliness.UNKNOWN,
    price: str = "125.50",
    scope: str = "test:plan:A",
) -> MarketQuote:
    return MarketQuote(
        quote_id="synthetic:quote",
        instrument=INSTRUMENT,
        provider="Synthetic Quote",
        provider_symbol="DEMO",
        source_reference="synthetic:minute",
        kind=QuoteKind.CLOSE,
        price=Decimal(price),
        currency="USD",
        event_at=event_at,
        received_at=received_at,
        session=MarketSession.CLOSED,
        timeliness=timeliness,
        entitlement_scope=scope,
        rights=rights if rights is not None else MarketDataRights(),
    )


def licensed() -> MarketDataRights:
    return MarketDataRights(
        cache=Permission.ALLOWED,
        snapshot=Permission.DENIED,
        redistribute=Permission.DENIED,
    )


class FakeProvider:
    capabilities = ProviderCapabilities(
        "Synthetic Quote", frozenset({DataCapability.QUOTES, DataCapability.FILINGS})
    )

    def __init__(self, quote: MarketQuote | None = None, *, failures=None, filings=None):
        self.observation = quote if quote is not None else sample_quote()
        self.failures = list(failures or [])
        self._filings = (
            tuple(filings)
            if filings is not None
            else (
                FilingReference(
                    issuer=ISSUER,
                    accession="synthetic:1",
                    form="10-K",
                    filed_on=date(2026, 10, 20),
                    source_reference="synthetic:filing",
                    retrieved_at=NOW,
                ),
            )
        )
        self.quote_calls = 0
        self.filing_calls = 0

    async def get_quote(self, request):
        self.quote_calls += 1
        if self.failures:
            fail = self.failures.pop(0)
            raise fail
        return self.observation

    async def list_filings(self, request):
        self.filing_calls += 1
        if self.failures:
            fail = self.failures.pop(0)
            raise fail
        return self._filings


class Clock:
    def __init__(self, now=NOW):
        self.now = now

    def __call__(self):
        return self.now


def service(provider, clock=None, *, cache=None, sleep=None, retry=None, principal="local"):
    return ConnectedDataService(
        quote_provider=provider,
        filing_provider=provider,
        principal_scope=principal,
        clock=clock or Clock(),
        cache=cache,
        sleep=sleep,
        retry=retry,
    )


def run(coro):
    return asyncio.run(coro)


def test_no_cache_without_explicit_vendor_grant_even_with_fresh_timestamp():
    provider = FakeProvider()
    app = service(provider)
    first = run(app.quote(QUOTE_REQUEST, max_age=timedelta(minutes=5)))
    again = run(app.quote(QUOTE_REQUEST, max_age=timedelta(minutes=5)))
    assert first.freshness == again.freshness == QuoteFreshness.WITHIN_POLICY
    assert first.quote.timeliness == QuoteTimeliness.UNKNOWN
    assert first.from_cache is False
    assert again.from_cache is False
    assert provider.quote_calls == 2
    assert app.cache_size == 0


def test_explicit_grant_allows_bounded_cache_without_granting_redistribution():
    provider = FakeProvider(sample_quote(rights=licensed()))
    app = service(provider)
    one = run(app.quote(QUOTE_REQUEST, max_age=timedelta(minutes=10)))
    two = run(app.quote(QUOTE_REQUEST, max_age=timedelta(minutes=10)))
    assert one.from_cache is False and one.attempts == 1
    assert two.from_cache is True and two.attempts == 0
    assert provider.quote_calls == 1
    assert app.cache_size == 1
    assert two.quote.rights.allows("snapshot") is False
    assert two.quote.rights.allows("redistribute") is False
    app.clear_cache()
    assert app.cache_size == 0
    assert run(app.quote(QUOTE_REQUEST, max_age=timedelta(minutes=10))).from_cache is False


def test_cached_quote_expires_at_bounded_ttl_even_if_source_age_policy_is_longer():
    clock = Clock()
    provider = FakeProvider(sample_quote(rights=licensed()))
    app = service(provider, clock, cache=BoundedQuoteCache(ttl=timedelta(seconds=10)))
    run(app.quote(QUOTE_REQUEST, max_age=timedelta(hours=1)))
    clock.now += timedelta(seconds=10)
    result = run(app.quote(QUOTE_REQUEST, max_age=timedelta(hours=1)))
    assert not result.from_cache
    assert provider.quote_calls == 2


def test_stale_market_observation_cannot_be_reused_from_a_fresh_cache():
    clock = Clock()
    provider = FakeProvider(sample_quote(rights=licensed()))
    app = service(provider, clock, cache=BoundedQuoteCache(ttl=timedelta(minutes=5)))
    one = run(app.quote(QUOTE_REQUEST, max_age=timedelta(seconds=5)))
    assert one.from_cache is False
    clock.now += timedelta(seconds=6)
    two = run(app.quote(QUOTE_REQUEST, max_age=timedelta(seconds=5)))
    assert two.freshness == QuoteFreshness.STALE
    assert not two.from_cache
    assert provider.quote_calls == 2
    assert app.cache_size == 0


def test_unbounded_or_unknown_age_policy_disables_caching():
    provider = FakeProvider(sample_quote(rights=licensed()))
    app = service(provider)
    a = run(app.quote(QUOTE_REQUEST, max_age=None))
    b = run(app.quote(QUOTE_REQUEST, max_age=None))
    assert a.freshness == b.freshness == QuoteFreshness.UNKNOWN
    assert not a.from_cache and not b.from_cache
    assert app.cache_size == 0
    with pytest.raises(ValueError, match="max_age"):
        run(app.quote(QUOTE_REQUEST, max_age=timedelta(seconds=0)))


def test_eod_or_delayed_label_is_never_upgraded_by_freshness():
    for timeliness in (QuoteTimeliness.END_OF_DAY, QuoteTimeliness.DELAYED):
        # Delay seconds is optional when unknown even if timeliness is DELAYED.
        provider = FakeProvider(sample_quote(timeliness=timeliness, rights=licensed()))
        result = run(service(provider).quote(
            QUOTE_REQUEST, max_age=timedelta(minutes=5)
        ))
        assert result.freshness == QuoteFreshness.WITHIN_POLICY
        assert result.quote.timeliness == timeliness
        assert result.quote.session == MarketSession.CLOSED


def test_cache_isolation_scopes_and_entitlement_changes():
    cache = BoundedQuoteCache(max_entries=2, ttl=timedelta(minutes=5))
    q = sample_quote(rights=licensed())
    first = QuoteCacheKey("provider-A", "alice", q.entitlement_scope, QUOTE_REQUEST)
    other_user = QuoteCacheKey("provider-A", "bob", q.entitlement_scope, QUOTE_REQUEST)
    other_entitlement = QuoteCacheKey("provider-A", "alice", "premium:other", QUOTE_REQUEST)
    other_provider = QuoteCacheKey("provider-B", "alice", q.entitlement_scope, QUOTE_REQUEST)
    cache.put(first, q, now=NOW)
    assert cache.get(first, now=NOW) == q
    assert cache.get(other_user, now=NOW) is None
    assert cache.get(other_entitlement, now=NOW) is None
    assert cache.get(other_provider, now=NOW) is None
    cache.put(other_entitlement, q, now=NOW)
    assert len(cache) == 1
    cache.invalidate(first)
    assert len(cache) == 0


def test_bounded_lru_and_reverse_clock_eviction():
    cache = BoundedQuoteCache(max_entries=2, ttl=timedelta(minutes=2))
    q = sample_quote(rights=licensed())
    keys = [
        QuoteCacheKey("provider-A", f"user:{i}", q.entitlement_scope, QUOTE_REQUEST)
        for i in range(3)
    ]
    cache.put(keys[0], q, now=NOW)
    cache.put(keys[1], q, now=NOW)
    assert cache.get(keys[0], now=NOW) == q
    cache.put(keys[2], q, now=NOW)
    assert cache.get(keys[1], now=NOW) is None
    assert len(cache) == 2
    assert cache.get(keys[0], now=NOW - timedelta(seconds=1)) is None


def test_cache_does_not_store_future_or_unlicensed_or_wrong_identity():
    cache = BoundedQuoteCache()
    key = QuoteCacheKey("provider-A", "local", "test:plan:A", QUOTE_REQUEST)
    cache.put(key, sample_quote(), now=NOW)
    assert len(cache) == 0
    cache.put(key, sample_quote(rights=licensed(), received_at=NOW + timedelta(seconds=1),
                                event_at=NOW + timedelta(seconds=1)), now=NOW)
    assert len(cache) == 0
    cache.put(key, sample_quote(rights=licensed(), scope="other:plan"), now=NOW)
    assert len(cache) == 0


def test_invalidation_forces_provider_refresh_without_resaving_thesis():
    provider = FakeProvider(sample_quote(rights=licensed()))
    app = service(provider)
    run(app.quote(QUOTE_REQUEST, max_age=timedelta(seconds=30)))
    app.invalidate_quote(QUOTE_REQUEST)
    assert app.cache_size == 0
    provider.observation = sample_quote(rights=licensed(), price="142.00")
    result = run(app.quote(QUOTE_REQUEST, max_age=timedelta(seconds=30)))
    assert result.quote.price == Decimal("142.00")
    assert result.from_cache is False
    assert provider.quote_calls == 2


def test_current_quote_result_rejects_wrong_instrument_kind_and_required_timeliness():
    provider = FakeProvider(replace(
        sample_quote(), instrument=InstrumentId("DEMO", "XNYS", "USD")
    ))
    with pytest.raises(ProviderFailure) as err:
        run(service(provider).quote(QUOTE_REQUEST, max_age=None))
    assert err.value.code == ProviderFailureCode.INVALID_RESPONSE
    provider.observation = replace(sample_quote(), kind=QuoteKind.LAST)
    with pytest.raises(ProviderFailure):
        run(service(provider).quote(QUOTE_REQUEST, max_age=None))
    req = QuoteRequest(INSTRUMENT, kind=QuoteKind.CLOSE,
                       required_timeliness=QuoteTimeliness.REAL_TIME)
    provider.observation = sample_quote()
    with pytest.raises(ProviderFailure):
        run(service(provider).quote(req, max_age=None))


def test_provider_future_clock_is_rejected_instead_of_labeling_live():
    provider = FakeProvider(sample_quote(
        event_at=NOW + timedelta(days=1), received_at=NOW + timedelta(days=1)
    ))
    with pytest.raises(ProviderFailure, match="timestamp"):
        run(service(provider).quote(QUOTE_REQUEST, max_age=timedelta(minutes=5)))


def test_retryable_timeout_and_rate_limit_use_bounded_retries_without_external_sleep():
    sleeps = []
    async def fake_sleep(seconds):
        sleeps.append(seconds)
    faults = [
        ProviderFailure("Synthetic Provider", ProviderFailureCode.TIMEOUT, "timeout"),
        ProviderFailure("Synthetic Provider", ProviderFailureCode.RATE_LIMITED, "rate",
                        retry_after_seconds=2),
    ]
    provider = FakeProvider(failures=faults)
    app = service(
        provider, sleep=fake_sleep,
        retry=RetryPolicy(max_attempts=3, base_delay_seconds=0.2, max_delay_seconds=4)
    )
    result = run(app.quote(QUOTE_REQUEST, max_age=None))
    assert result.attempts == 3
    assert provider.quote_calls == 3
    assert sleeps == [0.2, 2]


def test_no_retry_on_denied_entitlement_or_very_long_retry_after():
    sleeps = []
    async def fake_sleep(seconds):
        sleeps.append(seconds)
    denial = ProviderFailure(
        "Synthetic Provider", ProviderFailureCode.ENTITLEMENT_DENIED, "denied"
    )
    p = FakeProvider(failures=[denial])
    with pytest.raises(ProviderFailure) as error:
        run(service(p, sleep=fake_sleep).quote(QUOTE_REQUEST, max_age=None))
    assert error.value.code == ProviderFailureCode.ENTITLEMENT_DENIED
    assert p.quote_calls == 1 and sleeps == []
    rate = ProviderFailure(
        "Synthetic Provider", ProviderFailureCode.RATE_LIMITED, "rate",
        retry_after_seconds=30,
    )
    p2 = FakeProvider(failures=[rate])
    with pytest.raises(ProviderFailure):
        run(service(p2, sleep=fake_sleep).quote(QUOTE_REQUEST, max_age=None))
    assert p2.quote_calls == 1 and sleeps == []


def test_filing_result_is_on_demand_and_never_cached():
    provider = FakeProvider()
    app = service(provider)
    one = run(app.filings(FilingRequest(ISSUER)))
    two = run(app.filings(FilingRequest(ISSUER)))
    assert one.attempts == two.attempts == 1
    assert one.filings[0].publicly_available_at is None
    assert provider.filing_calls == 2
    assert app.cache_size == 0


def test_cross_issuer_and_overlimit_filing_responses_rejected():
    wrong_issuer = replace(
        FakeProvider()._filings[0], issuer=IssuerId("SEC_CIK", "0000777777")
    )
    for rows in ((wrong_issuer,), FakeProvider()._filings * 2):
        provider = FakeProvider(filings=rows)
        with pytest.raises(ProviderFailure) as error:
            run(service(provider).filings(FilingRequest(ISSUER, limit=1)))
        assert error.value.code == ProviderFailureCode.INVALID_RESPONSE


def test_provider_capability_denial_does_not_issue_network_requests():
    provider = FakeProvider()
    provider.capabilities = ProviderCapabilities(
        "Synthetic Provider", frozenset({DataCapability.FILINGS})
    )
    with pytest.raises(ProviderFailure) as error:
        run(service(provider).quote(QUOTE_REQUEST, max_age=None))
    assert error.value.code == ProviderFailureCode.UNSUPPORTED_REQUEST
    assert provider.quote_calls == 0


def test_cache_configuration_and_missing_identity_validation():
    with pytest.raises(ValueError):
        BoundedQuoteCache(max_entries=0)
    with pytest.raises(ValueError):
        BoundedQuoteCache(ttl=timedelta(0))
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=0)
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=4)
    with pytest.raises(ValueError):
        service(FakeProvider(), principal=" ")


def test_real_twelve_data_unknown_rights_never_cached_without_license():
    # The actual adapter is exercised with a fake HTTP transport, never a key
    # or provider endpoint on the network.
    from investiq_core.adapters.twelve_data import TwelveDataQuoteProvider

    class FakeHTTP:
        async def get_json(self, url, *, headers):
            return {
                "symbol": "DEMO", "mic_code": "XNAS", "currency": "USD",
                "close": "100.00", "last_quote_at": int(NOW.timestamp()),
                "is_market_open": False,
            }

    real_adapter = TwelveDataQuoteProvider(
        api_key="SYNTHETIC-KEY", transport=FakeHTTP(), clock=lambda: NOW
    )
    fake_filing = FakeProvider()
    app = ConnectedDataService(
        quote_provider=real_adapter, filing_provider=fake_filing,
        principal_scope="local", clock=lambda: NOW,
    )
    run(app.quote(QUOTE_REQUEST, max_age=timedelta(minutes=1)))
    run(app.quote(QUOTE_REQUEST, max_age=timedelta(minutes=1)))
    assert app.cache_size == 0


def test_scope_lookup_index_is_bounded_with_lru_cache():
    # Regression: an unbounded request-to-entitlement index defeats max_entries.
    class MultiTicker(FakeProvider):
        async def get_quote(self, request):
            self.quote_calls += 1
            return replace(
                self.observation,
                instrument=request.instrument,
                provider_symbol=request.instrument.ticker,
                quote_id="synthetic:" + request.instrument.ticker,
            )

    provider = MultiTicker(sample_quote(rights=licensed()))
    app = service(provider, cache=BoundedQuoteCache(max_entries=2))
    for n in range(30):
        request = QuoteRequest(
            InstrumentId(f"TEST{n}", "XNAS", "USD"), kind=QuoteKind.CLOSE
        )
        run(app.quote(request, max_age=timedelta(minutes=1)))
    assert app.cache_size <= 2
    assert len(app._quote_scopes) <= 2


@pytest.mark.parametrize("invalidation", ["clear", "single"])
def test_inflight_quote_cannot_repopulate_or_escape_invalidated_access(invalidation):
    async def scenario():
        start = asyncio.Event()
        finish = asyncio.Event()

        class SlowProvider(FakeProvider):
            async def get_quote(self, request):
                start.set()
                await finish.wait()
                return await super().get_quote(request)

        provider = SlowProvider(sample_quote(rights=licensed()))
        app = service(provider)
        pending = asyncio.create_task(
            app.quote(QUOTE_REQUEST, max_age=timedelta(minutes=1))
        )
        await start.wait()
        if invalidation == "clear":
            app.clear_cache()
        else:
            app.invalidate_quote(QUOTE_REQUEST)
        finish.set()
        with pytest.raises(ProviderFailure) as error:
            await pending
        assert error.value.code == ProviderFailureCode.ENTITLEMENT_DENIED
        assert app.cache_size == 0
        assert app._quote_scopes == {}

    run(scenario())
