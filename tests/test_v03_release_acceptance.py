"""v0.3 offline release gate: whole local investor journey, not isolated mocks only.

Uses a real loopback HTTP server, CSRF sessions, real research controller,
real AI coordinator/validators, real deterministic scenarios and filesystem
snapshot store. ONLY the issuer/document/fundamentals/model I/O ports are fake.
"""

from __future__ import annotations

import http.client
import json
import threading

import pytest

from investiq_core.ai_research import AiResearchCoordinator
from investiq_core.local_connected import LocalConnectedResearch
from investiq_core.webapp import create_app_server

CIK = "0000012345"
DOCUMENT_URL = (
    "https://www.sec.gov/Archives/edgar/data/12345/"
    "000001234526000007/annual.htm"
)
PASSAGE_ID = "sec:12345-26-000007:200:99aacc"


class FictionalDirectory:
    def __init__(self):
        self.calls = 0

    async def get_json(self, url, *, headers):
        assert url == "https://www.sec.gov/files/company_tickers_exchange.json"
        self.calls += 1
        return {
            "fields": ["cik", "name", "ticker", "exchange"],
            "data": [[12345, "Fictional Components", "EXM", "Nasdaq"]],
        }


class FictionalFiling:
    def __init__(self):
        self.calls = []

    async def inspect(self, issuer, *, topic):
        assert issuer.value == CIK
        self.calls.append(topic)
        return {
            "mode": "filing_passage_inspection_not_ai",
            "topic": topic,
            "document": {
                "form": "10-K", "accession": "0000012345-26-000007",
                "filed_on": "2026-03-04", "source_url": DOCUMENT_URL,
            },
            "passages": [{
                "evidence_id": PASSAGE_ID, "topic": "risks",
                "excerpt": "Fictional customer demand and supplier risks are described.",
                "extracted_start": 200, "extracted_end": 260,
                "excerpt_sha256": "a" * 64,
            }],
            "limitations": ["Fictional keyword passages; not verified sections."],
        }


class EmptyAnnualFacts:
    def __init__(self):
        self.calls = 0

    async def get_annual_metrics(self, request):
        self.calls += 1
        assert request.issuer.value == CIK
        return ()  # Missing facts must not be invented or supplemented with quotes.


class FictionalModel:
    def __init__(self):
        self.calls = []
        self.fabricate_citation = False

    async def generate(self, *, instructions, evidence, question):
        self.calls.append({
            "instructions": instructions, "evidence": evidence, "question": question
        })
        return {
            "overview": "Fictional disclosures mention risks; no financial conclusion follows.",
            "findings": [{
                "claim": "The presented fictional filing describes supplier risks.",
                "evidence_ids": ["sec:invented-source"] if self.fabricate_citation else [PASSAGE_ID],
            }],
            "bear_case": {
                "claim": "A decline in supplier resilience could weaken operations.",
                "evidence_ids": [PASSAGE_ID],
            },
            "open_questions": ["What additional filings establish the exposure?"],
        }


@pytest.fixture
def research_desk(tmp_path):
    directory = FictionalDirectory()
    filing = FictionalFiling()
    fundamentals = EmptyAnnualFacts()
    model = FictionalModel()
    private = tmp_path / "private-decisions"
    coordinator = AiResearchCoordinator(
        evidence_factory=lambda _contact: filing,
        fundamentals_factory=lambda _contact: fundamentals,
        model_factory=lambda _key, _model_name: model,
    )
    connected = LocalConnectedResearch(
        directory_transport=directory,
        evidence_factory=lambda _contact: filing,
        ai_coordinator=coordinator,
        decision_dir=private,
    )
    server = create_app_server(0, connected=connected)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_port, directory, filing, fundamentals, model, private
    finally:
        server.shutdown()
        thread.join(timeout=4)
        server.server_close()
        assert not thread.is_alive()


def request(port, path, *, data=None, cookie=None, csrf=None, method="POST",
            origin=True, referer=None, host=None):
    http = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    headers = {"Host": host or f"127.0.0.1:{port}"}
    if origin:
        headers["Origin"] = f"http://127.0.0.1:{port}"
    if method == "GET" and path == "/api/v1/session":
        headers["X-InvestIQ-Init"] = "1"
    if cookie:
        headers["Cookie"] = cookie
    if csrf:
        headers["X-InvestIQ-CSRF"] = csrf
    if referer:
        headers["Referer"] = referer
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8") if data is not None else None
    if payload is not None:
        headers["Content-Type"] = "application/json"
    try:
        http.request(method, path, body=payload, headers=headers)
        response = http.getresponse()
        body = response.read()
        return response.status, dict(response.getheaders()), json.loads(body)
    finally:
        http.close()


