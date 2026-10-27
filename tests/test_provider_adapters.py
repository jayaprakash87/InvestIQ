"""Offline provider adapter acceptance: never use a real key or call the network."""

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from urllib.parse import parse_qs, urlparse

import pytest

from investiq_core.adapters._http import (
    TransportInvalidResponseError,
    TransportStatusError,
    TransportTimeoutError,
    TransportUnavailableError,
)
from investiq_core.adapters.sec_edgar import SecEdgarFilingProvider
from investiq_core.adapters.twelve_data import TwelveDataQuoteProvider
from investiq_core.evidence import InstrumentId
from investiq_core.market import IssuerId, MarketSession, QuoteKind, QuoteTimeliness
from investiq_core.ports import (
    DataCapability,
    FilingRequest,
    ProviderFailure,
    ProviderFailureCode,
    QuoteRequest,
)

NOW = datetime(2026, 10, 27, 16, tzinfo=UTC)
EVENT = datetime(2026, 10, 26, 15, tzinfo=UTC)
KEY = "SYNTHETIC-DO-NOT-USE"


class FakeTransport:
    def __init__(self, payload=None, *, failure: Exception | None = None):
        self.payload = payload
        self.failure = failure
        self.calls: list[tuple[str, dict[str, str]]] = []

    async def get_json(self, url: str, *, headers):
        self.calls.append((url, dict(headers)))
        if self.failure:
            raise self.failure
        return self.payload


def sec_payload():
    return {
        "cik": 320193,
        "filings": {"recent": {
            "accessionNumber": ["0000320193-26-000001", "0000320193-26-000002"],
            "form": ["10-K", "8-K"],
            "filingDate": ["2026-10-23", "2026-10-22"],
            "acceptanceDateTime": ["2026-10-23T16:10:01.000Z", "2026-10-22T16:10:01.000Z"],
        }},
    }


def quote_payload():
    return {
        "symbol": "DEMO",
        "mic_code": "XNAS",
        "currency": "USD",
        "close": "127.50000",
        "last_quote_at": int(EVENT.timestamp()),
        "timestamp": int((EVENT - timedelta(days=1)).timestamp()),
        "is_market_open": False,
    }


def get_filings(transport: FakeTransport, issuer=None, *, limit: int = 2):
    provider = SecEdgarFilingProvider(
        user_agent="InvestIQ Research developer@example.org",
        transport=transport, clock=lambda: NOW,
    )
    return asyncio.run(provider.list_filings(
        FilingRequest(issuer or IssuerId("SEC_CIK", "320193"), limit=limit)
    ))


def get_quote(transport: FakeTransport, request=None):
    provider = TwelveDataQuoteProvider(
        api_key=KEY, transport=transport, clock=lambda: NOW
    )
    return asyncio.run(provider.get_quote(
        request or QuoteRequest(InstrumentId("DEMO", "XNAS", "USD"), kind=QuoteKind.CLOSE)
    ))


def test_sec_returns_date_only_filing_records_and_no_fabricated_public_time():
    transport = FakeTransport(sec_payload())
    rows = get_filings(transport, limit=1)
    assert len(rows) == 1
    assert rows[0].accession == "0000320193-26-000001"
    assert rows[0].filed_on == date(2026, 10, 23)
    assert rows[0].retrieved_at == NOW
    assert rows[0].publicly_available_at is None
    assert "CIK0000320193.json" in transport.calls[0][0]
    assert transport.calls[0][1]["User-Agent"].endswith("developer@example.org")
    assert "accession=" in rows[0].source_reference


def test_sec_port_and_input_policy():
    assert SecEdgarFilingProvider.capabilities.has(DataCapability.FILINGS)
    assert not SecEdgarFilingProvider.capabilities.has(DataCapability.QUOTES)
    with pytest.raises(ValueError, match="User-Agent"):
        SecEdgarFilingProvider(user_agent="InvestIQ only")
    with pytest.raises(ValueError, match="0.2"):
        SecEdgarFilingProvider(
            user_agent="InvestIQ Research developer@example.org", min_interval_seconds=0
        )
    transport = FakeTransport(sec_payload())
    with pytest.raises(ProviderFailure) as exc:
        get_filings(transport, issuer=IssuerId("LEI", "012345"))
    assert exc.value.code == ProviderFailureCode.UNSUPPORTED_INSTRUMENT
    assert not transport.calls


