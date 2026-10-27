"""Twelve Data BYOK quote adapter.

The /quote 'close' and 'last_quote_at' describe the most recent minute
candle; they are NOT a timestamped exchange trade. Timeliness is UNKNOWN
unless future entitlement verification is implemented. No caching or reuse.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import urlencode

from ..market import (
    MarketQuote,
    MarketSession,
    PriceAdjustment,
    QuoteKind,
    QuoteTimeliness,
)
from ..ports import (
    DataCapability,
    ProviderCapabilities,
    ProviderFailure,
    ProviderFailureCode,
    QuoteRequest,
)
from ._errors import translate_error
from ._http import (
    JsonTransport,
    TransportInvalidResponseError,
    TransportStatusError,
    TransportTimeoutError,
    TransportUnavailableError,
    UrllibJsonTransport,
)

TWELVE_DATA_ORIGIN = "https://api.twelvedata.com/quote"


class TwelveDataQuoteProvider:
    """QuoteProvider implementation for entitled self-supplied Twelve Data keys.

    The requested instrument MUST agree with returned symbol/MIC/currency.
    The provider's close is a minute-candle close, never mislabeled as a
    verified last trade, and the quote time is the minute candle timestamp.
    """

    capabilities = ProviderCapabilities("Twelve Data", frozenset({DataCapability.QUOTES}))

    def __init__(
        self,
        *,
        api_key: str,
        transport: JsonTransport | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if (
            not isinstance(api_key, str)
            or not api_key.strip()
            or api_key != api_key.strip()
            or any(ord(c) < 33 or ord(c) > 126 for c in api_key)
        ):
            raise ValueError("Twelve Data requires a private nonempty API key")
        self._key = api_key
        self._transport = transport if transport is not None else UrllibJsonTransport()
        self._clock = clock or (lambda: datetime.now(UTC))
        # Opaque namespace, not raw key. Future shared caches still need
        # explicit legal permission and tenant entitlement enforcement.
        self._scope = "twelvedata:byok:" + hashlib.sha256(api_key.encode()).hexdigest()[:24]

    async def get_quote(self, request: QuoteRequest) -> MarketQuote:
        if not isinstance(request, QuoteRequest):
            raise TypeError("request must be QuoteRequest")
        if request.kind != QuoteKind.CLOSE or request.as_of is not None:
            raise ProviderFailure(
                "Twelve Data", ProviderFailureCode.UNSUPPORTED_REQUEST,
                "Adapter supports current minute-candle close only",
            )
        if request.required_timeliness not in (None, QuoteTimeliness.UNKNOWN):
            raise ProviderFailure(
                "Twelve Data", ProviderFailureCode.ENTITLEMENT_DENIED,
                "Quote timeliness cannot be verified from this BYOK adapter",
            )
        ticker = request.instrument.ticker
        url = TWELVE_DATA_ORIGIN + "?" + urlencode(
            {"symbol": ticker, "apikey": self._key, "timezone": "UTC"}
        )
        try:
            payload = await self._transport.get_json(url, headers={})
        except (
            TransportStatusError,
            TransportTimeoutError,
            TransportUnavailableError,
            TransportInvalidResponseError,
        ) as exc:
            raise translate_error("Twelve Data", exc) from None

        received = self._clock()
        if (
            not isinstance(received, datetime)
            or received.tzinfo is None
            or received.utcoffset() is None
        ):
            raise ValueError("clock must provide timezone-aware datetime")
        if isinstance(payload, dict) and payload.get("status") == "error":
            code = payload.get("code")
            if type(code) is not int:
                code = 0
            if code == 429:
                failure = ProviderFailureCode.RATE_LIMITED
            elif code == 401:
                failure = ProviderFailureCode.UNAUTHORIZED
            elif code == 403:
                failure = ProviderFailureCode.ENTITLEMENT_DENIED
            elif code in (400, 404):
                failure = ProviderFailureCode.UNSUPPORTED_INSTRUMENT
            else:
                failure = ProviderFailureCode.INVALID_RESPONSE
            raise ProviderFailure(
                "Twelve Data", failure, "Twelve Data rejected the quote request"
            )
        try:
            return _parse_quote(payload, request, received, self._scope)
        except (ValueError, TypeError, KeyError, OverflowError, InvalidOperation) as exc:
            raise ProviderFailure(
                "Twelve Data", ProviderFailureCode.INVALID_RESPONSE,
                "Twelve Data quote failed identity/time/value validation",
            ) from None


def _parse_quote(
    payload: Any, request: QuoteRequest, received: datetime, scope: str
) -> MarketQuote:
    if not isinstance(payload, dict):
        raise ValueError("quote response must be an object")
    subject = request.instrument
    symbol = payload["symbol"]
    mic = payload["mic_code"]
    currency = payload["currency"]
    if symbol != subject.ticker or mic != subject.venue or currency != subject.trading_currency:
        raise ValueError("quote instrument identity mismatch")
    if not all(isinstance(x, str) for x in (symbol, mic, currency)):
        raise ValueError("quote instrument identity must be strings")
    # last_quote_at is the documented last minute-candle timestamp;
    # 'timestamp' may refer to a different candle and is not substituted.
    timestamp = payload["last_quote_at"]
    if type(timestamp) is not int or not 1_000_000_000 <= timestamp <= 4_102_444_800:
        raise ValueError("quote timestamp must be a plausible Unix second")
    event = datetime.fromtimestamp(timestamp, tz=UTC)
    raw_price = payload["close"]
    if not isinstance(raw_price, str) or re.fullmatch(
        r"[0-9]+(?:\.[0-9]+)?", raw_price
    ) is None:
        raise ValueError("close must be an exact positive decimal string")
    price = Decimal(raw_price)
    is_open = payload.get("is_market_open")
    if not isinstance(is_open, bool):
        raise ValueError("is_market_open must be an explicit boolean")
    # True does not prove regular vs pre/after market session. False describes
    # the provider's market status; never infer freshness from it.
    session = MarketSession.UNKNOWN if is_open else MarketSession.CLOSED
    digest = hashlib.sha256(
        f"{subject.ticker}:{subject.venue}:{timestamp}:{raw_price}".encode()
    ).hexdigest()[:24]
    reference = TWELVE_DATA_ORIGIN + "?" + urlencode({"symbol": symbol})
    return MarketQuote(
        quote_id=f"twelvedata:{digest}",
        instrument=subject,
        provider="Twelve Data",
        provider_symbol=symbol,
        source_reference=reference,
        kind=QuoteKind.CLOSE,
        price=price,
        currency=currency,
        event_at=event,
        received_at=received,
        session=session,
        timeliness=QuoteTimeliness.UNKNOWN,
        entitlement_scope=scope,
        adjustment=PriceAdjustment.UNKNOWN,
        # No false 'real-time' or '15-minute delay' claim from a 200 response.
        delay_seconds=None,
    )
