"""Bounded HTTPS transport tests with mocked urllib; no network access."""

import asyncio
import io
from datetime import UTC, datetime, timedelta
from email.utils import format_datetime
from http.client import IncompleteRead
from urllib.error import HTTPError, URLError

import pytest

from investiq_core.adapters import _http


class DummyResponse:
    def __init__(self, payload: bytes):
        self.payload = io.BytesIO(payload)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, amount):
        return self.payload.read(amount)


class DummyOpener:
    def __init__(self, value):
        self.value = value

    def open(self, request, timeout):
        if isinstance(self.value, Exception):
            raise self.value
        return DummyResponse(self.value)


def call(monkeypatch, response, *, max_bytes=200, clock=None):
    monkeypatch.setattr(_http, "build_opener", lambda *_args: DummyOpener(response))
    return asyncio.run(_http.UrllibJsonTransport(max_bytes=max_bytes, clock=clock).get_json(
        "https://example.org/api?apikey=SYNTHETIC-SECRET",
        headers={"User-Agent": "InvestIQ Synthetic developer@example.org"},
    ))


def test_valid_json_roundtrip_and_fail_closed_scheme(monkeypatch):
    assert call(monkeypatch, b'{"ok": true, "value": "1.234"}') == {
        "ok": True, "value": "1.234"
    }
    with pytest.raises(_http.TransportInvalidResponseError, match="HTTPS"):
        asyncio.run(_http.UrllibJsonTransport().get_json(
            "http://example.org/", headers={}
        ))


@pytest.mark.parametrize("payload", [
    b'{"number":NaN}',
    b'{"bad":',
    b'\xff\xfe',
])
def test_non_json_and_nonfinite_constants_are_rejected(monkeypatch, payload):
    with pytest.raises(_http.TransportInvalidResponseError):
        call(monkeypatch, payload)


def test_oversized_response_is_rejected(monkeypatch):
    with pytest.raises(_http.TransportInvalidResponseError, match="limit"):
        call(monkeypatch, b'{"long":"' + b"x" * 300 + b'"}', max_bytes=100)


@pytest.mark.parametrize("status,expected_retry", [
    (401, None), (403, None), (302, None), (429, 10), (500, None)
])
def test_http_errors_are_sanitized_and_retries_bounded(monkeypatch, status, expected_retry):
    url = "https://example.org/api?apikey=SYNTHETIC-SECRET"
    headers = {"Retry-After": "10"} if status == 429 else {}
    error = HTTPError(url, status, "SECRET HTTP ERROR", headers, None)
    with pytest.raises(_http.TransportStatusError) as exc:
        call(monkeypatch, error)
    assert exc.value.status == status
    assert exc.value.retry_after_seconds == expected_retry
    assert "SYNTHETIC-SECRET" not in str(exc.value)
    assert "SECRET HTTP ERROR" not in str(exc.value)


@pytest.mark.parametrize("failure,expected", [
    (TimeoutError("SYNTHETIC-SECRET"), _http.TransportTimeoutError),
    (URLError("SYNTHETIC-SECRET"), _http.TransportUnavailableError),
])
def test_socket_failures_do_not_reveal_credential_bearing_url(monkeypatch, failure, expected):
    with pytest.raises(expected) as exc:
        call(monkeypatch, failure)
    assert "SYNTHETIC-SECRET" not in str(exc.value)


def test_transport_constructor_rejects_unsafe_limits():
    with pytest.raises(ValueError):
        _http.UrllibJsonTransport(timeout_seconds=0)
    with pytest.raises(ValueError):
        _http.UrllibJsonTransport(max_bytes=20_000_000)


def test_retry_after_http_date_is_parsed_as_minimum_provider_delay(monkeypatch):
    now = datetime(2026, 10, 27, 10, tzinfo=UTC)
    deadline = format_datetime(now + timedelta(minutes=7), usegmt=True)
    error = HTTPError(
        "https://example.org/api?apikey=SYNTHETIC-SECRET",
        429, "SECRET ERROR", {"Retry-After": deadline}, None,
    )
    with pytest.raises(_http.TransportStatusError) as exc:
        call(monkeypatch, error, clock=lambda: now)
    assert exc.value.retry_after_seconds == 420
    assert "SYNTHETIC-SECRET" not in str(exc.value)


def test_retry_after_past_http_date_has_no_remaining_minimum(monkeypatch):
    now = datetime(2026, 10, 27, 10, tzinfo=UTC)
    deadline = format_datetime(now - timedelta(seconds=15), usegmt=True)
    error = HTTPError("https://example.org/", 429, "rate", {"Retry-After": deadline}, None)
    with pytest.raises(_http.TransportStatusError) as exc:
        call(monkeypatch, error, clock=lambda: now)
    assert exc.value.retry_after_seconds == 0


def test_truncated_http_body_maps_to_sanitized_retryable_transport_failure(monkeypatch):
    class InterruptedBody:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, amount):
            raise IncompleteRead(b'{"private":', 100)

    class InterruptedOpener:
        def open(self, request, timeout):
            return InterruptedBody()

    monkeypatch.setattr(
        _http, "build_opener", lambda *_args: InterruptedOpener()
    )
    with pytest.raises(_http.TransportUnavailableError) as error:
        asyncio.run(_http.UrllibJsonTransport().get_json(
            "https://example.org/api?apikey=SYNTHETIC-SECRET",
            headers={},
        ))
    assert "SYNTHETIC-SECRET" not in str(error.value)
