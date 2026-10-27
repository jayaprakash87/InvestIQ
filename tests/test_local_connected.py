"""PR 2: SEC issuer candidates, session-bound endpoints and verified data boundaries."""

from __future__ import annotations

import http.client
import json
import threading
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from investiq_core.issuer_directory import parse_directory, search_candidates
from investiq_core.local_connected import LocalConnectedResearch
from investiq_core.market import (
    MarketQuote,
    MarketSession,
    PriceAdjustment,
    QuoteFreshness,
    QuoteKind,
    QuoteTimeliness,
)
from investiq_core.ports import ProviderFailure, ProviderFailureCode
from investiq_core.webapp import create_app_server

DIRECTORY = {
    "fields": ["cik", "name", "ticker", "exchange"],
    "data": [
        [12345, "Example Industries", "EXM", "Nasdaq"],
        [67890, "Example Partners", "EPR", "NYSE"],
        [22222, "Not Supported", "OTH", "NYSE American"],
    ],
}


class FakeDirectoryTransport:
    def __init__(self, payload=None):
        self.payload = DIRECTORY if payload is None else payload
        self.calls = 0
        self.headers = []

    async def get_json(self, url, *, headers):
        assert url == "https://www.sec.gov/files/company_tickers_exchange.json"
        self.calls += 1
        self.headers.append(headers)
        return self.payload


class FakeResearchService:
    def __init__(self):
        self.calls = []

    async def analyze(self, request, *, refresh=False):
        self.calls.append((request, refresh))
        time = datetime.now(UTC) - timedelta(minutes=2)
        quote = MarketQuote(
            quote_id="synthetic:quote", instrument=request.listing.instrument,
            provider="Synthetic injected test provider",
            provider_symbol=request.listing.instrument.ticker,
            source_reference="synthetic:connected-quote", kind=QuoteKind.CLOSE,
            price=Decimal("75.00"), currency="USD",
            event_at=time, received_at=datetime.now(UTC),
            session=MarketSession.UNKNOWN, timeliness=QuoteTimeliness.UNKNOWN,
            entitlement_scope="synthetic:session",
            adjustment=PriceAdjustment.UNKNOWN,
        )
        return SimpleNamespace(
            issuer=request.listing.issuer.value,
            quote=SimpleNamespace(quote=quote, freshness=QuoteFreshness.WITHIN_POLICY),
            annual_facts=(),
            annual_pe_proxy=None,
            warnings=("Synthetic test only",),
        )


@dataclass
class Harness:
    port: int
    connected: LocalConnectedResearch
    directory: FakeDirectoryTransport
    research: FakeResearchService
    server: object


@pytest.fixture
def harness():
    directory = FakeDirectoryTransport()
    research = FakeResearchService()
    connected = LocalConnectedResearch(
        directory_transport=directory, research_factory=lambda contact, key: research
    )
    server = create_app_server(0, connected=connected)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield Harness(server.server_port, connected, directory, research, server)
    finally:
        server.shutdown()
        thread.join(timeout=4)
        server.server_close()
        assert not thread.is_alive()


def request(harness, method, path, data=None, *, cookie=None, csrf=None, origin=True):
    connection = http.client.HTTPConnection("127.0.0.1", harness.port, timeout=5)
    headers = {"Host": f"127.0.0.1:{harness.port}"}
    if origin:
        headers["Origin"] = f"http://127.0.0.1:{harness.port}"
    if cookie:
        headers["Cookie"] = cookie
    if csrf:
        headers["X-InvestIQ-CSRF"] = csrf
    if data is not None:
        headers["Content-Type"] = "application/json"
        raw = json.dumps(data).encode("utf-8")
    else:
        raw = None
    try:
        connection.request(method, path, body=raw, headers=headers)
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), json.loads(response.read())
    finally:
        connection.close()


def initialize(harness):
    code, headers, payload = request(harness, "GET", "/api/v1/session", origin=False)
    assert code == 200
    return headers["Set-Cookie"].split(";", 1)[0], payload["csrf"], headers, payload


def configure(harness, cookie, csrf, key="test_key_fake"):
    return request(
        harness, "POST", "/api/v1/session/configure",
        {"sec_contact": "InvestIQ Test research@example.com", "twelve_data_api_key": key},
        cookie=cookie, csrf=csrf,
    )


def test_sec_directory_candidates_are_not_verified_listings():
    items = parse_directory(DIRECTORY, observed_at=datetime.now(UTC))
    assert len(items) == 2
    assert {item.venue for item in items} == {"XNAS", "XNYS"}
    assert all(item.currency_candidate == "USD" for item in items)
    assert all("candidate_requires" in item.public_record()["status"] for item in items)
    assert search_candidates(items, "EXM")[0].cik == "0000012345"
    assert len(search_candidates(items, "example")) == 2
    assert not search_candidates(items, "unsupported")
    with pytest.raises(ValueError, match="2"):
        search_candidates(items, "E")
    conflicting = {
        "fields": DIRECTORY["fields"],
        "data": [
            [1, "A", "EXM", "Nasdaq"],
            [2, "B", "EXM", "Nasdaq"],
        ],
    }
    with pytest.raises(ValueError, match="Conflicting"):
        parse_directory(conflicting, observed_at=datetime.now(UTC))


