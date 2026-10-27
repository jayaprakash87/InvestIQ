"""SEC EDGAR submissions listing adapter.

Requires an operator-declared User-Agent and obeys an instance-level request
interval. This provider returns filing metadata, not financial XBRL facts.
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import Callable
from datetime import UTC, date, datetime
from typing import Any

from ..fundamentals import FilingReference
from ..ports import (
    DataCapability,
    FilingRequest,
    ProviderCapabilities,
    ProviderFailure,
    ProviderFailureCode,
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

SEC_SUBMISSIONS_ORIGIN = "https://data.sec.gov/submissions/"


class SecEdgarFilingProvider:
    """Read the 'recent' filings array for a known, explicitly supplied SEC CIK.

    Historical pagination (files[]), Companyfacts and issuer lookup are outside
    PR 2. Limit is capped by the FilingRequest contract, not a global crawler.
    """

    capabilities = ProviderCapabilities("SEC EDGAR", frozenset({DataCapability.FILINGS}))

    def __init__(
        self,
        *,
        user_agent: str,
        transport: JsonTransport | None = None,
        clock: Callable[[], datetime] | None = None,
        min_interval_seconds: float = 1.0,
    ) -> None:
        if (
            not isinstance(user_agent, str)
            or not 8 <= len(user_agent) <= 200
            or "\n" in user_agent
            or "\r" in user_agent
            or "@" not in user_agent
            or not user_agent.isascii()
        ):
            raise ValueError("SEC requires a declared contact User-Agent (name and email)")
        if not isinstance(min_interval_seconds, (int, float)) or not (
            0.2 <= min_interval_seconds <= 60
        ):
            raise ValueError("SEC min_interval_seconds must be between 0.2 and 60")
        self._user_agent = user_agent
        self._transport = transport if transport is not None else UrllibJsonTransport()
        self._clock = clock or (lambda: datetime.now(UTC))
        self._interval = float(min_interval_seconds)
        self._lock = asyncio.Lock()
        self._last_request: float | None = None

    async def list_filings(self, request: FilingRequest) -> tuple[FilingReference, ...]:
        if not isinstance(request, FilingRequest):
            raise TypeError("request must be FilingRequest")
        issuer = request.issuer
        if issuer.namespace != "SEC_CIK" or re.fullmatch(r"[0-9]{1,10}", issuer.value) is None:
            raise ProviderFailure(
                "SEC EDGAR", ProviderFailureCode.UNSUPPORTED_INSTRUMENT,
                "Only explicit numeric SEC CIK issuer IDs are supported",
            )
        cik = int(issuer.value)
        if cik == 0:
            raise ProviderFailure(
                "SEC EDGAR", ProviderFailureCode.UNSUPPORTED_INSTRUMENT,
                "SEC CIK must be nonzero",
            )
        url = f"{SEC_SUBMISSIONS_ORIGIN}CIK{cik:010d}.json"
        # Rate-limit across concurrent calls on this instance; do not claim
        # global, multi-process / shared-IP compliance.
        async with self._lock:
            loop = asyncio.get_running_loop()
            if self._last_request is not None:
                wait = self._interval - (loop.time() - self._last_request)
                if wait > 0:
                    await asyncio.sleep(wait)
            self._last_request = loop.time()
            try:
                payload = await self._transport.get_json(
                    url, headers={"User-Agent": self._user_agent}
                )
            except (
                TransportStatusError,
                TransportTimeoutError,
                TransportUnavailableError,
                TransportInvalidResponseError,
            ) as exc:
                raise translate_error("SEC EDGAR", exc) from None
        retrieved = self._clock()
        if (
            not isinstance(retrieved, datetime)
            or retrieved.tzinfo is None
            or retrieved.utcoffset() is None
        ):
            raise ValueError("clock must provide timezone-aware datetime")
        try:
            return _parse_recent(payload, issuer, cik, retrieved, request.limit, url)
        except (ValueError, TypeError, KeyError, IndexError):
            raise ProviderFailure(
                "SEC EDGAR", ProviderFailureCode.INVALID_RESPONSE,
                "SEC EDGAR submissions schema is invalid",
            ) from None


def _parse_recent(
    payload: Any, issuer, cik: int, received: datetime, limit: int, url: str
) -> tuple[FilingReference, ...]:
    if not isinstance(payload, dict):
        raise TypeError("expected object")
    actual = payload.get("cik")
    # SEC submissions CIK may be a string (with leading zeros) or an integer.
    # Never accept booleans or nonnumeric/truncated identifiers.
    if type(actual) is int:
        normalized_cik = actual
    elif isinstance(actual, str) and re.fullmatch(r"[0-9]{1,10}", actual):
        normalized_cik = int(actual)
    else:
        raise ValueError("invalid SEC CIK type or format")
    if normalized_cik != cik:
        raise ValueError("CIK mismatch")
    filings = payload["filings"]
    if not isinstance(filings, dict):
        raise TypeError("filings must be an object")
    recent = filings["recent"]
    if not isinstance(recent, dict):
        raise TypeError("recent must be an object")
    accessions = recent["accessionNumber"]
    forms = recent["form"]
    dates = recent["filingDate"]
    if not all(isinstance(v, list) for v in (accessions, forms, dates)):
        raise ValueError("recent fields must be arrays")
    if not len(accessions) == len(forms) == len(dates):
        raise ValueError("filing arrays misaligned")
    result: list[FilingReference] = []
    seen: set[str] = set()
    for accession, form, filed in zip(accessions, forms, dates):
        if not isinstance(accession, str) or not re.fullmatch(r"[0-9]{10}-[0-9]{2}-[0-9]{6}", accession):
            raise ValueError("bad accession number")
        if accession in seen:
            raise ValueError("duplicate accession")
        seen.add(accession)
        if not isinstance(form, str) or not form.strip():
            raise ValueError("invalid form")
        if not isinstance(filed, str):
            raise TypeError("invalid filing date")
        filed_on = date.fromisoformat(filed)
        result.append(
            FilingReference(
                issuer=issuer,
                accession=accession,
                form=form,
                filed_on=filed_on,
                source_reference=f"{url}#accession={accession}",
                retrieved_at=received,
                # A SEC filing date or acceptance timestamp is NOT independent
                # proof of exact public dissemination.
                publicly_available_at=None,
            )
        )
        if len(result) >= limit:
            break
    return tuple(result)
