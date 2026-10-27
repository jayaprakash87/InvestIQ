"""Synthetic market-domain tests; no network, vendor credentials or live data."""

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from investiq_core.evidence import InstrumentId
from investiq_core.market import (
    IssuerId,
    IssuerListing,
    MarketDataRights,
    MarketQuote,
    MarketSession,
    Permission,
    PriceAdjustment,
    QuoteFreshness,
    QuoteKind,
    QuoteTimeliness,
    assess_quote_freshness,
    resolve_issuer,
)


def observed() -> datetime:
    return datetime(2026, 10, 26, 15, tzinfo=UTC)


def quote(**changes: object) -> MarketQuote:
    arguments = {
        "quote_id": "synthetic:quote:1",
        "instrument": InstrumentId("DEMO", "XNAS", "USD"),
        "provider": "FictionalFeed",
        "provider_symbol": "DEMO",
        "source_reference": "synthetic:quote-response",
        "kind": QuoteKind.LAST,
        "price": Decimal("125.50"),
        "currency": "USD",
        "event_at": observed(),
        "received_at": observed() + timedelta(seconds=1),
        "session": MarketSession.REGULAR,
        "timeliness": QuoteTimeliness.DELAYED,
        "entitlement_scope": "demo-delayed-feed",
        "delay_seconds": 900,
    }
    arguments.update(changes)
    return MarketQuote(**arguments)


def test_quote_keeps_attribution_exact_precision_and_declared_delay() -> None:
    item = quote()
    assert item.price == Decimal("125.50")
    assert str(item.price) == "125.50"
    assert item.instrument.venue == "XNAS"
    assert item.timeliness == QuoteTimeliness.DELAYED
    assert item.delay_seconds == 900
    assert item.rights == MarketDataRights()
    assert not item.rights.allows("cache")
    assert not item.rights.allows("snapshot")
    assert not item.rights.allows("redistribute")


def test_freshness_is_caller_policy_not_vendor_tier_or_session() -> None:
    item = quote(timeliness=QuoteTimeliness.END_OF_DAY, delay_seconds=None,
                 session=MarketSession.CLOSED)
    now = item.received_at + timedelta(seconds=3)
    assert assess_quote_freshness(item, now=now, max_age=None) == QuoteFreshness.UNKNOWN
    assert assess_quote_freshness(
        item, now=now, max_age=timedelta(seconds=10)
    ) == QuoteFreshness.WITHIN_POLICY
    # An EOD quote can be recent under a caller policy. This does NOT upgrade
    # its classification to real-time or turn CLOSED into an open session.
    assert item.timeliness == QuoteTimeliness.END_OF_DAY
    assert item.session == MarketSession.CLOSED
    assert assess_quote_freshness(
        item, now=now + timedelta(seconds=30), max_age=timedelta(seconds=10)
    ) == QuoteFreshness.STALE


def test_quote_from_old_session_is_stale_despite_very_recent_retrieval() -> None:
    item = quote(
        event_at=observed() - timedelta(days=1),
        received_at=observed() + timedelta(seconds=1),
        timeliness=QuoteTimeliness.UNKNOWN,
        delay_seconds=None,
    )
    assert assess_quote_freshness(
        item, now=observed() + timedelta(seconds=2), max_age=timedelta(minutes=5)
    ) == QuoteFreshness.STALE
    assert item.timeliness == QuoteTimeliness.UNKNOWN


@pytest.mark.parametrize(
    "change,error",
    [
        ({"price": Decimal("0")}, "positive finite"),
        ({"price": Decimal("-1")}, "positive finite"),
        ({"price": Decimal("NaN")}, "positive finite"),
        ({"price": 125.5}, "positive finite"),
        ({"currency": "EUR"}, "trading currency"),
        ({"kind": "last"}, "QuoteKind"),
        ({"session": "regular"}, "MarketSession"),
        ({"timeliness": "real_time"}, "QuoteTimeliness"),
        ({"adjustment": "unadjusted"}, "PriceAdjustment"),
        ({"rights": None}, "MarketDataRights"),
        ({"event_at": observed() + timedelta(days=1)}, "event time"),
        ({"event_at": observed().replace(tzinfo=None)}, "timezone-aware"),
        ({"delay_seconds": 0}, "zero delay"),
        ({"delay_seconds": True}, "nonnegative integer"),
        ({"timeliness": QuoteTimeliness.REAL_TIME, "delay_seconds": 900}, "timeliness"),
        ({"timeliness": QuoteTimeliness.END_OF_DAY, "delay_seconds": 900}, "timeliness"),
        ({"provider": ""}, "nonempty"),
    ],
)
def test_invalid_or_misleading_quote_is_rejected(change: dict, error: str) -> None:
    with pytest.raises((ValueError, TypeError), match=error):
        quote(**change)


def test_freshness_rejects_invalid_clock_and_policy() -> None:
    item = quote()
    with pytest.raises(ValueError, match="clock"):
        assess_quote_freshness(item, now=observed(), max_age=timedelta(seconds=5))
    with pytest.raises(ValueError, match="timezone-aware"):
        assess_quote_freshness(
            item, now=datetime(2026, 10, 26, 16), max_age=timedelta(seconds=5)
        )
    with pytest.raises(ValueError, match="positive timedelta"):
        assess_quote_freshness(
            item, now=observed() + timedelta(days=1), max_age=timedelta(0)
        )


def test_rights_explicitly_allow_only_named_operations() -> None:
    rights = MarketDataRights(cache=Permission.ALLOWED, snapshot=Permission.DENIED)
    assert rights.allows("cache")
    assert not rights.allows("snapshot")
    assert not rights.allows("redistribute")
    with pytest.raises(ValueError, match="unknown"):
        rights.allows("trade")
    with pytest.raises(TypeError, match="Permission"):
        MarketDataRights(cache=True)
    # An adapter cannot quietly change the rights attached to an old record.
    assert replace(quote(), rights=rights).rights.cache == Permission.ALLOWED


def test_issuer_mapping_is_venue_qualified_and_effective_dated() -> None:
    issuer = IssuerId("SEC_CIK", "0000123456")
    instrument = InstrumentId("DEMO", "XNAS", "USD")
    link = IssuerListing(
        issuer=issuer,
        instrument=instrument,
        effective_from=date(2025, 1, 1),
        effective_until=date(2026, 1, 1),
        source_reference="synthetic:listing",
        verified_at=observed(),
    )
    assert resolve_issuer([link], instrument=instrument, on=date(2025, 1, 1)) == issuer
    assert resolve_issuer([link], instrument=instrument, on=date(2026, 1, 1)) == issuer
    with pytest.raises(ValueError, match="no issuer mapping"):
        resolve_issuer([link], instrument=instrument, on=date(2026, 1, 2))
    with pytest.raises(ValueError, match="no issuer mapping"):
        resolve_issuer(
            [link], instrument=InstrumentId("DEMO", "XNYS", "USD"), on=date(2025, 5, 1)
        )
    with pytest.raises(ValueError, match="ambiguous"):
        resolve_issuer([link, link], instrument=instrument, on=date(2025, 5, 1))
    with pytest.raises(ValueError, match="end"):
        replace(link, effective_until=date(2024, 12, 31))
    with pytest.raises(ValueError, match="namespace"):
        IssuerId("cik", "0000123456")
    with pytest.raises(ValueError, match="whitespace"):
        IssuerId("SEC_CIK", " 0000123456")
