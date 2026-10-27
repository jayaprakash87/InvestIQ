"""Session-scoped local connected research application service.

No startup network access, persistent credentials, quote cache, issuer history,
password store or multi-user account model. An individual browser session must
configure a provider explicitly before each server lifetime's connected use.
"""

from __future__ import annotations

import asyncio
import secrets
import threading
import time
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any, Callable

from .adapters._http import JsonTransport
from .adapters.sec_companyfacts import SecCompanyFactsProvider
from .adapters.sec_edgar import SecEdgarFilingProvider
from .adapters.twelve_data import TwelveDataQuoteProvider
from .application.connected_data import ConnectedDataService
from .application.connected_research import CompanyResearchRequest, ConnectedResearchService
from .connected_cli import _render_current
from .evidence import InstrumentId
from .issuer_directory import IssuerCandidate, SecDirectoryProvider, search_candidates
from .market import IssuerId, IssuerListing

SESSION_LIFETIME_SECONDS = 60 * 60
DIRECTORY_LIFETIME_SECONDS = 15 * 60
MAX_SESSIONS = 8


@dataclass(slots=True)
class BrowserSession:
    csrf: str
    created_at: float
    contact: str | None = None
    quote_key: str | None = None
    directory: tuple[IssuerCandidate, ...] = ()
    directory_refreshed_at: float | None = None
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    @property
    def configured(self) -> bool:
        return self.contact is not None and self.quote_key is not None


