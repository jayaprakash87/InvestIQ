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
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from .adapters._http import JsonTransport
from .adapters.sec_companyfacts import SecCompanyFactsProvider
from .adapters.sec_edgar import SecEdgarFilingProvider
from .adapters.twelve_data import TwelveDataQuoteProvider
from .ai_research import (
    ALLOWED_MODELS,
    AiResearchCoordinator,
    OpenAIResponseModel,
    default_ai_coordinator,
)
from .application.connected_data import ConnectedDataService
from .application.connected_research import CompanyResearchRequest, ConnectedResearchService
from .browser_decisions import BrowserDecisionHistory
from .connected_cli import _render_current
from .evidence import InstrumentId
from .filing_evidence import SecFilingEvidenceProvider
from .interactive_scenarios import evaluate_hypothetical
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
    model_key: str | None = None
    model_name: str | None = None
    history_unlocked: bool = False
    directory: tuple[IssuerCandidate, ...] = ()
    directory_refreshed_at: float | None = None
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    @property
    def configured(self) -> bool:
        return self.contact is not None

    @property
    def quote_configured(self) -> bool:
        return self.contact is not None and self.quote_key is not None

    @property
    def model_configured(self) -> bool:
        return self.contact is not None and self.model_key is not None


class LocalConnectedResearch:
    """Small, session-only boundary; external I/O is explicit and injectable."""

    def __init__(
        self,
        *,
        directory_transport: JsonTransport | None = None,
        research_factory: Callable[[str, str], ConnectedResearchService] | None = None,
        evidence_factory: Callable[[str], SecFilingEvidenceProvider] | None = None,
        ai_coordinator: AiResearchCoordinator | None = None,
        decision_dir: Path | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._sessions: dict[str, BrowserSession] = {}
        self._mutex = threading.Lock()
        self._clock = clock
        self._directory_transport = directory_transport
        self._ai = ai_coordinator or default_ai_coordinator()
        self._decisions = BrowserDecisionHistory(decision_dir)
        self._history_code = secrets.token_urlsafe(24) if self._decisions.enabled else None
        self._research_factory = research_factory or _build_research_service
        self._evidence_factory = evidence_factory or (
            lambda contact: SecFilingEvidenceProvider(user_agent=contact)
        )

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
            "quote_configured": session.quote_configured,
            "model_configured": session.model_configured,
            "model_name": session.model_name,
            "credentials_persisted": False,
            "csrf": session.csrf,
            "directory_loaded": session.directory_refreshed_at is not None,
            "private_history_unlocked": session.history_unlocked,
        }

    @staticmethod
    def configure(session: BrowserSession, data: dict[str, Any]) -> dict[str, Any]:
        contact = data.get("sec_contact")
        key = data.get("twelve_data_api_key")
        if not isinstance(contact, str) or key is not None and not isinstance(key, str):
            raise TypeError("SEC contact is required; quote key must be a string if supplied")
        if not 8 <= len(contact) <= 200 or (
            isinstance(key, str) and len(key) > 256
        ):
            raise ValueError("Provider credentials do not meet supported length limits")
        # SEC directory and public-filing AI research do not require paid
        # quote credentials. Quote analysis still fails closed without BYOK.
        SecEdgarFilingProvider(user_agent=contact)
        if key:
            TwelveDataQuoteProvider(api_key=key)
        with session.lock:
            session.contact = contact
            session.quote_key = key or None
            session.directory = ()
            session.directory_refreshed_at = None
        return {
            "configured": True,
            "quote_configured": bool(key),
            "credentials_persisted": False,
            "network_called": False,
        }

    @staticmethod
    def clear(session: BrowserSession) -> dict[str, Any]:
        with session.lock:
            session.contact = None
            session.quote_key = None
            session.model_key = None
            session.model_name = None
            session.history_unlocked = False
            session.directory = ()
            session.directory_refreshed_at = None
        return {
            "configured": False, "quote_configured": False,
            "model_configured": False, "credentials_persisted": False,
        }

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

    @staticmethod
    def configure_model(session: BrowserSession, data: dict[str, Any]) -> dict[str, Any]:
        """Store a BYOK credential for this one local-server session only."""
        key = data.get("model_api_key")
        model = data.get("model", "gpt-4.1-mini")
        # Validate without requesting the external service.
        OpenAIResponseModel(api_key=key, model=model)
        with session.lock:
            if not session.configured:
                raise PermissionError("Configure SEC contact before model access")
            session.model_key = key
            session.model_name = model
        return {
            "model_configured": True, "model_name": model,
            "credentials_persisted": False, "network_called": False,
        }

    @staticmethod
    def clear_model(session: BrowserSession) -> dict[str, Any]:
        with session.lock:
            session.model_key = None
            session.model_name = None
        return {"model_configured": False, "credentials_persisted": False}

    def ai_analyze(self, session: BrowserSession, data: dict[str, Any]) -> dict[str, Any]:
        """One explicit authorized call, with SEC-only public evidence consent."""
        symbol, venue, cik = (data.get(name) for name in ("symbol", "venue", "cik"))
        question = data.get("question")
        if (
            not isinstance(symbol, str) or not isinstance(venue, str)
            or not isinstance(cik, str)
            or data.get("currency") != "USD"
            or data.get("confirm_current_listing") is not True
            or data.get("confirm_currency") is not True
            or data.get("consent_external_sec_data") is not True
            or not isinstance(question, str) or not 5 <= len(question.strip()) <= 360
        ):
            raise ValueError("Select and confirm an issuer; question and consent required")
        with session.lock:
            if (
                not session.configured or session.contact is None
                or session.model_key is None or session.model_name not in ALLOWED_MODELS
            ):
                raise PermissionError("Configure the SEC and model sessions first")
            if (
                session.directory_refreshed_at is None
                or self._clock() - session.directory_refreshed_at > DIRECTORY_LIFETIME_SECONDS
            ):
                raise ValueError("Company directory expired; search and confirm again")
            candidates = [
                item for item in session.directory
                if (item.symbol, item.venue, item.cik) == (symbol, venue, cik)
            ]
            if len(candidates) != 1:
                raise ValueError("Selected listing is not an active directory candidate")
            # Lock prevents clearance or credential rotation during processing.
            return asyncio.run(self._ai.run(
                cik=cik, contact=session.contact, model_key=session.model_key,
                model_name=session.model_name, question=question.strip(),
            ))

    def history_available(self) -> bool:
        return self._decisions.enabled

    @property
    def history_access_code(self) -> str | None:
        """Ephemeral launch-terminal capability, never exposed via HTTP."""
        return self._history_code

    def unlock_history(self, session: BrowserSession, data: dict[str, Any]) -> dict[str, bool]:
        if not self._decisions.enabled or self._history_code is None:
            raise PermissionError("Private history is disabled")
        if not isinstance(data, dict) or set(data) != {"code"}:
            raise PermissionError("Invalid private history authorization")
        supplied = data["code"]
        if (
            not isinstance(supplied, str) or len(supplied) > 128
            or not secrets.compare_digest(supplied, self._history_code)
        ):
            raise PermissionError("Invalid private history authorization")
        with session.lock:
            session.history_unlocked = True
        return {"private_history_unlocked": True}

    @staticmethod
    def _require_history_unlock(session: BrowserSession) -> None:
        if not session.history_unlocked:
            raise PermissionError("Unlock private history using the launch-terminal code")

    def list_decisions(self, session: BrowserSession) -> dict[str, Any]:
        with session.lock:
            self._require_history_unlock(session)
            return self._decisions.list()

    def open_decision(
        self, session: BrowserSession, data: dict[str, Any]
    ) -> dict[str, Any]:
        with session.lock:
            self._require_history_unlock(session)
            return self._decisions.load(data.get("thesis_id"), data.get("revision"))

    def export_decision(
        self, session: BrowserSession, data: dict[str, Any]
    ) -> dict[str, str]:
        with session.lock:
            self._require_history_unlock(session)
            return self._decisions.export(
                data.get("thesis_id"), data.get("revision"), data.get("format"),
            )

    def save_decision(
        self, session: BrowserSession, data: dict[str, Any]
    ) -> dict[str, Any]:
        symbol, venue, cik = (data.get(name) for name in ("symbol", "venue", "cik"))
        if (
            not isinstance(symbol, str) or not isinstance(venue, str)
            or not isinstance(cik, str) or data.get("currency") != "USD"
            or data.get("confirm_current_listing") is not True
            or data.get("confirm_currency") is not True
            or data.get("approve_private_save") is not True
            or set(data) != {
                "symbol", "venue", "cik", "currency", "confirm_current_listing",
                "confirm_currency", "approve_private_save", "decision",
            }
        ):
            raise ValueError("Explicit save requires a confirmed issuer and decision")
        with session.lock:
            self._require_history_unlock(session)
            if not session.configured:
                raise PermissionError("Configure SEC discovery first")
            if (
                session.directory_refreshed_at is None
                or self._clock() - session.directory_refreshed_at > DIRECTORY_LIFETIME_SECONDS
            ):
                raise ValueError("Issuer directory expired; search again")
            if sum(
                (item.symbol, item.venue, item.cik) == (symbol, venue, cik)
                for item in session.directory
            ) != 1:
                raise ValueError("Issuer is not the selected directory candidate")
            return self._decisions.save(
                symbol=symbol, venue=venue, cik=cik, data=data["decision"],
            )

    def preview_scenarios(
        self, session: BrowserSession, data: dict[str, Any]
    ) -> dict[str, Any]:
        """User-authored calculation, independently of model and market providers."""
        symbol, venue, cik = (data.get(name) for name in ("symbol", "venue", "cik"))
        if (
            not isinstance(symbol, str) or not isinstance(venue, str)
            or not isinstance(cik, str) or data.get("currency") != "USD"
            or data.get("confirm_current_listing") is not True
            or data.get("confirm_currency") is not True
        ):
            raise ValueError("Confirm the supported listing and USD currency")
        with session.lock:
            if not session.configured:
                raise PermissionError("Configure SEC discovery and select an issuer first")
            if (
                session.directory_refreshed_at is None
                or self._clock() - session.directory_refreshed_at > DIRECTORY_LIFETIME_SECONDS
            ):
                raise ValueError("Company selection expired; search and confirm again")
            if sum(
                (item.symbol, item.venue, item.cik) == (symbol, venue, cik)
                for item in session.directory
            ) != 1:
                raise ValueError("Issuer selection is not a current directory candidate")
            result = evaluate_hypothetical(data.get("hypothetical"))
            result["selection"] = {
                "symbol": symbol, "venue": venue, "cik": cik,
                "selection_type": "directory_candidate_user_confirmed_not_verified_basis",
            }
            return result

    def inspect_evidence(
        self, session: BrowserSession, data: dict[str, Any]
    ) -> dict[str, Any]:
        """On-demand 10-K excerpts for a confirmed directory candidate.

        Never fetch arbitrary CIK, path or supplied URL; require matching
        candidate, directory TTL and current listing/currency confirmation.
        """
        symbol, venue, cik = (data.get(name) for name in ("symbol", "venue", "cik"))
        topic = data.get("topic")
        if (
            not isinstance(symbol, str) or not isinstance(venue, str)
            or not isinstance(cik, str)
            or topic not in ("business", "risks", "management")
            or data.get("currency") != "USD"
            or data.get("confirm_current_listing") is not True
            or data.get("confirm_currency") is not True
        ):
            raise ValueError("Confirm supported listing and evidence topic")
        with session.lock:
            if not session.configured or session.contact is None:
                raise PermissionError("Configure your authorized provider session first")
            if (
                session.directory_refreshed_at is None
                or self._clock() - session.directory_refreshed_at > DIRECTORY_LIFETIME_SECONDS
            ):
                raise ValueError("Company directory expired; search and confirm again")
            matches = [
                item for item in session.directory
                if (item.symbol, item.venue, item.cik) == (symbol, venue, cik)
            ]
            if len(matches) != 1:
                raise ValueError("Listing is not in the current SEC directory")
            issuer = IssuerId("SEC_CIK", matches[0].cik)
            return asyncio.run(self._evidence_factory(session.contact).inspect(
                issuer, topic=topic
            ))

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