def authenticated(port):
    status, headers, result = request(port, "/api/v1/session", method="GET")
    assert status == 200
    return headers["Set-Cookie"].split(";", 1)[0], result["csrf"], result


def send(port, path, body, cookie, csrf):
    return request(port, path, data=body, cookie=cookie, csrf=csrf)


def selected():
    return {
        "symbol": "EXM", "venue": "XNAS", "cik": CIK, "currency": "USD",
        "confirm_current_listing": True, "confirm_currency": True,
    }


def assumptions():
    return {
        "start_eps": 4.0, "initial_price": 70.0, "years": 5,
        "scenarios": [
            {"name": "bear", "annual_growth_percent": -5,
             "terminal_pe": 10, "weight_percent": 25},
            {"name": "base", "annual_growth_percent": 5,
             "terminal_pe": 15, "weight_percent": 50},
            {"name": "bull", "annual_growth_percent": 15,
             "terminal_pe": 20, "weight_percent": 25},
        ],
    }


def authored():
    return {
        "thesis_id": "issuer_exm", "stage": "watching",
        "statement": "My fictional thesis: source uncertainty remains material.",
        "reason": "First deliberate research note",
        "risks": ["Restricted source coverage", "Execution underperformance"],
        "invalidation_triggers": ["A key contract fails"],
        "hypothetical": assumptions(),
    }


def test_entire_local_research_journey_with_purposeful_save_and_no_provider_leak(research_desk):
    port, directory, filing, fundamentals, model, private = research_desk
    cookie, csrf, initial = authenticated(port)
    assert initial["private_history_enabled"] is True
    assert not private.exists()
    assert directory.calls == 0
    code, _, demo = request(port, "/api/v1/demo", method="GET")
    assert code == 200 and demo["mode"] == "synthetic"
    assert demo["connected"] is False and demo["model_executed"] is False
    assert not private.exists()

    # No discovery, source read, priced calculation or saving without setup.
    assert send(port, "/api/v1/companies/search", {"query": "EXM"}, cookie, csrf)[0] == 403
    assert send(port, "/api/v1/decisions/save", {
        **selected(), "approve_private_save": True, "decision": authored(),
    }, cookie, csrf)[0] == 403
    assert send(port, "/api/v1/session/configure", {
        "sec_contact": "InvestIQ Test researcher@example.org", "twelve_data_api_key": "",
    }, cookie, csrf)[0] == 200
    code, _, found = send(port, "/api/v1/companies/search", {"query": "EXM"}, cookie, csrf)
    assert code == 200
    assert len(found["companies"]) == 1
    assert found["companies"][0]["cik"] == CIK

    assert send(port, "/api/v1/research/connected", {
        **selected(), "max_quote_age_minutes": 60,
    }, cookie, csrf)[0] == 403  # no licensed quote key
    assert send(port, "/api/v1/research/filing-evidence", {
        **selected(), "topic": "risks",
    }, cookie, csrf)[0] == 200
    assert filing.calls == ["risks"]
    code, _, model_status = send(port, "/api/v1/model/configure", {
        "model_api_key": "fictional-secret-token", "model": "gpt-4.1-mini",
    }, cookie, csrf)
    assert code == 200
    assert "fictional-secret-token" not in json.dumps(model_status)
    question = "What might disconfirm the business thesis?"
    prompt = {
        **selected(), "question": question, "consent_external_sec_data": True,
    }
    assert send(port, "/api/v1/research/ai", {
        **prompt, "consent_external_sec_data": False,
    }, cookie, csrf)[0] == 400
    assert send(port, "/api/v1/research/ai", {
        **prompt, "cik": "0000012346",
    }, cookie, csrf)[0] == 400
    assert model.calls == []
    code, _, analysis = send(port, "/api/v1/research/ai", prompt, cookie, csrf)
    assert code == 200
    assert analysis["analysis"]["findings"][0]["evidence_ids"] == [PASSAGE_ID]
    assert analysis["source_records"][PASSAGE_ID]["source_url"] == DOCUMENT_URL
    assert analysis["model_executed"] is True
    assert "fictional-secret-token" not in json.dumps(analysis)
    assert "twelve_data_api_key" not in json.dumps(model.calls)
    assert model.calls[0]["evidence"]["annual_sec_facts"] == []
    assert len(model.calls) == 1

    # Fresh question is a NEW independent request: no previous question or
    # model answer in the second prompt, and explicit consent is mandatory.
    followup = {
        **selected(), "question": "Which risks need primary-source corroboration?",
        "consent_external_sec_data": True,
    }
    code, _, _ = send(port, "/api/v1/research/ai", followup, cookie, csrf)
    assert code == 200
    assert len(model.calls) == 2
    assert question not in json.dumps(model.calls[1])
    assert "Fictional disclosures mention risks" not in json.dumps(model.calls[1])

    code, _, scenarios = send(port, "/api/v1/research/scenarios", {
        **selected(), "hypothetical": assumptions(),
    }, cookie, csrf)
    assert code == 200
    assert scenarios["mode"] == "manual_hypothetical_no_provider_data"
    assert scenarios["weighted_terminal_price"] > 0
    assert len(model.calls) == 2  # scenario calculation did NOT call the model

    # Saving is deliberate. It does not store source text, quote, price/EPS
    # assumptions, computed valuation or AI response; it is a valid offline
    # historical authored decision.
    assert not private.exists()
    code, _, saved = send(port, "/api/v1/decisions/save", {
        **selected(), "approve_private_save": True, "decision": authored(),
    }, cookie, csrf)
    assert code == 200 and saved["revision"] == 1
    code, _, reopened = send(port, "/api/v1/decisions/open", {
        "thesis_id": "issuer_exm", "revision": 1,
    }, cookie, csrf)
    assert code == 200
    assert reopened["statement"] == authored()["statement"]
    assert reopened["replay_numerical_price_analysis"] is False
    code, _, exported = send(port, "/api/v1/decisions/export", {
        "thesis_id": "issuer_exm", "revision": 1, "format": "json",
    }, cookie, csrf)
    assert code == 200
    manifest = json.loads(exported["content"])["payload"]
    assert manifest["quote"] is None and manifest["annual_facts"] == []
    assert manifest["thesis"]["invalidation_triggers"] == ["A key contract fails"]
    assert manifest["scenario_years"] == 5
    assert "start_eps" not in exported["content"]
    assert "initial_price" not in exported["content"]
    assert DOCUMENT_URL not in exported["content"]
    assert "fictional-secret-token" not in exported["content"]

    assert send(port, "/api/v1/session/clear", {}, cookie, csrf)[0] == 200
    # Offline history is accessible after clearing provider credentials.
    assert send(port, "/api/v1/decisions/open", {
        "thesis_id": "issuer_exm", "revision": 1,
    }, cookie, csrf)[0] == 200
    assert directory.calls == 1
    assert filing.calls.count("all") == 2
    assert fundamentals.calls == 2
    assert len(model.calls) == 2


