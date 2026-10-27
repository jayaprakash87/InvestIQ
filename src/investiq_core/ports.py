"""Provider-neutral async ports and categorized, safe failure contracts.

No network or paid-provider dependency is imported here. Concrete adapters
are deliberately postponed to v0.2 PR 2 and must enforce the entitlements.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol

from .evidence import InstrumentId
from .fundamentals import FilingReference
from .market import IssuerId, MarketQuote, QuoteKind, QuoteTimeliness


class DataCapability(str, Enum):
    QUOTES = "quotes"
    PRICE_HISTORY = "price_history"
    FILINGS = "filings"
    FUNDAMENTALS = "fundamentals"
    ESTIMATES = "estimates"
    FX = "fx"
    NEWS = "news"


@dataclass(frozen=True, slots=True)
class ProviderCapabilities:
    provider: str
    supported: frozenset[DataCapability]

    def __post_init__(self) -> None:
        if not isinstance(self.provider, str) or not self.provider.strip():
            raise ValueError("provider must be nonempty")
        if not isinstance(self.supported, frozenset) or any(
            not isinstance(item, DataCapability) for item in self.supported
        ):
            raise TypeError("supported must be a frozenset of DataCapability")

    def has(self, capability: DataCapability) -> bool:
        if not isinstance(capability, DataCapability):
            raise TypeError("capability must be DataCapability")
        return capability in self.supported


class ProviderFailureCode(str, Enum):
    UNAUTHORIZED = "unauthorized"
    ENTITLEMENT_DENIED = "entitlement_denied"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    TEMPORARILY_UNAVAILABLE = "temporarily_unavailable"
    UNSUPPORTED_INSTRUMENT = "unsupported_instrument"
    AMBIGUOUS_INSTRUMENT = "ambiguous_instrument"
    MISSING_DATA = "missing_data"
    INVALID_RESPONSE = "invalid_response"


_RETRYABLE = frozenset({
    ProviderFailureCode.RATE_LIMITED,
    ProviderFailureCode.TIMEOUT,
    ProviderFailureCode.TEMPORARILY_UNAVAILABLE,
})


class ProviderFailure(Exception):
    """Safe error category; sanitized public messages must not include secrets."""

    def __init__(
        self, provider: str, code: ProviderFailureCode, message: str,
        *, retry_after_seconds: int | None = None,
    ) -> None:
        if not isinstance(provider, str) or not provider.strip():
            raise ValueError("provider must be nonempty")
        if not isinstance(code, ProviderFailureCode):
            raise TypeError("code must be ProviderFailureCode")
        if not isinstance(message, str) or not message.strip():
            raise ValueError("message must be nonempty")
        if retry_after_seconds is not None and (
            not isinstance(retry_after_seconds, int)
            or isinstance(retry_after_seconds, bool)
            or retry_after_seconds < 0
            or code != ProviderFailureCode.RATE_LIMITED
        ):
            raise ValueError("retry_after_seconds requires a rate-limited response")
        self.provider = provider
        self.code = code
        self.retry_after_seconds = retry_after_seconds
        super().__init__(message)

    @property
    def retryable(self) -> bool:
        return self.code in _RETRYABLE


@dataclass(frozen=True, slots=True)
class QuoteRequest:
    instrument: InstrumentId
    kind: QuoteKind = QuoteKind.LAST
    required_timeliness: QuoteTimeliness | None = None
    as_of: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.instrument, InstrumentId):
            raise TypeError("instrument must be InstrumentId")
        if not isinstance(self.kind, QuoteKind):
            raise TypeError("kind must be QuoteKind")
        if self.required_timeliness is not None and not isinstance(
            self.required_timeliness, QuoteTimeliness
        ):
            raise TypeError("required_timeliness must be QuoteTimeliness or None")
        if self.as_of is not None and (
            not isinstance(self.as_of, datetime)
            or self.as_of.tzinfo is None
            or self.as_of.utcoffset() is None
        ):
            raise ValueError("as_of must be timezone-aware")


@dataclass(frozen=True, slots=True)
class FilingRequest:
    issuer: IssuerId
    limit: int = 10

    def __post_init__(self) -> None:
        if not isinstance(self.issuer, IssuerId):
            raise TypeError("issuer must be IssuerId")
        if not isinstance(self.limit, int) or isinstance(self.limit, bool) or not 1 <= self.limit <= 100:
            raise ValueError("limit must be an integer from 1 through 100")


class QuoteProvider(Protocol):
    @property
    def capabilities(self) -> ProviderCapabilities: ...

    async def get_quote(self, request: QuoteRequest) -> MarketQuote: ...


class FilingProvider(Protocol):
    @property
    def capabilities(self) -> ProviderCapabilities: ...

    async def list_filings(self, request: FilingRequest) -> tuple[FilingReference, ...]: ...
