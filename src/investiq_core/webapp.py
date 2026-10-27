"""Loopback-only, no-dependency research preview backed by existing synthetic core.

PR 1 intentionally exposes NO live provider, secrets, AI calls, storage or writes.
It must not be mistaken for the v0.3 connected research application.
"""

from __future__ import annotations

import json
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from typing import Any
from urllib.parse import urlsplit

from .workflow import build_synthetic_bundle, validate_bundle

_ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
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
        "form-action 'none'"
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


class ResearchAppHandler(BaseHTTPRequestHandler):
    """Serve a fixed allowlist of static assets and one read-only JSON API."""

    server_version = "InvestIQ-Local"
    sys_version = ""

    def _trusted_request(self) -> bool:
        host = self.headers.get("Host", "")
        port = self.server.server_port
        allowed = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if host not in allowed:
            return False
        origin = self.headers.get("Origin")
        if origin is not None and origin not in {f"http://{item}" for item in allowed}:
            return False
        return True

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for key, value in _HEADERS.items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, status: int, value: dict[str, Any]) -> None:
        data = json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self._send(status, data, "application/json; charset=utf-8")

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
            self._json(200, {"status": "ok", "mode": "synthetic", "network": "disabled"})
        elif path == "/api/v1/demo":
            self._json(200, build_demo_response())
        elif path in _ASSETS:
            name, mime_type = _ASSETS[path]
            content = files("investiq_core").joinpath("web", name).read_bytes()
            self._send(200, content, mime_type)
        else:
            self._json(404, {"error": "Not found"})

    def do_GET(self) -> None:  # noqa: N802
        self._read()

    def do_HEAD(self) -> None:  # noqa: N802
        self._read()

    def do_POST(self) -> None:  # noqa: N802
        self._json(405, {"error": "Read-only preview; writes are not available"})

    def log_message(self, format: str, *args: object) -> None:
        """Never print URLs/query strings, which could become sensitive later."""
        # The app is a local development preview. Avoid request-path logging.
        return


def create_app_server(port: int = 8765) -> ThreadingHTTPServer:
    """Bind to IPv4 loopback only. Zero selects a free port (useful in tests)."""
    if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
        raise ValueError("port must be an integer between 0 and 65535")
    server = ThreadingHTTPServer(("127.0.0.1", port), ResearchAppHandler)
    server.daemon_threads = True
    return server


def serve_app(*, port: int = 8765, open_browser: bool = True) -> None:
    """Run the read-only app until the user stops the process with Ctrl+C."""
    with create_app_server(port) as server:
        url = f"http://127.0.0.1:{server.server_port}/"
        print(f"InvestIQ synthetic research preview: {url}", flush=True)
        print("Fictional offline data only; Ctrl+C to stop.", flush=True)
        if open_browser:
            webbrowser.open(url)
        try:
            server.serve_forever(poll_interval=0.2)
        except KeyboardInterrupt:
            pass
