"""No-network adapter ports: fake implementations exercise contract shape."""

import asyncio
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from investiq_core.evidence import InstrumentId
from investiq_core.fundamentals import FilingReference
from investiq_core.market import (
    IssuerId,
    MarketQuote,
    MarketSession,
    QuoteTimeliness,
)
from investiq_core.ports import (
    DataCapability,
    FilingProvider,
    FilingRequest,
    ProviderCapabilities,
    ProviderFailure,
    ProviderFailureCode,
    QuoteProvider,
    QuoteRequest,
)


def test_provider_capabilities_and_retryable_failure_categories() -> None:
    caps = ProviderCapabilities("FictionalFeed", frozenset({DataCapability.QUOTES}))
    assert caps.has(DataCapability.QUOTES)
    assert not caps.has(DataCapability.FILINGS)
    with pytest.raises(TypeError, match="DataCapability"):
        caps.has("quotes")
    with pytest.raises(TypeError, match="frozenset"):
        ProviderCapabilities("bad", {"quotes"})
    for code in (
        ProviderFailureCode.RATE_LIMITED,
        ProviderFailureCode.TIMEOUT,
        ProviderFailureCode.TEMPORARILY_UNAVAILABLE,
    ):
        assert ProviderFailure("synthetic", code, "safe").retryable
    for code in (
        ProviderFailureCode.UNAUTHORIZED,
        ProviderFailureCode.ENTITLEMENT_DENIED,
        ProviderFailureCode.AMBIGUOUS_INSTRUMENT,
        ProviderFailureCode.INVALID_RESPONSE,
        ProviderFailureCode.MISSING_DATA,
    ):
        assert not ProviderFailure("synthetic", code, "safe").retryable
    error = ProviderFailure(
        "synthetic", ProviderFailureCode.RATE_LIMITED, "quota exceeded",
        retry_after_seconds=10,
    )
    assert str(error) == "quota exceeded"
    assert error.retry_after_seconds == 10
    with pytest.raises(ValueError, match="rate-limited"):
        ProviderFailure(
            "synthetic", ProviderFailureCode.UNAUTHORIZED, "denied", retry_after_seconds=10
        )


def test_requests_validate_identity_time_and_limit() -> None:
    instrument = InstrumentId("DEMO", "XNAS", "USD")
    r = QuoteRequest(instrument, required_timeliness=QuoteTimeliness.REAL_TIME)
    assert r.required_timeliness == QuoteTimeliness.REAL_TIME
    with pytest.raises(ValueError, match="timezone-aware"):
        replace(r, as_of=datetime(2026, 10, 26))
    with pytest.raises(TypeError, match="QuoteTimeliness"):
        replace(r, required_timeliness="real_time")
    f = FilingRequest(IssuerId("SEC_CIK", "0000123456"))
    assert f.limit == 10
    with pytest.raises(ValueError, match="1 through 100"):
        replace(f, limit=101)
    with pytest.raises(ValueError, match="1 through 100"):
        replace(f, limit=True)


def test_async_fake_quote_and_filing_providers_need_no_network() -> None:
    instant = datetime(2026, 10, 26, 15, tzinfo=UTC)
    issuer = IssuerId("SEC_CIK", "0000123456")
    instrument = InstrumentId("DEMO", "XNAS", "USD")

    class FakeProvider:
        capabilities = ProviderCapabilities(
            "FictionalFeed", frozenset({DataCapability.QUOTES, DataCapability.FILINGS})
        )

        async def get_quote(self, request: QuoteRequest) -> MarketQuote:
            if request.required_timeliness == QuoteTimeliness.REAL_TIME:
                raise ProviderFailure(
                    "FictionalFeed", ProviderFailureCode.ENTITLEMENT_DENIED,
                    "Only delayed quotes are permitted",
                )
            return MarketQuote(
                quote_id="synthetic:quote",
                instrument=request.instrument,
                provider="FictionalFeed",
                provider_symbol=request.instrument.ticker,
                source_reference="synthetic:test",
                kind=request.kind,
                price=Decimal("50.00"),
                currency="USD",
                event_at=instant,
                received_at=instant,
                session=MarketSession.REGULAR,
                timeliness=QuoteTimeliness.DELAYED,
                entitlement_scope="demo",
            )

        async def list_filings(self, request: FilingRequest) -> tuple[FilingReference, ...]:
            return (
                FilingReference(
                    issuer=request.issuer, accession="synthetic:1", form="10-K",
                    filed_on=date(2026, 2, 1), source_reference="synthetic:filing",
                    retrieved_at=instant,
                ),
            )

    provider = FakeProvider()
    async def run() -> None:
        quote_provider: QuoteProvider = provider
        filing_provider: FilingProvider = provider
        found = await quote_provider.get_quote(QuoteRequest(instrument))
        assert found.price == Decimal("50.00")
        assert found.timeliness == QuoteTimeliness.DELAYED
        filings = await filing_provider.list_filings(FilingRequest(issuer))
        assert filings[0].issuer == issuer
        assert filings[0].publicly_available_at is None
        with pytest.raises(ProviderFailure) as failure:
            await quote_provider.get_quote(
                QuoteRequest(instrument, required_timeliness=QuoteTimeliness.REAL_TIME)
            )
        assert failure.value.code == ProviderFailureCode.ENTITLEMENT_DENIED
        assert not failure.value.retryable

    asyncio.run(run())
