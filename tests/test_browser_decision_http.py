"""PR6 HTTP acceptance for opt-in private decisions and offline history."""

from __future__ import annotations

import http.client
import json
import threading

import pytest

from investiq_core.local_connected import LocalConnectedResearch
from investiq_core.webapp import create_app_server


class DirectoryFixture:
    def __init__(self):
        self.calls = 0

    async def get_json(self, url, *, headers):
        self.calls += 1
        return {
            "fields": ["cik", "name", "ticker", "exchange"],
            "data": [[12345, "Fictional Industries", "EXM", "Nasdaq"]],
        }


@pytest.fixture
def app(tmp_path):
    directory = tmp_path / "private"
    catalog = DirectoryFixture()
    service = LocalConnectedResearch(
        decision_dir=directory,
        directory_transport=catalog,
    )
    server = create_app_server(0, connected=service)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_port, directory, catalog
    finally:
        server.shutdown()
        thread.join(timeout=4)
        server.server_close()
        assert not thread.is_alive()


def send(port, path, *, data=None, cookie=None, csrf=None, method="POST", origin=True):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=4)
    headers = {"Host": f"127.0.0.1:{port}"}
    if origin:
        headers["Origin"] = f"http://127.0.0.1:{port}"
    if cookie:
        headers["Cookie"] = cookie
    if csrf:
        headers["X-InvestIQ-CSRF"] = csrf
    if method == "GET":
        headers["X-InvestIQ-Init"] = "1"
    if data is not None:
        headers["Content-Type"] = "application/json"
    payload = json.dumps(data).encode("utf-8") if data is not None else None
    try:
        connection.request(method, path, body=payload, headers=headers)
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), json.loads(response.read())
    finally:
        connection.close()


def session(port):
    status, headers, data = send(port, "/api/v1/session", method="GET")
    assert status == 200
    return headers["Set-Cookie"].split(";")[0], data["csrf"], data


def request(port, path, data, cookie, csrf):
    return send(port, path, data=data, cookie=cookie, csrf=csrf)


def typed_thesis():
    return {
        "thesis_id": "fictional_industries",
        "statement": "A manually authored thesis about unit economics",
        "reason": "First analysis",
        "stage": "researching",
        "risks": ["Competition may increase"],
        "invalidation_triggers": ["Recurring margin decline"],
        "hypothetical": None,
    }


def save_payload():
    return {
        "symbol": "EXM", "venue": "XNAS", "cik": "0000012345",
        "currency": "USD", "confirm_current_listing": True,
        "confirm_currency": True, "approve_private_save": True,
        "decision": typed_thesis(),
    }


def test_browser_history_save_load_export_and_auth_without_quote_or_ai(app):
    port, directory, catalog = app
    cookie, csrf, status = session(port)
    assert status["private_history_enabled"] is True
    assert not directory.exists()
    assert request(port, "/api/v1/decisions/list", {}, cookie, csrf)[0] == 200
    assert request(port, "/api/v1/decisions/save", save_payload(), cookie, csrf)[0] == 403
    assert request(port, "/api/v1/session/configure", {
        "sec_contact": "Research support@example.org", "twelve_data_api_key": "",
    }, cookie, csrf)[0] == 200
    assert request(port, "/api/v1/decisions/save", save_payload(), cookie, csrf)[0] == 400
    assert request(port, "/api/v1/companies/search", {"query": "EXM"}, cookie, csrf)[0] == 200
    assert catalog.calls == 1
    for altered in (
        {**save_payload(), "approve_private_save": False},
        {**save_payload(), "cik": "0000012346"},
        {**save_payload(), "confirm_currency": False},
        {**save_payload(), "currency": "EUR"},
    ):
        assert request(port, "/api/v1/decisions/save", altered, cookie, csrf)[0] == 400
    code, _, saved = request(port, "/api/v1/decisions/save", save_payload(), cookie, csrf)
    assert code == 200
    assert saved["revision"] == 1
    assert saved["quote_retained"] is False
    assert "price" not in json.dumps(saved).lower() or "NOT saved" in " ".join(saved["limitations"])
    code, _, listing = request(port, "/api/v1/decisions/list", {}, cookie, csrf)
    assert code == 200
    assert listing["snapshots"][0]["revision"] == 1
    code, _, opened = request(port, "/api/v1/decisions/open", {
        "thesis_id": "fictional_industries", "revision": 1
    }, cookie, csrf)
    assert code == 200
    assert opened["replay_numerical_price_analysis"] is False
    code, _, export = request(port, "/api/v1/decisions/export", {
        "thesis_id": "fictional_industries", "revision": 1, "format": "json"
    }, cookie, csrf)
    assert code == 200
    assert "Fictional Industries" not in export["content"]
    assert "unit economics" in export["content"]
    assert "quote" in export["content"]
    assert "api_key" not in export["content"]
    code, _, second = request(port, "/api/v1/decisions/save", save_payload(), cookie, csrf)
    assert code == 200
    assert second["revision"] == 2
    assert second["parent_digest"] == saved["thesis_digest"]
    assert request(port, "/api/v1/decisions/list", {}, cookie, csrf)[2]["snapshots"][0]["revision"] == 2
    assert catalog.calls == 1  # No provider call from save/replay/export


def test_multibyte_thesis_within_documented_limits_can_be_saved(app):
    port, directory, _ = app
    cookie, csrf, _ = session(port)
    assert request(port, "/api/v1/session/configure", {
        "sec_contact": "Research support@example.org", "twelve_data_api_key": "",
    }, cookie, csrf)[0] == 200
    assert request(
        port, "/api/v1/companies/search", {"query": "EXM"}, cookie, csrf,
    )[0] == 200
    payload = save_payload()
    payload["decision"]["thesis_id"] = "unicode_decision"
    payload["decision"]["statement"] = "测" * 1400
    payload["decision"]["reason"] = "变" * 400
    payload["decision"]["risks"] = ["风" * 189 + str(i) for i in range(5)]
    payload["decision"]["invalidation_triggers"] = [
        "险" * 189 + str(i) for i in range(5)
    ]
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    assert 8192 < len(raw) < 32768
    status, _, data = request(
        port, "/api/v1/decisions/save", payload, cookie, csrf,
    )
    assert status == 200
    assert data["revision"] == 1
    assert directory.joinpath("unicode_decision-00000001.json").exists()


def test_history_requires_cookie_csrf_origin_and_declared_folder(app):
    port, _, catalog = app
    cookie, csrf, _ = session(port)
    assert send(port, "/api/v1/decisions/list", data={}, csrf=csrf)[0] == 403
    assert send(port, "/api/v1/decisions/list", data={}, cookie=cookie)[0] == 403
    assert send(port, "/api/v1/decisions/list", data={}, cookie=cookie,
                csrf=csrf, origin=False)[0] == 403
    assert request(port, "/api/v1/decisions/open", {
        "thesis_id": "nonexistent", "revision": 1
    }, cookie, csrf)[0] == 404
    assert request(port, "/api/v1/decisions/open", {
        "thesis_id": "../bad", "revision": 1
    }, cookie, csrf)[0] == 400
    assert catalog.calls == 0


def test_history_disabled_does_not_create_any_unrequested_files(tmp_path):
    service = LocalConnectedResearch()
    assert service.history_available() is False
    with pytest.raises(PermissionError):
        service.list_decisions()
    assert not list(tmp_path.iterdir())