def test_session_cookie_and_csrf_are_required_for_all_connected_requests(harness):
    cookie, csrf, headers, initial = initialize(harness)
    assert "HttpOnly" in headers["Set-Cookie"]
    assert "SameSite=Strict" in headers["Set-Cookie"]
    assert headers["Cache-Control"] == "no-store"
    assert initial["configured"] is False
    assert initial["credentials_persisted"] is False
    assert len(csrf) >= 30
    code, _, _ = request(harness, "POST", "/api/v1/session/configure", {}, csrf=csrf)
    assert code == 403
    code, _, _ = request(harness, "POST", "/api/v1/session/configure", {}, cookie=cookie)
    assert code == 403
    code, _, _ = request(
        harness, "POST", "/api/v1/session/configure", {}, cookie=cookie,
        csrf=csrf, origin=False,
    )
    assert code == 403
    code, _, _ = request(
        harness, "POST", "/api/v1/session/configure", {},
        cookie=cookie, csrf="wrong",
    )
    assert code == 403


def test_connected_search_and_research_requires_confirmation_and_is_unsaved(harness):
    cookie, csrf, _, _ = initialize(harness)
    code, _, _ = request(
        harness, "POST", "/api/v1/companies/search", {"query": "EXM"},
        cookie=cookie, csrf=csrf,
    )
    assert code == 403
    code, _, configured = configure(harness, cookie, csrf)
    assert code == 200
    assert configured == {
        "configured": True, "credentials_persisted": False, "network_called": False
    }
    code, _, payload = request(
        harness, "POST", "/api/v1/companies/search", {"query": "EXM"},
        cookie=cookie, csrf=csrf,
    )
    assert code == 200
    assert payload["status"] == "candidate_only"
    assert len(payload["companies"]) == 1
    assert payload["companies"][0]["cik"] == "0000012345"
    assert harness.directory.calls == 1
    assert harness.directory.headers[0]["User-Agent"].startswith("InvestIQ Test")
    code, _, _ = request(
        harness, "POST", "/api/v1/companies/search", {"query": "EPR"},
        cookie=cookie, csrf=csrf,
    )
    assert code == 200
    assert harness.directory.calls == 1  # per-session memory, no re-fetch for keystrokes

    chosen = {
        "symbol": "EXM", "venue": "XNAS", "cik": "0000012345",
        "currency": "USD", "confirm_current_listing": True,
        "confirm_currency": True, "max_quote_age_minutes": 120,
    }
    for bad in (
        {**chosen, "confirm_currency": False},
        {**chosen, "confirm_current_listing": False},
        {**chosen, "cik": "0000012346"},
        {**chosen, "symbol": "UNKN"},
        {**chosen, "currency": "EUR"},
        {**chosen, "max_quote_age_minutes": 0},
    ):
        code, _, _ = request(
            harness, "POST", "/api/v1/research/connected", bad,
            cookie=cookie, csrf=csrf,
        )
        assert code == 400
    assert not harness.research.calls

    code, _, research = request(
        harness, "POST", "/api/v1/research/connected", chosen,
        cookie=cookie, csrf=csrf,
    )
    assert code == 200
    assert research["mode"] == "connected_current_view_not_saved"
    assert research["model_executed"] is False
    assert research["credentials_persisted"] is False
    assert research["research_saved"] is False
    assert research["reported_annual_pe_proxy"] is None
    assert research["quote"]["timeliness"] == "unknown"
    assert research["quote"]["snapshot_right"] == "unknown"
    assert research["quote"]["price"] == "75.00"
    assert research["listing_status"].startswith("current_SEC_candidate")
    req, refresh = harness.research.calls[0]
    assert refresh is True
    assert req.analyst_confirmed_share_basis is False
    assert req.listing.instrument.venue == "XNAS"

    code, _, cleared = request(
        harness, "POST", "/api/v1/session/clear", {},
        cookie=cookie, csrf=csrf,
    )
    assert code == 200
    assert cleared["configured"] is False
    code, _, _ = request(
        harness, "POST", "/api/v1/companies/search", {"query": "EXM"},
        cookie=cookie, csrf=csrf,
    )
    assert code == 403


def test_invalid_inputs_fail_before_fetch_and_never_echo_key(harness):
    cookie, csrf, _, _ = initialize(harness)
    secret = "secret_api_token_never_echo"
    code, _, err = configure(harness, cookie, csrf, key=secret + "\n")
    assert code == 400
    assert secret not in json.dumps(err)
    code, _, _ = configure(harness, cookie, csrf)
    assert code == 200
    code, _, result = request(
        harness, "POST", "/api/v1/companies/search", {"query": "x"},
        cookie=cookie, csrf=csrf,
    )
    assert code == 400
    assert harness.directory.calls == 0
    assert secret not in json.dumps(result)


def test_provider_failure_is_categorized_without_secrets(harness):
    cookie, csrf, _, _ = initialize(harness)
    assert configure(harness, cookie, csrf)[0] == 200
    original = harness.connected._directory_transport

    class Denied:
        async def get_json(self, url, *, headers):
            from investiq_core.adapters._http import TransportStatusError
            raise TransportStatusError(403)

    harness.connected._directory_transport = Denied()
    code, _, err = request(
        harness, "POST", "/api/v1/companies/search", {"query": "EXM"},
        cookie=cookie, csrf=csrf,
    )
    assert code == 502
    assert err["code"] in {"entitlement_denied", "unauthorized", "invalid_response"}
    assert "test_key_fake" not in json.dumps(err)
    harness.connected._directory_transport = original


def test_app_does_not_require_connection_for_existing_synthetic_demo(harness):
    status, _, payload = request(harness, "GET", "/api/v1/demo", origin=False)
    assert status == 200
    assert payload["mode"] == "synthetic"
    assert payload["bundle"]["synthetic"] is True
    assert harness.directory.calls == 0
    assert harness.research.calls == []


def test_registry_bad_shapes_are_not_silently_interpreted():
    for bad in (None, [], {}, {"fields": [], "data": []},
                {"fields": DIRECTORY["fields"], "data": [[True, "A", "A", "NYSE"]]}):
        with pytest.raises((TypeError, ValueError)):
            parse_directory(bad, observed_at=datetime.now(UTC))
