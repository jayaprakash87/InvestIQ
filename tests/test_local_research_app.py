"""PR1 acceptance: accessible synthetic local app is loopback-only and read-only."""

from __future__ import annotations

import http.client
import json
import threading
from importlib.resources import files
from unittest.mock import patch

import pytest

from investiq_core.cli import main
from investiq_core.webapp import _allowed_authorities, build_demo_response, create_app_server
from investiq_core.workflow import validate_bundle


def _request(port: int, method: str, path: str, *, host: str | None = None):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    headers = {"Host": host if host is not None else f"127.0.0.1:{port}"}
    try:
        connection.request(method, path, headers=headers)
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        connection.close()


@pytest.fixture
def app_port():
    server = create_app_server(0)
    runner = threading.Thread(target=server.serve_forever, daemon=True)
    runner.start()
    try:
        yield server.server_port
    finally:
        server.shutdown()
        runner.join(timeout=3)
        server.server_close()
        assert not runner.is_alive()


def test_demo_reuses_core_validation_not_hardcoded_claims():
    payload = build_demo_response()
    assert payload["mode"] == "synthetic"
    assert payload["connected"] is False
    assert payload["model_executed"] is False
    assert payload["persistence_enabled"] is False
    assert payload["bundle"]["synthetic"] is True
    assert payload["validation"] == validate_bundle(payload["bundle"], basis="recorded")
    assert payload["validation"]["validation"] == "structural_only"
    assert len(payload["bundle"]["thesis_history"]) == 2
    assert len(payload["validation"]["scenario_analysis"]["outcomes"]) == 3


def test_local_http_assets_are_packaged_and_available(app_port):
    for path, expected_type in (
        ("/", "text/html"),
        ("/index.html", "text/html"),
        ("/styles.css", "text/css"),
        ("/app.js", "text/javascript"),
        ("/connect.js", "text/javascript"),
    ):
        status, headers, body = _request(app_port, "GET", path)
        assert status == 200
        assert expected_type in headers["Content-Type"]
        assert headers["Cache-Control"] == "no-store"
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] == "DENY"
        assert "default-src 'none'" in headers["Content-Security-Policy"]
        assert len(body) == int(headers["Content-Length"])
        assert body

    html = files("investiq_core").joinpath("web", "index.html").read_text(
        encoding="utf-8"
    )
    js = files("investiq_core").joinpath("web", "app.js").read_text(
        encoding="utf-8"
    )
    assert "FICTIONAL DATA" in html
    assert "model" in html.lower()
    assert "textContent" in js
    assert "innerHTML" not in js


def test_offline_api_is_structurally_valid_and_explicit(app_port):
    status, headers, raw = _request(app_port, "GET", "/api/v1/demo")
    assert status == 200
    assert headers["Content-Type"].startswith("application/json")
    payload = json.loads(raw)
    # JSON round-trip converts typed dataclass tuples into JSON arrays.
    assert payload == json.loads(json.dumps(build_demo_response()))
    assert payload["bundle"]["report"]["findings"][0]["evidence_ids"]
    assert "Fictional" in payload["description"]

    status, _, raw = _request(app_port, "GET", "/api/v1/health")
    assert status == 200
    assert json.loads(raw) == {
        "status": "ok",
        "mode": "local_app",
        "network": "opt_in_only",
    }


def test_preview_rejects_mutation_cross_origin_and_unexpected_paths(app_port):
    status, _, raw = _request(app_port, "POST", "/api/v1/demo")
    assert status == 403
    assert "trusted browser origin" in raw.decode()
    for path in ("/api/v1/research", "/.env", "/../../secret", "/src/investiq_core/cli.py"):
        status, _, _ = _request(app_port, "GET", path)
        assert status == 404
    status, _, _ = _request(app_port, "GET", "/", host="attacker.example")
    assert status == 403


def test_preview_rejects_cross_site_origin_and_supports_head(app_port):
    connection = http.client.HTTPConnection("127.0.0.1", app_port, timeout=3)
    try:
        connection.request(
            "GET",
            "/api/v1/demo",
            headers={"Host": f"127.0.0.1:{app_port}", "Origin": "https://evil.test"},
        )
        response = connection.getresponse()
        assert response.status == 403
        response.read()
    finally:
        connection.close()
    status, headers, raw = _request(app_port, "HEAD", "/")
    assert status == 200
    assert raw == b""
    assert int(headers["Content-Length"]) > 0


def test_default_http_port_authorities_do_not_reject_browser_host():
    assert _allowed_authorities(80) == {
        "localhost", "127.0.0.1", "localhost:80", "127.0.0.1:80"
    }
    assert _allowed_authorities(8765) == {"localhost:8765", "127.0.0.1:8765"}


def test_only_loopback_host_and_valid_ports():
    with create_app_server(0) as server:
        assert server.server_address[0] == "127.0.0.1"
        assert server.server_port > 0
    for port in (-1, 65536, "8765", True):
        with pytest.raises(ValueError, match="port"):
            create_app_server(port)


def test_app_cli_launches_local_server_without_default_provider_usage():
    with patch("investiq_core.webapp.serve_app") as serve:
        assert main(["app", "--port", "0", "--no-browser"]) == 0
        serve.assert_called_once_with(port=0, open_browser=False)


def test_app_cli_rejects_invalid_port(capsys):
    assert main(["app", "--port", "-2", "--no-browser"]) == 2
    assert "validation failed" in capsys.readouterr().err.lower()
