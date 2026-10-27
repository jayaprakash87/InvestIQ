"""Bounded HTTPS JSON transport with safe, credential-free exceptions.

All provider endpoints are fixed by individual adapters. Requests are never
automatically redirected; response bodies and provider error text are not logged.
"""

from __future__ import annotations

import asyncio
import json
from decimal import Decimal
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from http.client import HTTPException
from math import ceil
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener


@dataclass(frozen=True, slots=True)
class TransportStatusError(Exception):
    status: int
    retry_after_seconds: int | None = None


class TransportTimeoutError(Exception):
    pass


class TransportUnavailableError(Exception):
    pass


class TransportInvalidResponseError(Exception):
    pass


class JsonTransport(Protocol):
    async def get_json(self, url: str, *, headers: Mapping[str, str]) -> Any: ...


class _RejectRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def _retry_after_seconds(raw: str | None, *, now: datetime) -> int | None:
    """HTTP Retry-After supports delta-seconds OR an RFC 9110 HTTP-date.

    Preserve the provider's minimum wait so the caller can refuse a retry
    beyond its budget. Unexpected/malformed formats remain untrusted.
    """
    if not isinstance(raw, str) or not raw or len(raw) > 128 or not raw.isascii():
        return None
    if raw.isdigit():
        try:
            return min(int(raw), 86_400)
        except ValueError:
            return None
    try:
        end = parsedate_to_datetime(raw)
        if end.tzinfo is None or end.utcoffset() is None:
            return None
        return max(0, ceil((end.astimezone(UTC) - now.astimezone(UTC)).total_seconds()))
    except (TypeError, ValueError, OverflowError):
        return None


class UrllibJsonTransport:
    """No extra runtime dependency; injectable for offline contract tests."""

    def __init__(
        self,
        *,
        timeout_seconds: float = 10.0,
        max_bytes: int = 2_000_000,
        clock: Callable[[], datetime] | None = None,
    ):
        if not isinstance(timeout_seconds, (int, float)) or not 0 < timeout_seconds <= 60:
            raise ValueError("timeout_seconds must be between 0 and 60")
        if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or not 0 < max_bytes <= 10_000_000:
            raise ValueError("max_bytes must be a positive integer <= 10 MB")
        self._timeout_seconds = timeout_seconds
        self._max_bytes = max_bytes
        self._clock = clock or (lambda: datetime.now(UTC))

    async def get_json(self, url: str, *, headers: Mapping[str, str]) -> Any:
        # Network I/O is off the event loop; no hidden retries.
        return await asyncio.to_thread(self._request, url, dict(headers))

    def _request(self, url: str, headers: dict[str, str]) -> Any:
        if not url.startswith("https://"):
            raise TransportInvalidResponseError("only HTTPS is permitted")
        request = Request(url, method="GET", headers={"Accept": "application/json", **headers})
        opener = build_opener(_RejectRedirect())
        try:
            with opener.open(request, timeout=self._timeout_seconds) as response:
                raw = response.read(self._max_bytes + 1)
        except HTTPError as exc:
            retry_after = None
            if exc.code == 429 and exc.headers is not None:
                retry_after = _retry_after_seconds(
                    exc.headers.get("Retry-After"), now=self._clock()
                )
            # Never surface the URL, headers, provider body or exception text.
            raise TransportStatusError(exc.code, retry_after) from None
        except TimeoutError:
            raise TransportTimeoutError() from None
        except (URLError, OSError, HTTPException):
            # Truncated chunked/body responses (e.g. IncompleteRead) must
            # become typed, safely retryable provider failures.
            raise TransportUnavailableError() from None
        if len(raw) > self._max_bytes:
            raise TransportInvalidResponseError("provider JSON exceeds response limit")
        try:
            return json.loads(
                raw.decode("utf-8"),
                parse_float=Decimal,
                parse_constant=lambda _value: (_ for _ in ()).throw(ValueError()),
            )
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
            raise TransportInvalidResponseError("invalid JSON response") from None