@pytest.mark.parametrize("change", [
    {"cik": 999999},
    {"cik": "320193"},
    {"filings": {"recent": {"accessionNumber": ["a"], "form": ["10-K"], "filingDate": ["2026-10-23"]}}},
    {"filings": {"recent": {"accessionNumber": ["0000320193-26-000001"], "form": [], "filingDate": ["2026-10-23"]}}},
    {"filings": {"recent": {"accessionNumber": ["0000320193-26-000001"], "form": ["10-K"], "filingDate": ["2026-20-23"]}}},
    {"filings": {"recent": {"accessionNumber": ["0000320193-26-000001", "0000320193-26-000001"], "form": ["10-K", "10-K"], "filingDate": ["2026-10-23", "2026-10-23"]}}},
    {"filings": []},
])
def test_sec_rejects_wrong_entity_or_corrupt_filing_arrays(change):
    payload = sec_payload()
    payload.update(change)
    with pytest.raises(ProviderFailure) as exc:
        get_filings(FakeTransport(payload))
    assert exc.value.code == ProviderFailureCode.INVALID_RESPONSE


def test_twelve_quote_uses_minute_candle_timestamp_not_unrelated_timestamp():
    transport = FakeTransport(quote_payload())
    quote = get_quote(transport)
    assert quote.kind == QuoteKind.CLOSE
    assert quote.price == Decimal("127.50000")
    assert quote.event_at == EVENT
    assert quote.received_at == NOW
    assert quote.session == MarketSession.CLOSED
    assert quote.timeliness == QuoteTimeliness.UNKNOWN
    assert quote.delay_seconds is None
    assert quote.rights.allows("cache") is False
    assert quote.rights.allows("snapshot") is False
    assert quote.rights.allows("redistribute") is False
    assert quote.provider == "Twelve Data"
    assert quote.instrument.venue == "XNAS"
    assert KEY not in quote.source_reference
    assert KEY not in quote.entitlement_scope
    assert quote.entitlement_scope.startswith("twelvedata:byok:")
    assert TwelveDataQuoteProvider.capabilities.has(DataCapability.QUOTES)
    params = parse_qs(urlparse(transport.calls[0][0]).query)
    assert params["apikey"] == [KEY]
    assert params["timezone"] == ["UTC"]


def test_twelve_does_not_call_provider_for_unsupported_or_unverified_request():
    transport = FakeTransport(quote_payload())
    instrument = InstrumentId("DEMO", "XNAS", "USD")
    for request, reason in (
        (QuoteRequest(instrument), ProviderFailureCode.UNSUPPORTED_REQUEST),
        (QuoteRequest(instrument, kind=QuoteKind.CLOSE, as_of=EVENT),
         ProviderFailureCode.UNSUPPORTED_REQUEST),
        (QuoteRequest(instrument, kind=QuoteKind.CLOSE,
                      required_timeliness=QuoteTimeliness.REAL_TIME),
         ProviderFailureCode.ENTITLEMENT_DENIED),
    ):
        with pytest.raises(ProviderFailure) as exc:
            get_quote(transport, request=request)
        assert exc.value.code == reason
        assert exc.value.retryable is False
    assert transport.calls == []


@pytest.mark.parametrize("update", [
    {"symbol": "OTHER"},
    {"mic_code": "XNYS"},
    {"currency": "EUR"},
    {"close": 127.5},
    {"close": "-1.0"},
    {"close": "NaN"},
    {"close": "0"},
    {"last_quote_at": "not a time"},
    {"last_quote_at": 0},
    {"last_quote_at": int((NOW + timedelta(days=2)).timestamp())},
    {"is_market_open": "false"},
    {"is_market_open": None},
])
def test_twelve_quote_rejects_unsafe_identity_precision_time_and_response(update):
    payload = quote_payload()
    payload.update(update)
    with pytest.raises(ProviderFailure) as exc:
        get_quote(FakeTransport(payload))
    assert exc.value.code == ProviderFailureCode.INVALID_RESPONSE


