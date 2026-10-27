"""Loopback-only local Research Desk: offline demo and explicitly opted-in providers.

No startup network, persistent keys, hosted access, background polling or AI.
Connected endpoints require origin, session cookie and anti-CSRF controls.
"""

from __future__ import annotations

import json
import secrets
import webbrowser
from http.cookies import CookieError, SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from typing import Any
from urllib.parse import urlsplit

from .local_connected import LocalConnectedResearch
from .ports import ProviderFailure, ProviderFailureCode
from .workflow import build_synthetic_bundle, validate_bundle

_ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/connect.js": ("connect.js", "text/javascript; charset=utf-8"),
}
_HEADERS = {
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Content-Security-Policy": (
        "default-src 'none'; script-src 'self'; style-src 'self'; "
        "img-src 'self' data:; connect-src 'self'; font-src 'self'; "
        "object-src 'none'; frame-ancestors 'none'; base-uri 'none'; "
        "form-action 'self'"
    ),
}


def build_demo_response() -> dict[str, Any]:
    """Validate the actual core fixture before offering it to the browser."""
    bundle = build_synthetic_bundle()
    result = validate_bundle(bundle, basis="recorded")
    return {
        "mode": "synthetic",
        "connected": False,
        "model_executed": False,
        "persistence_enabled": False,
        "description": (
            "Fictional historical demonstration. No live prices, provider calls, "
            "AI analysis, saved decisions or investment advice."
        ),
        "bundle": bundle,
        "validation": result,
    }


def _allowed_authorities(port: int) -> set[str]:
    """Browser Host/Origin may omit :80 for the default HTTP port."""
    allowed = {f"127.0.0.1:{port}", f"localhost:{port}"}
    if port == 80:
        allowed.update({"127.0.0.1", "localhost"})
    return allowed