class LocalConnectedResearch:
    """Small, session-only boundary; external I/O is explicit and injectable."""

    def __init__(
        self,
        *,
        directory_transport: JsonTransport | None = None,
        research_factory: Callable[[str, str], ConnectedResearchService] | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._sessions: dict[str, BrowserSession] = {}
        self._mutex = threading.Lock()
        self._clock = clock
        self._directory_transport = directory_transport
        self._research_factory = research_factory or _build_research_service

    def session(self, session_id: str | None, *, create: bool) -> tuple[str, BrowserSession] | None:
        now = self._clock()
        with self._mutex:
            for key, old in tuple(self._sessions.items()):
                if now - old.created_at >= SESSION_LIFETIME_SECONDS:
                    self._sessions.pop(key, None)
            if session_id in self._sessions:
                return session_id, self._sessions[session_id]
            if not create:
                return None
            if len(self._sessions) >= MAX_SESSIONS:
                # Never evict another session that may hold a pending request.
                return None
            new_id = secrets.token_urlsafe(32)
            result = BrowserSession(csrf=secrets.token_urlsafe(32), created_at=now)
            self._sessions[new_id] = result
            return new_id, result

    @staticmethod
    def session_status(session: BrowserSession) -> dict[str, Any]:
        return {
            "mode": "local_session",
            "configured": session.configured,
            "credentials_persisted": False,
            "csrf": session.csrf,
            "directory_loaded": session.directory_refreshed_at is not None,
        }

    @staticmethod
    def configure(session: BrowserSession, data: dict[str, Any]) -> dict[str, Any]:
        contact = data.get("sec_contact")
        key = data.get("twelve_data_api_key")
        if not isinstance(contact, str) or not isinstance(key, str):
            raise ValueError("SEC contact and Twelve Data API key are required")
        if not 8 <= len(contact) <= 200 or not 1 <= len(key) <= 256:
            raise ValueError("Provider credentials do not meet supported length limits")
        # Validate syntactic contracts with existing providers, WITHOUT network I/O.
        SecEdgarFilingProvider(user_agent=contact)
        TwelveDataQuoteProvider(api_key=key)
        with session.lock:
            session.contact = contact
            session.quote_key = key
            session.directory = ()
            session.directory_refreshed_at = None
        return {"configured": True, "credentials_persisted": False, "network_called": False}

    @staticmethod
    def clear(session: BrowserSession) -> dict[str, Any]:
        with session.lock:
            session.contact = None
            session.quote_key = None
            session.directory = ()
            session.directory_refreshed_at = None
        return {"configured": False, "credentials_persisted": False}

    def search(self, session: BrowserSession, data: dict[str, Any]) -> dict[str, Any]:
        query = data.get("query")
        # Fail without network on invalid input.
        if not isinstance(query, str) or not 2 <= len(query.strip()) <= 80:
            raise ValueError("Search for a company name or symbol (2–80 characters)")
        with session.lock:
            if not session.configured or session.contact is None:
                raise PermissionError("Configure your authorized provider session first")
            now = self._clock()
            if (
                session.directory_refreshed_at is None
                or now - session.directory_refreshed_at > DIRECTORY_LIFETIME_SECONDS
            ):
                session.directory = asyncio.run(
                    SecDirectoryProvider(
                        user_agent=session.contact, transport=self._directory_transport
                    ).load()
                )
                session.directory_refreshed_at = self._clock()
            matches = search_candidates(session.directory, query)
            observed = session.directory[0].observed_at if session.directory else None
            return {
                "status": "candidate_only",
                "source": "SEC company_tickers_exchange",
                "observed_at": observed.isoformat() if observed else None,
                "companies": [item.public_record() for item in matches],
                "warnings": [
                    "Issuer directory is not a verified historical listing ledger.",
                    "Only Nasdaq and NYSE issuer candidates are supported initially.",
                    "You must confirm current listing and proposed USD currency.",
                ],
            }

    def analyze(self, session: BrowserSession, data: dict[str, Any]) -> dict[str, Any]:
        symbol, venue, cik = (data.get(name) for name in ("symbol", "venue", "cik"))
        age = data.get("max_quote_age_minutes")
        if (
            not isinstance(symbol, str)
            or not isinstance(venue, str)
            or not isinstance(cik, str)
            or data.get("currency") != "USD"
            or data.get("confirm_current_listing") is not True
            or data.get("confirm_currency") is not True
            or type(age) is not int
            or not 1 <= age <= 1440
        ):
            raise ValueError("Confirm a supported listing and currency and choose quote age (1–1440 min)")
        with session.lock:
            if not session.configured or session.contact is None or session.quote_key is None:
                raise PermissionError("Configure your authorized provider session first")
            if (
                session.directory_refreshed_at is None
                or self._clock() - session.directory_refreshed_at > DIRECTORY_LIFETIME_SECONDS
            ):
                raise ValueError("Company directory expired; search and verify the listing again")
            matches = [
                item for item in session.directory
                if (item.symbol, item.venue, item.cik) == (symbol, venue, cik)
            ]
            if len(matches) != 1:
                raise ValueError("Listing is not in the current SEC directory; search again")
            item = matches[0]
            if item.observed_at.astimezone(UTC).date() > datetime.now(UTC).date():
                raise ValueError("Invalid future SEC directory observation")
            # The directory timestamp is ONLY when it was observed. It does not
            # prove when the listing started or which share basis EPS represents.
            listing = IssuerListing(
                issuer=IssuerId("SEC_CIK", item.cik),
                instrument=InstrumentId(item.symbol, item.venue, "USD"),
                effective_from=item.observed_at.astimezone(UTC).date(),
                source_reference=item.source + " (current candidate, user confirmed)",
                verified_at=datetime.now(UTC),
            )
            request = CompanyResearchRequest(
                listing=listing,
                max_quote_age=timedelta(minutes=age),
                analyst_confirmed_share_basis=False,
                share_basis_rationale=None,
            )
            result = asyncio.run(
                self._research_factory(session.contact, session.quote_key).analyze(
                    request, refresh=True
                )
            )
            payload = _render_current(result)
            payload["listing_status"] = "current_SEC_candidate_confirmed_by_user_not_historical_proof"
            payload["source_directory_at"] = item.observed_at.isoformat()
            payload["model_executed"] = False
            payload["credentials_persisted"] = False
            payload["research_saved"] = False
            payload["warnings"].append(
                "SEC candidate mapping and USD currency were confirmed by the user; "
                "historical listing dates, split/share basis and market entitlement "
                "remain unverified. Annual P/E suppressed without separate basis verification."
            )
            return payload


def _build_research_service(contact: str, key: str) -> ConnectedResearchService:
    data = ConnectedDataService(
        quote_provider=TwelveDataQuoteProvider(api_key=key),
        filing_provider=SecEdgarFilingProvider(user_agent=contact),
        principal_scope="local-session-no-cache",
    )
    return ConnectedResearchService(
        data=data,
        fundamentals=SecCompanyFactsProvider(user_agent=contact),
    )
