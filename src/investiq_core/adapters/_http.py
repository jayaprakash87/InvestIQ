"""Bounded HTTPS JSON transport with safe, credential-free exceptions.

All provider endpoints are fixed by individual adapters. Requests are never
automatically redirected; response bodies and provider error text are not logged.
"""

from __future__ import annotations

import asyncio
import json
import socket
from collections.abc import Mapping
from dataclasses import dataclass
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


class UrllibJsonTransport:
    """No extra runtime dependency; injectable for offline contract tests."""

    def __init__(self, *, timeout_seconds: float = 10.0, max_bytes: int = 2_000_000):
        if not isinstance(timeout_seconds, (int, float)) or not 0 < timeout_seconds <= 60:
            raise ValueError("timeout_seconds must be between 0 and 60")
        if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or not 0 < max_bytes <= 10_000_000:
            raise ValueError("max_bytes must be a positive integer <= 10 MB")
        self._timeout_seconds = timeout_seconds
        self._max_bytes = max_bytes

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
            if exc.code == 429:
                raw_retry = exc.headers.get("Retry-After")
                if raw_retry and raw_retry.isascii() and raw_retry.isdigit():
                    retry_after = min(int(raw_retry), 86_400)
            # Never surface the URL, headers, provider body or exception text.
            raise TransportStatusError(exc.code, retry_after) from None
        except (TimeoutError, socket.timeout) as exc:
            raise TransportTimeoutError() from None
        except (URLError, OSError) as exc:
            raise TransportUnavailableError() from None
        if len(raw) > self._max_bytes:
            raise TransportInvalidResponseError("provider JSON exceeds response limit")
        try:
            return json.loads(
                raw.decode("utf-8"),
                parse_constant=lambda _value: (_ for _ in ()).throw(ValueError()),
            )
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
            raise TransportInvalidResponseError("invalid JSON response") from None