class ResearchAppHandler(BaseHTTPRequestHandler):
    """Serve static app plus bounded, explicitly authorized local research APIs."""

    server_version = "InvestIQ-Local"
    sys_version = ""

    def _trusted_request(self) -> bool:
        host = self.headers.get("Host", "")
        port = self.server.server_port
        allowed = _allowed_authorities(port)
        if host not in allowed:
            return False
        origin = self.headers.get("Origin")
        return origin is None or origin in {f"http://{item}" for item in allowed}

    def _send(
        self, status: int, body: bytes, content_type: str,
        *, extra_headers: dict[str, str] | None = None,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for key, value in _HEADERS.items():
            self.send_header(key, value)
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(
        self, status: int, value: dict[str, Any],
        *, extra_headers: dict[str, str] | None = None,
    ) -> None:
        data = json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self._send(
            status, data, "application/json; charset=utf-8",
            extra_headers=extra_headers,
        )

    def _session_cookie(self) -> str | None:
        raw = self.headers.get("Cookie", "")
        if len(raw) > 2048:
            return None
        cookie = SimpleCookie()
        try:
            cookie.load(raw)
        except CookieError:
            return None
        item = cookie.get("investiq_sid")
        return item.value if item is not None else None

    def _read_session(self) -> None:
        # A cross-site <img>/resource GET has no custom header and must never
        # allocate session capacity. A cross-origin JS request with this header
        # requires CORS preflight, which the local server never permits.
        if (
            self.headers.get("X-InvestIQ-Init") != "1"
            or self.headers.get("Sec-Fetch-Site") not in (None, "same-origin")
        ):
            self._json(403, {"error": "Local session initialization requires app context"})
            return
        session = self.server.connected.session(self._session_cookie(), create=True)
        if session is None:
            self._json(429, {"error": "Too many active local sessions; restart after expiry"})
            return
        sid, state = session
        self._json(
            200, self.server.connected.session_status(state),
            extra_headers={
                "Set-Cookie": (
                    f"investiq_sid={sid}; HttpOnly; SameSite=Strict; "
                    "Path=/; Max-Age=3600"
                ),
            },
        )

    def _read_post(self) -> None:
        if not self._trusted_request():
            self._json(403, {"error": "Host or origin not allowed"})
            return
        # The connected endpoints require BOTH the same-origin browser Origin
        # and an unguessable header token linked to an HttpOnly session cookie.
        if self.headers.get("Origin") not in {
            f"http://{item}" for item in _allowed_authorities(self.server.server_port)
        }:
            self._json(403, {"error": "Connected requests require a trusted browser origin"})
            return
        session = self.server.connected.session(self._session_cookie(), create=False)
        if session is None:
            self._json(403, {"error": "Open the local app and initialize a session"})
            return
        _, state = session
        supplied_csrf = self.headers.get("X-InvestIQ-CSRF", "")
        if not secrets.compare_digest(supplied_csrf, state.csrf):
            self._json(403, {"error": "Invalid session authorization"})
            return
        path = urlsplit(self.path)
        if path.query or path.fragment or path.path not in {
            "/api/v1/session/configure",
            "/api/v1/session/clear",
            "/api/v1/companies/search",
            "/api/v1/research/connected",
        }:
            self._json(404, {"error": "Not found"})
            return
        length = self.headers.get("Content-Length", "")
        if (
            self.headers.get("Transfer-Encoding")
            or not length.isascii()
            or not length.isdigit()
            or len(length) > 4
            or not 2 <= int(length) <= 2048
            or self.headers.get("Content-Type") != "application/json"
        ):
            self._json(400, {"error": "Expected a bounded JSON request body"})
            return
        try:
            body = json.loads(self.rfile.read(int(length)).decode("utf-8"))
            if not isinstance(body, dict):
                raise TypeError("JSON body must be an object")
            if path.path == "/api/v1/session/configure":
                result = self.server.connected.configure(state, body)
            elif path.path == "/api/v1/session/clear":
                result = self.server.connected.clear(state)
            elif path.path == "/api/v1/companies/search":
                result = self.server.connected.search(state, body)
            else:
                result = self.server.connected.analyze(state, body)
            self._json(200, result)
        except PermissionError:
            self._json(403, {"error": "Configure this local session first"})
        except ProviderFailure as exc:
            status = 429 if exc.code == ProviderFailureCode.RATE_LIMITED else 502
            self._json(status, {"error": "Connected provider request failed", "code": exc.code.value})
        except (ValueError, TypeError, KeyError, UnicodeError, json.JSONDecodeError):
            # No exception bodies or request values may be reflected: keys and
            # contact details are present in the setup request.
            self._json(400, {"error": "Invalid request or unsupported issuer selection"})
        except Exception:  # noqa: BLE001 - sanitize all unexpected HTTP boundary failures
            self._json(500, {"error": "Local research request failed"})


    def _read(self) -> None:
        if not self._trusted_request():
            self._json(403, {"error": "Host or origin not allowed"})
            return
        parsed = urlsplit(self.path)
        if parsed.query or parsed.fragment:
            self._json(404, {"error": "Not found"})
            return
        path = parsed.path
        if path == "/api/v1/health":
            self._json(200, {"status": "ok", "mode": "local_app", "network": "opt_in_only"})
        elif path == "/api/v1/session":
            self._read_session()
        elif path == "/api/v1/demo":
            self._json(200, build_demo_response())
        elif path in _ASSETS:
            name, mime_type = _ASSETS[path]
            content = files("investiq_core").joinpath("web", name).read_bytes()
            self._send(200, content, mime_type)
        else:
            self._json(404, {"error": "Not found"})

    def do_GET(self) -> None:
        self._read()

    def do_HEAD(self) -> None:
        self._read()

    def do_POST(self) -> None:
        self._read_post()

    def log_message(self, format: str, *args: object) -> None:
        """Never print URLs/query strings, which could become sensitive later."""
        # The app is a local development preview. Avoid request-path logging.
        return


def create_app_server(
    port: int = 8765, *, connected: LocalConnectedResearch | None = None
) -> ThreadingHTTPServer:
    """Bind to IPv4 loopback only. Zero selects a free port (useful in tests)."""
    if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
        raise ValueError("port must be an integer between 0 and 65535")
    server = ThreadingHTTPServer(("127.0.0.1", port), ResearchAppHandler)
    server.connected = connected or LocalConnectedResearch()
    server.daemon_threads = True
    return server


def serve_app(*, port: int = 8765, open_browser: bool = True) -> None:
    """Run the local research app until stopped; connected mode is user-initiated."""
    with create_app_server(port) as server:
        url = f"http://127.0.0.1:{server.server_port}/"
        print(f"InvestIQ local research desk: {url}", flush=True)
        print("Demo is fictional; connected data requires session setup; Ctrl+C to stop.", flush=True)
        if open_browser:
            webbrowser.open(url)
        try:
            server.serve_forever(poll_interval=0.2)
        except KeyboardInterrupt:
            pass