def test_twelve_missing_timestamp_is_not_silently_replaced_by_received_time():
    payload = quote_payload()
    del payload["last_quote_at"]
    with pytest.raises(ProviderFailure) as exc:
        get_quote(FakeTransport(payload))
    assert exc.value.code == ProviderFailureCode.INVALID_RESPONSE


@pytest.mark.parametrize("code,expected,retryable", [
    (401, ProviderFailureCode.UNAUTHORIZED, False),
    (403, ProviderFailureCode.ENTITLEMENT_DENIED, False),
    (404, ProviderFailureCode.UNSUPPORTED_INSTRUMENT, False),
    (429, ProviderFailureCode.RATE_LIMITED, True),
    (999, ProviderFailureCode.INVALID_RESPONSE, False),
])
def test_twelve_business_errors_do_not_leak_vendor_text_or_key(code, expected, retryable):
    message = f"Sensitive secret {KEY} in provider response"
    payload = {"status": "error", "code": code, "message": message}
    with pytest.raises(ProviderFailure) as exc:
        get_quote(FakeTransport(payload))
    assert exc.value.code == expected
    assert exc.value.retryable == retryable
    assert KEY not in str(exc.value)
    assert message not in str(exc.value)


@pytest.mark.parametrize("failure,expected,retryable", [
    (TransportStatusError(401), ProviderFailureCode.UNAUTHORIZED, False),
    (TransportStatusError(403), ProviderFailureCode.ENTITLEMENT_DENIED, False),
    (TransportStatusError(429, 15), ProviderFailureCode.RATE_LIMITED, True),
    (TransportStatusError(503), ProviderFailureCode.TEMPORARILY_UNAVAILABLE, True),
    (TransportTimeoutError(), ProviderFailureCode.TIMEOUT, True),
    (TransportUnavailableError(), ProviderFailureCode.TEMPORARILY_UNAVAILABLE, True),
    (TransportInvalidResponseError(), ProviderFailureCode.INVALID_RESPONSE, False),
])
def test_both_adapters_map_network_errors_to_safe_domain_categories(failure, expected, retryable):
    for request in ("sec", "twelve"):
        with pytest.raises(ProviderFailure) as exc:
            if request == "sec":
                get_filings(FakeTransport(failure=failure))
            else:
                get_quote(FakeTransport(failure=failure))
        assert exc.value.code == expected
        assert exc.value.retryable == retryable
        assert KEY not in str(exc.value)
        if expected == ProviderFailureCode.RATE_LIMITED:
            assert exc.value.retry_after_seconds == 15


def test_no_key_saved_in_exception_for_invalid_api_result():
    transport = FakeTransport({"status": "error", "code": 401, "message": KEY})
    with pytest.raises(ProviderFailure) as exc:
        get_quote(transport)
    assert KEY not in str(exc.value)
    assert KEY not in repr(exc.value)


def test_filing_and_quote_adapters_require_timezone_aware_received_time():
    filing_provider = SecEdgarFilingProvider(
        user_agent="InvestIQ Research developer@example.org",
        transport=FakeTransport(sec_payload()), clock=lambda: datetime(2026, 10, 27),
    )
    with pytest.raises(ValueError, match="timezone-aware"):
        asyncio.run(filing_provider.list_filings(FilingRequest(IssuerId("SEC_CIK", "320193"))))
    quote_provider = TwelveDataQuoteProvider(
        api_key=KEY, transport=FakeTransport(quote_payload()),
        clock=lambda: datetime(2026, 10, 27),
    )
    with pytest.raises(ValueError, match="timezone-aware"):
        asyncio.run(quote_provider.get_quote(
            QuoteRequest(InstrumentId("DEMO", "XNAS", "USD"), kind=QuoteKind.CLOSE)
        ))
