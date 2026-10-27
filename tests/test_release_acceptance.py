"""v0.2 end-to-end acceptance: real adapters, fake HTTP, full CLI/save/replay.

No provider credentials, market network calls or licensed observations are used.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

from investiq_core import cli, connected_cli
from investiq_core.adapters.sec_companyfacts import SecCompanyFactsProvider
from investiq_core.adapters.sec_edgar import SecEdgarFilingProvider
from investiq_core.adapters.twelve_data import TwelveDataQuoteProvider
from investiq_core.application.connected_data import ConnectedDataService
from investiq_core.application.connected_research import ConnectedResearchService
from investiq_core.snapshot_store import LocalSnapshotStore


class FakeHTTP:
    def __init__(self, response):
        self.response = response
        self.calls: list[tuple[str, dict[str, str]]] = []

    async def get_json(self, url, *, headers):
        self.calls.append((url, dict(headers)))
        return self.response


def sec_payload():
    return {
        "cik": "0000320193",
        "facts": {
            "us-gaap": {
                "EarningsPerShareDiluted": {
                    "units": {
                        "USD/shares": [{
                            "start": "2025-01-01", "end": "2025-12-31",
                            "filed": "2026-02-11",
                            "accn": "0000320193-26-000001",
                            "form": "10-K", "fp": "FY", "val": 6,
                        }]
                    }
                },
                "NetIncomeLoss": {
                    "units": {
                        "USD": [{
                            "start": "2025-01-01", "end": "2025-12-31",
                            "filed": "2026-02-11",
                            "accn": "0000320193-26-000001",
                            "form": "10-K", "fp": "FY", "val": 100_000_000,
                        }]
                    }
                },
            }
        },
    }


def args(*extra):
    return [
        "research",
        "--symbol", "DEMO", "--venue", "XNAS", "--currency", "USD",
        "--cik", "320193", "--listing-source", "synthetic:explicit-sourced-mapping",
        "--listing-from", "2025-01-01", "--max-age-minutes", "30",
        *extra,
    ]


def factory(*, quote_override=None, quote_payload_override=None):
    now = datetime.now(UTC)
    synthetic_quote = quote_payload_override if quote_payload_override is not None else {
        "symbol": "DEMO", "mic_code": "XNAS", "currency": "USD",
        "close": "123.456",
        "last_quote_at": int((now - timedelta(seconds=90)).timestamp()),
        "is_market_open": False,
    }
    sec = FakeHTTP(sec_payload())
    quotes = FakeHTTP(synthetic_quote)
    sec_contact = "Synthetic Test local@example.org"
    fundamentals = SecCompanyFactsProvider(user_agent=sec_contact, transport=sec)
    quote_provider = quote_override or TwelveDataQuoteProvider(
        api_key="SYNTHETIC-SECRET-DO-NOT-SAVE", transport=quotes
    )
    data = ConnectedDataService(
        quote_provider=quote_provider,
        filing_provider=SecEdgarFilingProvider(user_agent=sec_contact,
                                               transport=FakeHTTP({})),
        principal_scope="synthetic-single-researcher",
    )
    service = ConnectedResearchService(data=data, fundamentals=fundamentals)
    return service, sec, quotes


def test_cli_connected_current_to_explicit_save_to_offline_replay(monkeypatch, capsys, tmp_path):
    service, sec, quotes = factory()
    monkeypatch.setattr(connected_cli, "_build_service", lambda: service)
    root = tmp_path / "private"
    # Viewing is nonpersistent. That includes the provider's live-response price.
    assert cli.main(args()) == 0
    current = json.loads(capsys.readouterr().out)
    assert current["mode"] == "connected_current_view_not_saved"
    assert current["quote"]["price"] == "123.456"
    assert current["quote"]["timeliness"] == "unknown"
    assert current["quote"]["snapshot_right"] == "unknown"
    assert current["reported_annual_pe_proxy"] is None
    assert current["annual_facts"][0]["accession"] == "0000320193-26-000001"
    assert not root.exists()
    assert len(sec.calls) == len(quotes.calls) == 1
    assert "companyfacts/CIK0000320193.json" in sec.calls[0][0]
    assert "mic_code=XNAS" in quotes.calls[0][0]

    # Saving is explicit and is license aware.
    assert cli.main(args(
        "--save-dir", str(root), "--thesis-id", "decision_1",
        "--thesis-statement", "Business hypothesis independent of current price",
        "--revision-reason", "Initial analyst decision",
    )) == 0
    saved_response = json.loads(capsys.readouterr().out)
    assert saved_response["saved_decision"]["quote_retained"] is False
    stored = root / "decision_1-00000001.json"
    contents = stored.read_text(encoding="utf-8")
    assert "123.456" not in contents
    assert "SYNTHETIC-SECRET-DO-NOT-SAVE" not in contents
    assert "twelvedata:" not in contents
    assert "private-user-key" not in contents
    snap = LocalSnapshotStore(root).load("decision_1", 1)
    assert snap.quote is None
    assert snap.annual_facts[0].value == 6

    # Replay imports neither credentials nor provider data; prove no calls.
    monkeypatch.delenv("TWELVE_DATA_API_KEY", raising=False)
    monkeypatch.delenv("INVESTIQ_SEC_USER_AGENT", raising=False)
    monkeypatch.setattr(
        connected_cli, "_build_service",
        lambda: (_ for _ in ()).throw(AssertionError("unexpected live provider access"))
    )
    assert cli.main([
        "replay", "--store-dir", str(root), "--thesis-id", "decision_1",
        "--revision", "1",
    ]) == 0
    replayed = json.loads(capsys.readouterr().out)
    assert replayed["mode"] == "offline_replay_no_provider_calls"
    assert replayed["reported_annual_pe_proxy"] is None
    assert replayed["quote_retained"] is False
    assert cli.main([
        "replay", "--store-dir", str(root), "--thesis-id", "decision_1",
        "--revision", "1", "--format", "markdown",
    ]) == 0
    markdown = capsys.readouterr().out
    assert "not retained" in markdown
    assert "123.456" not in markdown
    assert len(sec.calls) == len(quotes.calls) == 2


def test_cli_replay_manifest_roundtrip_without_network(monkeypatch, capsys, tmp_path):
    service, _, _ = factory()
    monkeypatch.setattr(connected_cli, "_build_service", lambda: service)
    assert cli.main(args(
        "--save-dir", str(tmp_path / "private"), "--thesis-id", "capture",
        "--thesis-statement", "Initial qualitative thesis",
        "--revision-reason", "First decision",
    )) == 0
    capsys.readouterr()
    assert cli.main([
        "replay", "--store-dir", str(tmp_path / "private"), "--thesis-id", "capture",
        "--revision", "1", "--format", "manifest",
    ]) == 0
    manifest = json.loads(capsys.readouterr().out)
    assert manifest["payload"]["quote_omitted"] is True
    assert manifest["payload"]["annual_facts"][0]["metric"] == "diluted_eps"


def test_cli_fails_closed_on_identity_mismatch_without_saving(monkeypatch, capsys, tmp_path):
    bad = {
        "symbol": "DEMO", "mic_code": "XNYS", "currency": "USD",
        "close": "123.456", "last_quote_at": int(datetime.now(UTC).timestamp()) - 60,
        "is_market_open": False,
    }
    service, _, _ = factory(quote_payload_override=bad)
    monkeypatch.setattr(connected_cli, "_build_service", lambda: service)
    root = tmp_path / "private"
    assert cli.main(args(
        "--save-dir", str(root), "--thesis-id", "bad",
        "--thesis-statement", "Must not be stored", "--revision-reason", "Test",
    )) == 2
    output = capsys.readouterr()
    assert not root.exists()
    assert "invalid_response" in output.err
    assert "123.456" not in output.err


def test_cli_refuses_missing_credential_and_incomplete_save(monkeypatch, capsys, tmp_path):
    monkeypatch.delenv("TWELVE_DATA_API_KEY", raising=False)
    monkeypatch.delenv("INVESTIQ_SEC_USER_AGENT", raising=False)
    assert cli.main(args()) == 2
    assert "TWELVE_DATA_API_KEY" in capsys.readouterr().err
    assert cli.main(args("--save-dir", str(tmp_path / "private"))) == 2
    assert "Saving requires" in capsys.readouterr().err
    assert not (tmp_path / "private").exists()


@pytest.mark.parametrize("extra", [
    ("--max-age-minutes", "0"),
    ("--max-age-minutes", "1441"),
    ("--confirm-share-basis",),
    ("--basis-rationale", "unilateral assumption"),
])
def test_cli_preflight_invalid_policy_never_contacts_providers(monkeypatch, capsys, extra):
    monkeypatch.setattr(
        connected_cli, "_build_service",
        lambda: (_ for _ in ()).throw(AssertionError("provider accessed")),
    )
    current = args()
    if extra[0] == "--max-age-minutes":
        current[current.index("--max-age-minutes") + 1] = extra[1]
    else:
        current.extend(extra)
    assert cli.main(current) == 2
    assert capsys.readouterr().err


def test_old_offline_demo_and_validator_are_still_compatible(capsys, tmp_path):
    path = tmp_path / "synthetic.json"
    assert cli.main(["demo", "--output", str(path)]) == 0
    capsys.readouterr()
    assert cli.main(["validate", str(path), "--basis", "recorded"]) == 0
    parsed = json.loads(capsys.readouterr().out)
    assert parsed["validation"] == "structural_only"


def test_replay_does_not_create_new_snapshots_on_repeat(monkeypatch, capsys, tmp_path):
    service, _, _ = factory()
    monkeypatch.setattr(connected_cli, "_build_service", lambda: service)
    root = tmp_path / "private"
    assert cli.main(args(
        "--save-dir", str(root), "--thesis-id", "revision",
        "--thesis-statement", "First saved thesis",
        "--revision-reason", "Research completed",
    )) == 0
    capsys.readouterr()
    before = {path.name for path in root.iterdir()}
    for _ in range(2):
        assert cli.main(["replay", "--store-dir", str(root),
                         "--thesis-id", "revision", "--revision", "1"]) == 0
        assert json.loads(capsys.readouterr().out)["quote_retained"] is False
    assert {path.name for path in root.iterdir()} == before
