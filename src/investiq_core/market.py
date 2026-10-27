"""Provider-neutral securities identity, market quotes, data rights and freshness.

A vendor describing a feed as "real_time" is *not* independent exchange
verification. Freshness is a separate caller-supplied age policy and never
upgrades delayed/EOD/unknown source classifications.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from enum import Enum

from .evidence import InstrumentId


def _nonempty(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be nonempty text")


def _aware(value: datetime, label: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be a timezone-aware datetime")


@dataclass(frozen=True, slots=True)
class IssuerId:
    """Reporting entity identifier, distinct from any listed share class.

    Namespace examples: SEC_CIK, LEI. The adapter must normalize and verify the
    identifier; these generic contracts cannot authenticate a registry record.
    """

    namespace: str
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.namespace, str) or not re.fullmatch(
            r"[A-Z][A-Z0-9_.-]{1,31}", self.namespace
        ):
            raise ValueError("issuer namespace must be a normalized identifier")
        _nonempty(self.value, "issuer value")
        if self.value != self.value.strip():
            raise ValueError("issuer value must not have surrounding whitespace")


@dataclass(frozen=True, slots=True)
class IssuerListing:
    """Effective-dated issuer-to-exchange instrument mapping with attribution."""

    issuer: IssuerId
    instrument: InstrumentId
    effective_from: date
    source_reference: str
    verified_at: datetime
    effective_until: date | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.issuer, IssuerId):
            raise TypeError("issuer must be IssuerId")
        if not isinstance(self.instrument, InstrumentId):
            raise TypeError("instrument must be InstrumentId")
        if not isinstance(self.effective_from, date) or isinstance(self.effective_from, datetime):
            raise TypeError("effective_from must be a date")
        if self.effective_until is not None:
            if not isinstance(self.effective_until, date) or isinstance(
                self.effective_until, datetime
            ):
                raise TypeError("effective_until must be a date")
            if self.effective_until < self.effective_from:
                raise ValueError("listing end must not precede its start")
        _nonempty(self.source_reference, "source_reference")
        _aware(self.verified_at, "verified_at")


def resolve_issuer(
    listings: Iterable[IssuerListing], *, instrument: InstrumentId, on: date
) -> IssuerId:
    """Resolve a listing explicitly; never guess from a bare ticker.

    Inclusive date bounds, ambiguous overlapping mappings and no coverage fail
    closed. This does not prove the mapping source is genuine.
    """
    if not isinstance(instrument, InstrumentId):
        raise TypeError("instrument must be InstrumentId")
    if not isinstance(on, date) or isinstance(on, datetime):
        raise TypeError("on must be a date")
    candidates = []
    for listing in listings:
        if not isinstance(listing, IssuerListing):
            raise TypeError("listings must contain IssuerListing")
        if (
            listing.instrument == instrument
            and listing.effective_from <= on
            and (listing.effective_until is None or on <= listing.effective_until)
        ):
            candidates.append(listing.issuer)
    if not candidates:
        raise ValueError("no issuer mapping for instrument at requested date")
    if len(candidates) != 1:
        raise ValueError("ambiguous issuer mapping at requested date")
    return candidates[0]


class QuoteKind(str, Enum):
    LAST = "last"
    BID = "bid"
    ASK = "ask"
    OPEN = "open"
    CLOSE = "close"


class MarketSession(str, Enum):
    PRE_MARKET = "pre_market"
    REGULAR = "regular"
    AFTER_HOURS = "after_hours"
    CLOSED = "closed"
    HALTED = "halted"
    UNKNOWN = "unknown"


class QuoteTimeliness(str, Enum):
    REAL_TIME = "real_time"
    DELAYED = "delayed"
    END_OF_DAY = "end_of_day"
    HISTORICAL = "historical"
    UNKNOWN = "unknown"


class PriceAdjustment(str, Enum):
    UNADJUSTED = "unadjusted"
    SPLIT_ADJUSTED = "split_adjusted"
    TOTAL_RETURN_ADJUSTED = "total_return_adjusted"
    UNKNOWN = "unknown"


class Permission(str, Enum):
    """Source-granted rights; UNKNOWN is not approval."""

    UNKNOWN = "unknown"
    ALLOWED = "allowed"
    DENIED = "denied"


@dataclass(frozen=True, slots=True)
class MarketDataRights:
    """Default-deny for storing, sharing or redistributing market-data records."""

    cache: Permission = Permission.UNKNOWN
    snapshot: Permission = Permission.UNKNOWN
    redistribute: Permission = Permission.UNKNOWN

    def __post_init__(self) -> None:
        for name in ("cache", "snapshot", "redistribute"):
            if not isinstance(getattr(self, name), Permission):
                raise TypeError(f"{name} must be a Permission")

    def allows(self, operation: str) -> bool:
        if operation not in ("cache", "snapshot", "redistribute"):
            raise ValueError("unknown data reuse operation")
        return getattr(self, operation) == Permission.ALLOWED


@dataclass(frozen=True, slots=True)
class MarketQuote:
    """Exact attributed quote, not a claim it is fresh or independently verified.

    Timeliness is a vendor/entitlement assertion; freshness must be assessed with
    a separate, category-specific age policy. No automatic FX conversion.
    """

    quote_id: str
    instrument: InstrumentId
    provider: str
    provider_symbol: str
    source_reference: str
    kind: QuoteKind
    price: Decimal
    currency: str
    event_at: datetime
    received_at: datetime
    session: MarketSession
    timeliness: QuoteTimeliness
    entitlement_scope: str
    adjustment: PriceAdjustment = PriceAdjustment.UNKNOWN
    delay_seconds: int | None = None
    rights: MarketDataRights = field(default_factory=MarketDataRights)

    def __post_init__(self) -> None:
        for name in (
            "quote_id", "provider", "provider_symbol", "source_reference", "entitlement_scope"
        ):
            _nonempty(getattr(self, name), name)
        if not isinstance(self.instrument, InstrumentId):
            raise TypeError("instrument must be InstrumentId")
        if not isinstance(self.kind, QuoteKind):
            raise TypeError("kind must be QuoteKind")
        if not isinstance(self.price, Decimal) or not self.price.is_finite() or self.price <= 0:
            raise ValueError("quote price must be a positive finite Decimal")
        if self.currency != self.instrument.trading_currency:
            raise ValueError("quote currency must match instrument trading currency; FX is explicit")
        _aware(self.event_at, "event_at")
        _aware(self.received_at, "received_at")
        if self.event_at.astimezone(UTC) > self.received_at.astimezone(UTC):
            raise ValueError("market event time must not follow receipt time")
        if not isinstance(self.session, MarketSession):
            raise TypeError("session must be MarketSession")
        if not isinstance(self.timeliness, QuoteTimeliness):
            raise TypeError("timeliness must be QuoteTimeliness")
        if not isinstance(self.adjustment, PriceAdjustment):
            raise TypeError("adjustment must be PriceAdjustment")
        if not isinstance(self.rights, MarketDataRights):
            raise TypeError("rights must be MarketDataRights")
        if self.delay_seconds is not None:
            if (
                not isinstance(self.delay_seconds, int)
                or isinstance(self.delay_seconds, bool)
                or self.delay_seconds < 0
            ):
                raise ValueError("delay_seconds must be a nonnegative integer")
            if self.timeliness == QuoteTimeliness.DELAYED:
                if self.delay_seconds == 0:
                    raise ValueError("delayed quote cannot declare zero delay")
            elif self.timeliness != QuoteTimeliness.REAL_TIME or self.delay_seconds != 0:
                raise ValueError("delay_seconds must match the stated timeliness")


class QuoteFreshness(str, Enum):
    WITHIN_POLICY = "within_policy"
    STALE = "stale"
    UNKNOWN = "unknown"


def assess_quote_freshness(
    quote: MarketQuote, *, now: datetime, max_age: timedelta | None
) -> QuoteFreshness:
    """Assess age only. WITHIN_POLICY does NOT mean real-time or open-market.

    The caller chooses max_age from the licensed provider, market session and
    product requirements; there is no universal price refresh/expiry duration.
    """
    if not isinstance(quote, MarketQuote):
        raise TypeError("quote must be MarketQuote")
    _aware(now, "now")
    if now.astimezone(UTC) < quote.received_at.astimezone(UTC):
        raise ValueError("freshness clock precedes quote receipt")
    if max_age is None:
        return QuoteFreshness.UNKNOWN
    if not isinstance(max_age, timedelta) or max_age <= timedelta(0):
        raise ValueError("max_age must be a positive timedelta or None")
    return (
        QuoteFreshness.STALE
        if now.astimezone(UTC) - quote.event_at.astimezone(UTC) > max_age
        else QuoteFreshness.WITHIN_POLICY
    )