def test_fabricated_model_citation_fails_at_http_boundary_without_saving(research_desk):
    port, directory, filing, fundamentals, model, private = research_desk
    cookie, csrf, _ = authenticated(port)
    assert send(port, "/api/v1/session/configure", {
        "sec_contact": "InvestIQ Test researcher@example.org",
        "twelve_data_api_key": "",
    }, cookie, csrf)[0] == 200
    assert send(port, "/api/v1/companies/search", {
        "query": "EXM",
    }, cookie, csrf)[0] == 200
    assert send(port, "/api/v1/model/configure", {
        "model_api_key": "fictional-secret-token", "model": "gpt-4.1-mini",
    }, cookie, csrf)[0] == 200
    model.fabricate_citation = True
    code, _, payload = send(port, "/api/v1/research/ai", {
        **selected(), "consent_external_sec_data": True,
        "question": "Are there any substantiated disclosures?",
    }, cookie, csrf)
    assert code == 502
    assert payload["code"] == "model_research_unavailable"
    assert "fictional-secret-token" not in json.dumps(payload)
    assert "sec:invented-source" not in json.dumps(payload)
    assert not private.exists()
    assert len(model.calls) == 1
    assert directory.calls == 1 and filing.calls == ["all"]
    assert fundamentals.calls == 1


def test_security_and_input_rejection_for_local_release(research_desk):
    port, directory, filing, _, model, private = research_desk
    cookie, csrf, _ = authenticated(port)
    assert request(port, "/api/v1/decisions/list", data={}, cookie=cookie, csrf=csrf,
                   host="bad.example")[0] == 403
    assert request(port, "/api/v1/decisions/list", data={}, cookie=cookie, csrf=csrf,
                   origin=False)[0] == 403
    assert request(port, "/api/v1/decisions/list", data={}, cookie=cookie)[0] == 403
    assert request(port, "/api/v1/decisions/list", data={}, csrf=csrf)[0] == 403
    assert send(port, "/api/v1/decisions/open", {
        "thesis_id": "../escape", "revision": 1,
    }, cookie, csrf)[0] == 400
    assert send(port, "/api/v1/decisions/open", {
        "thesis_id": "absent", "revision": 1,
    }, cookie, csrf)[0] == 404
    assert not private.joinpath("absent-00000001.json").exists()
    assert directory.calls == 0 and filing.calls == [] and model.calls == []
