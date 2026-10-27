"""Bounded SEC company-directory discovery of *candidate* current US listings.

SEC company_tickers_exchange is a searchable issuer/ticker/exchange crosswalk,
not an exchange entitlement, share-basis confirmation, trading-currency proof
or historical effective-dated listing ledger. Never infer those silently.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from .adapters._errors import translate_error
from .adapters._http import (
    JsonTransport,
    TransportInvalidResponseError,
    TransportStatusError,
    TransportTimeoutError,
    TransportUnavailableError,
    UrllibJsonTransport,
)
from .ports import ProviderFailure, ProviderFailureCode

SEC_DIRECTORY_URL = "https://www.sec.gov/files/company_tickers_exchange.json"
_SUPPORTED_EXCHANGES = {"Nasdaq": "XNAS", "NYSE": "XNYS"}
_FAILURES = (
    TransportInvalidResponseError,
    TransportStatusError,
    TransportTimeoutError,
    TransportUnavailableError,
)


@dataclass(frozen=True, slots=True)
class IssuerCandidate:
    cik: str
    company: str
    symbol: str
    venue: str
    currency_candidate: str
    observed_at: datetime
    source: str = SEC_DIRECTORY_URL

    def public_record(self) -> dict[str, str]:
        return {
            "cik": self.cik,
            "company": self.company,
            "symbol": self.symbol,
            "venue": self.venue,
            "currency_candidate": self.currency_candidate,
            "observed_at": self.observed_at.isoformat(),
            "source": self.source,
            "status": "candidate_requires_listing_and_currency_confirmation",
        }


def parse_directory(payload: Any, *, observed_at: datetime) -> tuple[IssuerCandidate, ...]:
    """Validate registry shape; discard unsupported venues, never guess mappings."""
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError("observed_at must be timezone-aware")
    if not isinstance(payload, dict):
        raise ValueError("SEC directory must be an object")
    fields = payload.get("fields")
    rows = payload.get("data")
    if not isinstance(fields, list) or not all(isinstance(x, str) for x in fields):
        raise ValueError("SEC directory fields must be strings")
    if len(fields) != len(set(fields)) or not set(("cik", "name", "ticker", "exchange")) <= set(fields):
        raise ValueError("SEC directory missing or duplicate required fields")
    if not isinstance(rows, list) or len(rows) > 100_000:
        raise ValueError("SEC directory data has invalid shape/size")
    pos = {name: fields.index(name) for name in ("cik", "name", "ticker", "exchange")}
    results: list[IssuerCandidate] = []
    seen: dict[tuple[str, str], str] = {}
    for row in rows:
        if not isinstance(row, list) or len(row) != len(fields):
            raise ValueError("SEC directory row has invalid shape")
        cik, name, ticker, exchange = (row[pos[key]] for key in pos)
        if exchange not in _SUPPORTED_EXCHANGES:
            continue
        if type(cik) is not int or not 1 <= cik <= 9_999_999_999:
            raise ValueError("SEC directory CIK is invalid")
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 240:
            raise ValueError("SEC directory issuer name is invalid")
        if not isinstance(ticker, str) or re.fullmatch(r"[A-Za-z0-9.\-]{1,18}", ticker) is None:
            raise ValueError("SEC directory ticker is invalid")
        symbol = ticker.upper()
        venue = _SUPPORTED_EXCHANGES[exchange]
        key = (symbol, venue)
        cik_text = f"{cik:010d}"
        if key in seen:
            # Duplicate instrument rows make the issuer association ambiguous.
            if seen[key] != cik_text:
                raise ValueError("Conflicting SEC issuer-to-ticker mappings")
            continue
        seen[key] = cik_text
        results.append(
            IssuerCandidate(
                cik=cik_text,
                company=name.strip(),
                symbol=symbol,
                venue=venue,
                currency_candidate="USD",
                observed_at=observed_at,
            )
        )
    return tuple(results)


def search_candidates(
    catalog: tuple[IssuerCandidate, ...], query: str, *, limit: int = 12
) -> tuple[IssuerCandidate, ...]:
    if not isinstance(query, str) or not 2 <= len(query.strip()) <= 80:
        raise ValueError("Search for a company name or symbol (2–80 characters)")
    if type(limit) is not int or not 1 <= limit <= 30:
        raise ValueError("Search limit must be from 1 to 30")
    search = query.strip().casefold()
    matches = [
        item for item in catalog
        if search in item.company.casefold() or search in item.symbol.casefold()
    ]
    matches.sort(
        key=lambda item: (
            item.symbol.casefold() != search,
            not item.symbol.casefold().startswith(search),
            not item.company.casefold().startswith(search),
            item.company.casefold(),
            item.symbol,
        )
    )
    return tuple(matches[:limit])


class SecDirectoryProvider:
    """One on-demand directory fetch; caller owns session-local cache/pacing."""

    def __init__(self, *, user_agent: str, transport: JsonTransport | None = None) -> None:
        if (
            not isinstance(user_agent, str)
            or not 8 <= len(user_agent) <= 200
            or "@" not in user_agent
            or "\r" in user_agent
            or "\n" in user_agent
            or not user_agent.isascii()
        ):
            raise ValueError("SEC requires a contact name/email User-Agent")
        self._user_agent = user_agent
        self._transport = transport or UrllibJsonTransport(max_bytes=10_000_000)

    async def load(self) -> tuple[IssuerCandidate, ...]:
        try:
            payload = await self._transport.get_json(
                SEC_DIRECTORY_URL, headers={"User-Agent": self._user_agent}
            )
        except _FAILURES as error:
            raise translate_error("SEC company directory", error) from None
        try:
            return parse_directory(payload, observed_at=datetime.now(UTC))
        except (ValueError, TypeError):
            raise ProviderFailure(
                "SEC company directory",
                ProviderFailureCode.INVALID_RESPONSE,
                "SEC company directory response did not pass validation",
            ) from None
