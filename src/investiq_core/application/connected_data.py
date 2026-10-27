"""Connected, on-demand research data retrieval with bounded optional caching.

This layer **does not** produce valuations, save theses, redistribute quote data,
or grant market-data rights. Every returned quote retains provider provenance,
session, rights and asserted timeliness; age is assessed independently.
"""

from __future__ import annotations

import asyncio
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol, TypeVar

from ..fundamentals import FilingReference
from ..market import MarketQuote, QuoteFreshness, assess_quote_freshness
from ..ports import (
    DataCapability,
    FilingProvider,
    FilingRequest,
    ProviderFailure,
    ProviderFailureCode,
    QuoteProvider,
    QuoteRequest,
)

T = TypeVar("T")


def _instant(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("clock must return a timezone-aware datetime")
    return value.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Conservative request retry policy, without jitter or hidden loops.

    For 429 responses, provider Retry-After is a *minimum* delay, never a
    maximum. If it exceeds our budget, fail rather than violate the quota.
    """

    max_attempts: int = 2
    base_delay_seconds: float = 0.5
    max_delay_seconds: float = 5.0

    def __post_init__(self) -> None:
        if type(self.max_attempts) is not int or not 1 <= self.max_attempts <= 3:
            raise ValueError("max_attempts must be between 1 and 3")
        for name in ("base_delay_seconds", "max_delay_seconds"):
            value = getattr(self, name)
            if type(value) not in (int, float) or not 0 < value <= 30:
                raise ValueError(f"{name} must be a positive bounded number")
        if self.max_delay_seconds < self.base_delay_seconds:
            raise ValueError("max_delay_seconds must not be less than base delay")


@dataclass(frozen=True, slots=True)
class QuoteResult:
    quote: MarketQuote
    freshness: QuoteFreshness
    from_cache: bool
    attempts: int

    def __post_init__(self) -> None:
        if not isinstance(self.quote, MarketQuote):
            raise TypeError("quote must be MarketQuote")
        if not isinstance(self.freshness, QuoteFreshness):
            raise TypeError("freshness must be QuoteFreshness")
        if type(self.attempts) is not int or self.attempts < 0:
            raise ValueError("attempts must be a nonnegative integer")
        if not isinstance(self.from_cache, bool):
            raise TypeError("from_cache must be a boolean")


@dataclass(frozen=True, slots=True)
class FilingResult:
    filings: tuple[FilingReference, ...]
    attempts: int

    def __post_init__(self) -> None:
        if not isinstance(self.filings, tuple) or not all(
            isinstance(item, FilingReference) for item in self.filings
        ):
            raise TypeError("filings must be a tuple of FilingReference")
        if type(self.attempts) is not int or self.attempts < 1:
            raise ValueError("attempts must be positive")


@dataclass(frozen=True, slots=True)
class QuoteCacheKey:
    """Future cache-port key: caller identity/entitlement AND provider-specific query.

    Do not construct scope values from unauthenticated user-supplied headers in
    a hosted application. This module only uses a private single-client cache.
    """

    provider_instance: str
    principal_scope: str
    entitlement_scope: str
    request: QuoteRequest

    def __post_init__(self) -> None:
        for name in ("provider_instance", "principal_scope", "entitlement_scope"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be nonempty")
        if not isinstance(self.request, QuoteRequest):
            raise TypeError("request must be QuoteRequest")


class QuoteCachePort(Protocol):
    """Design boundary for later entitlement-aware shared caches; not deployed."""

    def get(self, key: QuoteCacheKey, *, now: datetime) -> MarketQuote | None: ...

    def put(
        self, key: QuoteCacheKey, quote: MarketQuote, *, now: datetime
    ) -> None: ...

    def invalidate(self, key: QuoteCacheKey) -> None: ...

    def clear(self) -> None: ...


class BoundedQuoteCache:
    """In-process LRU with per-entry TTL. Only stores explicitly cacheable quotes.

    Does not claim a provider's market-data rights. A caller still supplies the
    scoped key and controls cache policy/authorization. Not a shared host cache.
    """

    def __init__(self, *, max_entries: int = 128, ttl: timedelta = timedelta(seconds=30)):
        if type(max_entries) is not int or not 1 <= max_entries <= 10_000:
            raise ValueError("max_entries must be a positive bounded integer")
        if not isinstance(ttl, timedelta) or not timedelta(0) < ttl <= timedelta(hours=1):
            raise ValueError("ttl must be between 0 and one hour")
        self._max = max_entries
        self._ttl = ttl
        self._entries: OrderedDict[QuoteCacheKey, tuple[MarketQuote, datetime]] = OrderedDict()

    def get(self, key: QuoteCacheKey, *, now: datetime) -> MarketQuote | None:
        current = _instant(now)
        entry = self._entries.get(key)
        if entry is None:
            return None
        quote, inserted = entry
        if (
            current < inserted
            or current - inserted >= self._ttl
            or not quote.rights.allows("cache")
            or quote.entitlement_scope != key.entitlement_scope
        ):
            self._entries.pop(key, None)
            return None
        self._entries.move_to_end(key)
        return quote

    def put(self, key: QuoteCacheKey, quote: MarketQuote, *, now: datetime) -> None:
        recorded = _instant(now)
        if (
            not quote.rights.allows("cache")
            or quote.entitlement_scope != key.entitlement_scope
            or quote.instrument != key.request.instrument
            or quote.kind != key.request.kind
            or quote.received_at.astimezone(UTC) > recorded
            or quote.event_at.astimezone(UTC) > recorded
        ):
            # Rights, identity or clock mismatch: no storage.
            return
        self._entries[key] = (quote, recorded)
        self._entries.move_to_end(key)
        while len(self._entries) > self._max:
            self._entries.popitem(last=False)

    def invalidate(self, key: QuoteCacheKey) -> None:
        self._entries.pop(key, None)

    def clear(self) -> None:
        self._entries.clear()

    def __len__(self) -> int:
        return len(self._entries)


class ConnectedDataService:
    """One provider account/principal per service instance, never a hosted auth boundary.

    Supply a private in-process quote cache only when the provider *explicitly*
    licenses storage. QuoteResult exposes the source's age and rights; it never
    upgrades a delayed/EOD/unknown quote to a live label.
    """

    def __init__(
        self,
        *,
        quote_provider: QuoteProvider,
        filing_provider: FilingProvider,
        principal_scope: str,
        clock: Callable[[], datetime] | None = None,
        sleep: Callable[[float], Awaitable[None]] | None = None,
        retry: RetryPolicy | None = None,
        cache: BoundedQuoteCache | None = None,
    ) -> None:
        if not isinstance(principal_scope, str) or not principal_scope.strip():
            raise ValueError("principal_scope must be a nonempty internal identity")
        self._quote_provider = quote_provider
        self._filing_provider = filing_provider
        self._principal_scope = principal_scope
        self._clock = clock or (lambda: datetime.now(UTC))
        self._sleep = sleep or asyncio.sleep
        self._retry = retry or RetryPolicy()
        self._cache = cache if cache is not None else BoundedQuoteCache()
        # This namespace is intentionally local to a specific provider object,
        # not a value claim usable as a global multi-process authorization key.
        self._provider_instance = f"local:{id(quote_provider)}"
        self._quote_scopes: dict[QuoteRequest, str] = {}
        self._lock = asyncio.Lock()

    @property
    def cache_size(self) -> int:
        return len(self._cache)

    def clear_cache(self) -> None:
        """Call when credentials, license grants or principal change."""
        self._cache.clear()
        self._quote_scopes.clear()

    def invalidate_quote(self, request: QuoteRequest) -> None:
        entitlement = self._quote_scopes.pop(request, None)
        if entitlement is not None:
            self._cache.invalidate(self._key(request, entitlement))

    def _key(self, request: QuoteRequest, entitlement: str) -> QuoteCacheKey:
        return QuoteCacheKey(
            self._provider_instance, self._principal_scope, entitlement, request
        )

    async def _invoke(self, operation: Callable[[], Awaitable[T]]) -> tuple[T, int]:
        for attempt in range(1, self._retry.max_attempts + 1):
            try:
                return await operation(), attempt
            except ProviderFailure as error:
                if not error.retryable or attempt == self._retry.max_attempts:
                    raise
                delay = min(
                    self._retry.base_delay_seconds * (2 ** (attempt - 1)),
                    self._retry.max_delay_seconds,
                )
                if error.retry_after_seconds is not None:
                    delay = max(delay, error.retry_after_seconds)
                    if delay > self._retry.max_delay_seconds:
                        raise
                await self._sleep(delay)
        raise AssertionError("unreachable retry loop")

    async def quote(
        self,
        request: QuoteRequest,
        *,
        max_age: timedelta | None,
        allow_cache: bool = True,
    ) -> QuoteResult:
        if not isinstance(request, QuoteRequest):
            raise TypeError("request must be QuoteRequest")
        if not self._quote_provider.capabilities.has(DataCapability.QUOTES):
            raise ProviderFailure(
                self._quote_provider.capabilities.provider,
                ProviderFailureCode.UNSUPPORTED_REQUEST,
                "Provider does not support quotes",
            )
        # A policy is required to reuse any previously stored price.
        if max_age is not None and (
            not isinstance(max_age, timedelta) or max_age <= timedelta(0)
        ):
            raise ValueError("max_age must be positive or None")
        # Guard the cache read/write path. Async lock is per service instance;
        # this also prevents duplicate concurrent fetches for the same account.
        async with self._lock:
            now = _instant(self._clock())
            scope = self._quote_scopes.get(request)
            if allow_cache and max_age is not None and scope is not None:
                found = self._cache.get(self._key(request, scope), now=now)
                if found is not None and self._valid_quote(found, request, check=False):
                    status = assess_quote_freshness(found, now=now, max_age=max_age)
                    if status == QuoteFreshness.WITHIN_POLICY:
                        return QuoteResult(found, status, True, 0)
                    self._cache.invalidate(self._key(request, scope))
            quote, attempts = await self._invoke(
                lambda: self._quote_provider.get_quote(request)
            )
            self._valid_quote(quote, request)
            now = _instant(self._clock())
            try:
                freshness = assess_quote_freshness(quote, now=now, max_age=max_age)
            except ValueError as exc:
                raise ProviderFailure(
                    self._quote_provider.capabilities.provider,
                    ProviderFailureCode.INVALID_RESPONSE,
                    "Provider quote timestamp is inconsistent with the system clock",
                ) from None
            # NO cache when the record doesn't expressly allow it; this is
            # the case for Twelve Data BYOK until contractual rights verified.
            if (
                allow_cache and max_age is not None
                and freshness == QuoteFreshness.WITHIN_POLICY
                and quote.rights.allows("cache")
            ):
                key = self._key(request, quote.entitlement_scope)
                self._cache.put(key, quote, now=now)
                self._quote_scopes[request] = quote.entitlement_scope
            return QuoteResult(quote, freshness, False, attempts)

    def _valid_quote(self, quote: MarketQuote, request: QuoteRequest, *, check: bool = True) -> bool:
        valid = (
            isinstance(quote, MarketQuote)
            and quote.provider == self._quote_provider.capabilities.provider
            and quote.instrument == request.instrument
            and quote.kind == request.kind
            and (
                request.required_timeliness is None
                or quote.timeliness == request.required_timeliness
            )
        )
        if not valid and check:
            raise ProviderFailure(
                self._quote_provider.capabilities.provider,
                ProviderFailureCode.INVALID_RESPONSE,
                "Provider returned a quote that does not match the request",
            )
        return valid

    async def filings(self, request: FilingRequest) -> FilingResult:
        if not isinstance(request, FilingRequest):
            raise TypeError("request must be FilingRequest")
        if not self._filing_provider.capabilities.has(DataCapability.FILINGS):
            raise ProviderFailure(
                self._filing_provider.capabilities.provider,
                ProviderFailureCode.UNSUPPORTED_REQUEST,
                "Provider does not support filings",
            )
        records, attempts = await self._invoke(
            lambda: self._filing_provider.list_filings(request)
        )
        if (
            not isinstance(records, tuple)
            or len(records) > request.limit
            or any(
                not isinstance(row, FilingReference) or row.issuer != request.issuer
                for row in records
            )
        ):
            raise ProviderFailure(
                self._filing_provider.capabilities.provider,
                ProviderFailureCode.INVALID_RESPONSE,
                "Provider returned filings outside the requested issuer or limit",
            )
        # No claim of complete filing history or verified intraday availability.
        return FilingResult(records, attempts)
