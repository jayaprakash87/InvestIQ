"""PR6 private browser decisions reuse immutable v0.2 snapshot contracts."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pytest

from investiq_core.browser_decisions import BrowserDecisionHistory
from investiq_core.snapshot_store import LocalSnapshotStore, import_snapshot_json

ISSUER = {"symbol": "EXM", "venue": "XNAS", "cik": "0000012345"}


def draft(*, thesis_id="example_thesis", statement="My authored business thesis"):
    return {
        "thesis_id": thesis_id,
        "statement": statement,
        "reason": "Initial written decision",
        "stage": "researching",
        "risks": ["Demand could weaken", "Customer mix could change"],
        "invalidation_triggers": ["Revenue contracts materially"],
        "hypothetical": None,
    }


def hypothesis():
    return {
        "start_eps": 2.0,
        "initial_price": 40.0,
        "years": 5,
        "scenarios": [
            {"name": "bear", "annual_growth_percent": -5,
             "terminal_pe": 8, "weight_percent": 25},
            {"name": "base", "annual_growth_percent": 5,
             "terminal_pe": 15, "weight_percent": 50},
            {"name": "bull", "annual_growth_percent": 15,
             "terminal_pe": 20, "weight_percent": 25},
        ],
    }


def test_store_disabled_without_user_opt_in(tmp_path):
    workspace = BrowserDecisionHistory(None)
    assert workspace.enabled is False
    with pytest.raises(PermissionError):
        workspace.list()
    with pytest.raises(PermissionError):
        workspace.save(**ISSUER, data=draft())
    assert not any(tmp_path.iterdir())


def test_save_reopen_export_and_offline_replay_after_new_app_instance(tmp_path):
    directory = tmp_path / "decisions"
    first = BrowserDecisionHistory(directory)
    assert not directory.exists()
    saved = first.save(**ISSUER, data=draft())
    assert saved["revision"] == 1
    assert saved["mode"] == "explicit_private_decision_saved"
    assert saved["quote_retained"] is False
    assert saved["ai_analysis_retained"] is False
    assert saved["annual_facts_retained"] == 0
    assert directory.exists()
    filename = directory / "example_thesis-00000001.json"
    assert filename.is_file()
    if os.name == "posix":
        assert stat.S_IMODE(directory.stat().st_mode) == 0o700
        assert stat.S_IMODE(filename.stat().st_mode) == 0o600
    restored = BrowserDecisionHistory(directory)
    assert restored.list()["snapshots"][0]["digest_sha256"] == saved["digest_sha256"]
    opened = restored.load("example_thesis", 1)
    assert opened["statement"] == "My authored business thesis"
    assert opened["mode"] == "offline_replay_of_private_decision"
    assert opened["replay_numerical_price_analysis"] is False
    assert any("withheld" in w.lower() for w in opened["replay_warnings"])
    exported = restored.export("example_thesis", 1, "json")
    assert exported["filename"] == "example_thesis-00000001.json"
    parsed = import_snapshot_json(exported["content"])
    assert parsed.digest == saved["digest_sha256"]
    assert parsed.quote is None
    assert parsed.annual_facts == ()
    markdown = restored.export("example_thesis", 1, "markdown")["content"]
    assert "My authored business thesis" in markdown
    assert "not retained" in markdown
    assert "private" in markdown.lower()
    assert "api_key" not in exported["content"]


def test_versions_append_and_hash_link_without_overwriting_prior(tmp_path):
    journal = BrowserDecisionHistory(tmp_path / "decisions")
    initial = journal.save(**ISSUER, data=draft())
    changed = draft(statement="Researcher revised the business outlook")
    changed["reason"] = "Important new counterevidence"
    changed["stage"] = "challenged"
    changed["invalidation_triggers"] = ["Market share turns negative"]
    second = journal.save(**ISSUER, data=changed)
    assert initial["revision"] == 1
    assert second["revision"] == 2
    assert second["parent_digest"] == initial["thesis_digest"]
    assert journal.load("example_thesis", 1)["statement"] == "My authored business thesis"
    assert journal.load("example_thesis", 2)["statement"] == changed["statement"]
    third = journal.save(**ISSUER, data=changed)
    assert third["revision"] == 3
    assert third["parent_digest"] == second["thesis_digest"]
    assert {x["revision"] for x in journal.list()["snapshots"]} == {1, 2, 3}
    assert len(list((tmp_path / "decisions").glob("*.json"))) == 3


def test_optional_hypotheses_keep_only_year_growth_multiple_weights(tmp_path):
    journal = BrowserDecisionHistory(tmp_path / "decisions")
    saved = draft()
    saved["hypothetical"] = hypothesis()
    result = journal.save(**ISSUER, data=saved)
    opened = journal.load("example_thesis", 1)
    assert result["scenario_assumptions_retained"] is True
    assert opened["scenario_years"] == 5
    assert opened["scenario_assumptions"][1]["annual_growth_percent"] == 5.0
    assert opened["replay_numerical_price_analysis"] is False
    export = journal.export("example_thesis", 1, "json")["content"]
    record = json.loads(export)["payload"]
    assert record["quote"] is None
    assert record["share_basis_confirmed"] is False
    assert record["scenario_years"] == 5
    assert "start_eps" not in export
    assert "initial_price" not in export
    assert "weighted_terminal_price" not in export
    assert "Model" not in export


@pytest.mark.parametrize("change", [
    lambda x: x.update({"thesis_id": "../bad"}),
    lambda x: x.update({"thesis_id": ""}),
    lambda x: x.update({"statement": ""}),
    lambda x: x.update({"statement": "x" * 1401}),
    lambda x: x.update({"reason": "x" * 401}),
    lambda x: x.update({"stage": "unrecognized"}),
    lambda x: x.update({"risks": ["x"] * 6}),
    lambda x: x.update({"invalidation_triggers": ["duplicate", "duplicate"]}),
    lambda x: x.update({"secret_api_key": "extra"}),
    lambda x: x.update({"hypothetical": {**hypothesis(), "start_eps": 0}}),
])
def test_unsafe_or_unapproved_fields_do_not_create_decisions(tmp_path, change):
    journal = BrowserDecisionHistory(tmp_path / "decisions")
    data = draft()
    change(data)
    with pytest.raises((ValueError, TypeError)):
        journal.save(**ISSUER, data=data)
    if (tmp_path / "decisions").exists():
        assert not list((tmp_path / "decisions").glob("*.json"))


def test_existing_thesis_id_cannot_change_company_identity(tmp_path):
    journal = BrowserDecisionHistory(tmp_path / "decisions")
    journal.save(**ISSUER, data=draft())
    with pytest.raises(ValueError, match="another issuer"):
        journal.save(
            symbol="OTH", venue="XNYS", cik="0000022222", data=draft()
        )


def test_corrupt_file_and_unsafe_permissions_fail_closed(tmp_path):
    journal = BrowserDecisionHistory(tmp_path / "decisions")
    journal.save(**ISSUER, data=draft())
    path = tmp_path / "decisions" / "example_thesis-00000001.json"
    content = path.read_text(encoding="utf-8")
    path.write_text(content.replace("My authored business thesis", "tampered"), encoding="utf-8")
    with pytest.raises(ValueError, match="digest"):
        journal.load("example_thesis", 1)
    with pytest.raises(ValueError, match="digest"):
        journal.list()


def test_bounded_filename_validation_and_exports(tmp_path):
    journal = BrowserDecisionHistory(tmp_path / "decisions")
    journal.save(**ISSUER, data=draft())
    with pytest.raises(ValueError):
        journal.load("../../unsafe", 1)
    with pytest.raises(ValueError):
        journal.export("example_thesis", 1, "html")
    assert journal.export("example_thesis", 1, "markdown")["filename"].endswith(".md")
    # LocalSnapshotStore is the one source of truth, not a separate database.
    original = LocalSnapshotStore(tmp_path / "decisions").load("example_thesis", 1)
    assert original.quote is None
    assert original.issuer.value == "0000012345"


def test_history_browser_never_reads_ai_response_or_licensed_quote_markup():
    from importlib.resources import files

    script = files("investiq_core").joinpath("web", "history.js").read_text("utf-8")
    assert "innerHTML" not in script
    assert "textContent" in script
    assert 'post("/api/v1/decisions/save"' in script
    assert 'post("/api/v1/decisions/open"' in script
    assert 'post("/api/v1/decisions/list"' in script
    assert 'post("/api/v1/decisions/export"' in script
    assert "confirm_currency" in script
    assert "decision-consent" in script
    assert "scenario-calculated" in script
    assert 'document.getElementById("connected-output")' not in script
    assert 'document.getElementById("ai-result")' not in script
