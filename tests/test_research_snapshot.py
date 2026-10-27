"""Private snapshot save/replay contract: synthetic sources, no network calls."""

from __future__ import annotations

import json
import os
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from investiq_core.application.connected_data import QuoteResult
from investiq_core.application.connected_research import (
    CompanyResearchRequest,
    CompanyResearchResult,
)
from investiq_core.evidence import InstrumentId, ValueUnit
from investiq_core.fundamentals import AnnualMetricFact
from investiq_core.market import (
    IssuerId,
    IssuerListing,
    MarketDataRights,
    MarketQuote,
    MarketSession,
    Permission,
    PriceAdjustment,
    QuoteFreshness,
    QuoteKind,
    QuoteTimeliness,
)
from investiq_core.research_snapshot import (
    REPLAY_METHOD,
    capture_research_snapshot,
    replay_snapshot,
)
from investiq_core.snapshot_store import (
    LocalSnapshotStore,
    export_snapshot_json,
    import_snapshot_json,
    render_snapshot_markdown,
)
from investiq_core.thesis import ThesisSnapshot, ThesisStage
from investiq_core.valuation import ValuationScenario

NOW = datetime(2026, 10, 27, 11, tzinfo=UTC)
SAVED = NOW + timedelta(minutes=1)
INSTRUMENT = InstrumentId("DEMO", "XNAS", "USD")
ISSUER = IssuerId("SEC_CIK", "0000320193")
SEC_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json"


def inputs(*, right: Permission = Permission.UNKNOWN, price="123.456",
           eps="6.25", include_scenarios=False):
    quote = MarketQuote(
        quote_id="synthetic:quote-1", instrument=INSTRUMENT,
        provider="Fictional Feed", provider_symbol="DEMO",
        source_reference="synthetic:provider-reference-no-secrets",
        kind=QuoteKind.CLOSE, price=Decimal(price), currency="USD",
        event_at=NOW - timedelta(minutes=2), received_at=NOW,
        session=MarketSession.CLOSED, timeliness=QuoteTimeliness.UNKNOWN,
        entitlement_scope="private-user-key-fingerprint-DO-NOT-SAVE",
        adjustment=PriceAdjustment.UNKNOWN,
        rights=MarketDataRights(snapshot=right),
    )
    fact = AnnualMetricFact(
        issuer=ISSUER, metric="diluted_eps", value=Decimal(eps),
        unit=ValueUnit.MONEY_PER_SHARE, currency="USD",
        period_start=date(2025, 1, 1), period_end=date(2025, 12, 31),
        accession="0000320193-26-000001", filed_on=date(2026, 2, 11),
        source_reference=SEC_URL, taxonomy="us-gaap", tag="EarningsPerShareDiluted",
        retrieved_at=NOW,
    )
    listing = IssuerListing(
        issuer=ISSUER, instrument=INSTRUMENT, effective_from=date(2020, 1, 1),
        source_reference="synthetic:listing", verified_at=NOW,
    )
    scenarios = (
        ValuationScenario("bear", -0.03, 12, 0.25),
        ValuationScenario("base", 0.08, 20, 0.5),
        ValuationScenario("bull", 0.17, 28, 0.25),
    ) if include_scenarios else ()
    request = CompanyResearchRequest(
        listing=listing, max_quote_age=timedelta(minutes=5),
        analyst_confirmed_share_basis=True,
        share_basis_rationale="Checked same-share-class and split basis",
        scenario_years=3 if include_scenarios else None,
        scenarios=scenarios,
    )
    result = CompanyResearchResult(
        issuer="SEC_CIK:0000320193",
        observed_at=NOW,
        quote=QuoteResult(quote, QuoteFreshness.WITHIN_POLICY, False, 1),
        annual_facts=(fact,),
        annual_pe_proxy=quote.price / fact.value,
        scenarios=None, warnings=("price-sensitive example",),
    )
    return request, result


def thesis(*, thesis_id="analysis_1", revision=1, parent_digest=None,
           recorded_at=SAVED, statement="Company has durable returns"):
    return ThesisSnapshot(
        thesis_id=thesis_id, revision=revision, instrument=INSTRUMENT,
        as_of=NOW, recorded_at=recorded_at, method_version=REPLAY_METHOD,
        stage=ThesisStage.RESEARCHING, statement=statement,
        revision_reason="First explicit evidence capture" if revision == 1 else "Reassessed thesis",
        parent_digest=parent_digest,
    )


def make_snapshot(*, right=Permission.UNKNOWN, include_scenarios=False):
    request, result = inputs(right=right, include_scenarios=include_scenarios)
    return capture_research_snapshot(result, request, thesis(), saved_at=SAVED)


def test_unknown_quote_rights_omit_price_reference_and_derived_results():
    record = make_snapshot()
    assert record.quote is None
    assert replay_snapshot(record).annual_pe_proxy is None
    assert replay_snapshot(record).scenarios is None
    wire = export_snapshot_json(record)
    md = render_snapshot_markdown(record)
    assert "123.456" not in wire + md
    assert "synthetic:quote-1" not in wire + md
    assert "private-user-key-fingerprint" not in wire + md
    assert "provider-reference-no-secrets" not in wire + md
    assert "Snapshot rights" in md or "snapshot rights" in md
    assert "6.25" in wire
    assert record.to_record()["quote_omitted"] is True
    assert import_snapshot_json(wire) == record


@pytest.mark.parametrize("right", [Permission.UNKNOWN, Permission.DENIED])
def test_no_rights_never_leaks_licensed_price_even_with_scenarios(right):
    req, res = inputs(right=right, include_scenarios=True)
    record = capture_research_snapshot(res, req, thesis(), saved_at=SAVED)
    assert record.quote is None
    assert replay_snapshot(record).scenarios is None
    assert "123.456" not in export_snapshot_json(record)
    assert "123.456" not in render_snapshot_markdown(record)


def test_permitted_snapshot_has_deterministic_offline_valuation_and_outputs():
    record = make_snapshot(right=Permission.ALLOWED, include_scenarios=True)
    replayed = replay_snapshot(record)
    assert record.quote.price == Decimal("123.456")
    assert replayed.annual_pe_proxy == Decimal("123.456") / Decimal("6.25")
    assert replayed.scenarios is not None
    assert len(replayed.scenarios.outcomes) == 3
    json_text = export_snapshot_json(record)
    markdown = render_snapshot_markdown(record)
    assert "historical captured data" in markdown.lower() or "NOT a current/live" in markdown
    assert "123.456" in json_text and "123.456" in markdown
    assert "Annual" in markdown or "annual" in markdown
    restored = import_snapshot_json(json_text)
    assert restored.digest == record.digest
    assert replay_snapshot(restored) == replayed
    assert record.method_version == REPLAY_METHOD
    assert "private-user-key-fingerprint" not in json_text + markdown


def test_local_private_store_is_append_only_and_can_replay_without_provider(tmp_path):
    store = LocalSnapshotStore(tmp_path / "private")
    snap = make_snapshot(right=Permission.ALLOWED)
    saved_path = store.save(snap)
    assert saved_path.exists()
    assert saved_path.name == "analysis_1-00000001.json"
    loaded = store.load("analysis_1", 1)
    assert loaded.digest == snap.digest
    assert replay_snapshot(loaded).annual_pe_proxy == snap.quote.price / Decimal("6.25")
    assert render_snapshot_markdown(loaded) == render_snapshot_markdown(snap)
    with pytest.raises(FileExistsError):
        store.save(snap)
    assert store.load("analysis_1", 1) == loaded
    if os.name == "posix":
        assert (saved_path.stat().st_mode & 0o777) == 0o600
        assert (store.root.stat().st_mode & 0o777) == 0o700


def test_chain_revisions_reuse_thesis_digest_and_reject_orphans(tmp_path):
    store = LocalSnapshotStore(tmp_path / "private")
    first = make_snapshot()
    store.save(first)
    req, res = inputs(right=Permission.ALLOWED, price="140.00")
    rev2 = thesis(revision=2, parent_digest=first.thesis.digest,
                  recorded_at=SAVED + timedelta(days=1))
    second = capture_research_snapshot(
        res, req, rev2, saved_at=SAVED + timedelta(days=1)
    )
    store.save(second)
    assert store.load("analysis_1", 2).thesis.parent_digest == first.thesis.digest
    wrong = replace(second, thesis=replace(rev2, parent_digest="a" * 64))
    with pytest.raises(ValueError, match="ancestry"):
        store.save(wrong)
    missing = replace(second, thesis=replace(rev2, thesis_id="missing"))
    with pytest.raises(FileNotFoundError):
        store.save(missing)


def test_digest_tamper_duplicate_keys_and_unrecognized_schema_fail_closed():
    record = make_snapshot(right=Permission.ALLOWED)
    text = export_snapshot_json(record)
    root = json.loads(text)
    root["payload"]["quote"]["price"] = "100000000"
    with pytest.raises(ValueError, match="digest mismatch"):
        import_snapshot_json(json.dumps(root))
    root = json.loads(text)
    root["payload"]["schema_version"] = 999
    with pytest.raises(ValueError, match="digest mismatch"):
        import_snapshot_json(json.dumps(root))
    with pytest.raises(ValueError, match="duplicate JSON key"):
        import_snapshot_json('{"payload":{},"payload":{},"digest_sha256":"x"}')


def test_malicious_filename_symlink_private_permissions_and_overlimit(tmp_path):
    directory = tmp_path / "private"
    store = LocalSnapshotStore(directory)
    with pytest.raises(ValueError, match="safe short filename"):
        store.load("../other", 1)
    with pytest.raises(ValueError, match="range"):
        store.load("good", 0)
    outsider = tmp_path / "outside.json"
    outsider.write_text(export_snapshot_json(make_snapshot()))
    (directory / "analysis_1-00000001.json").symlink_to(outsider)
    with pytest.raises(ValueError, match="symbolic link"):
        store.load("analysis_1", 1)
    if os.name == "posix":
        public_dir = tmp_path / "public"
        public_dir.mkdir(mode=0o755)
        with pytest.raises(PermissionError, match="private"):
            LocalSnapshotStore(public_dir)
    with pytest.raises(ValueError, match="exceeds"):
        import_snapshot_json("x" * 2_000_001)


def test_reject_nonsec_fact_provenance_and_unbacked_thesis_evidence_ids():
    req, res = inputs()
    bad = replace(res.annual_facts[0], source_reference="https://external.example/api")
    with pytest.raises(ValueError, match="SEC Companyfacts"):
        capture_research_snapshot(
            replace(res, annual_facts=(bad,)), req, thesis(), saved_at=SAVED
        )
    with pytest.raises(ValueError, match="independently archived"):
        capture_research_snapshot(
            res, req, replace(thesis(), evidence_ids=("unarchived",)), saved_at=SAVED
        )


def test_snapshot_identity_clock_and_method_version_are_validated():
    req, res = inputs()
    with pytest.raises(ValueError, match="instrument"):
        capture_research_snapshot(
            res, req, replace(thesis(), instrument=InstrumentId("OTHER", "XNYS", "USD")),
            saved_at=SAVED,
        )
    with pytest.raises(ValueError, match="recording time"):
        capture_research_snapshot(res, req, thesis(), saved_at=SAVED + timedelta(seconds=10))
    record = make_snapshot()
    with pytest.raises(ValueError, match="unsupported"):
        replace(record, method_version="unrecognized-v7")
    with pytest.raises(ValueError, match="issuer"):
        replace(record, issuer=IssuerId("SEC_CIK", "0000777777"))


def test_rendering_user_notes_escapes_html_and_markdown_controls():
    req, res = inputs()
    user_thesis = thesis(statement="<script>alert('x')</script> | misleading")
    record = capture_research_snapshot(res, req, user_thesis, saved_at=SAVED)
    md = render_snapshot_markdown(record)
    assert "<script>" not in md
    assert "&lt;script&gt;" in md
    assert "\\|" in md


def test_false_entitlement_contradictory_quote_omission_and_old_method_not_readable():
    snap = make_snapshot(right=Permission.ALLOWED)
    doc = json.loads(export_snapshot_json(snap))
    doc["payload"]["quote_omitted"] = True
    # Hash cannot be spoofed merely by changing an unsigned field.
    with pytest.raises(ValueError, match="digest mismatch"):
        import_snapshot_json(json.dumps(doc))
    with pytest.raises(ValueError, match="unsupported"):
        replace(snap, schema_version=999)


def test_connected_research_cutoff_cannot_be_backdated_before_inputs():
    req, result = inputs()
    backdated = replace(thesis(), as_of=NOW - timedelta(days=7))
    with pytest.raises(ValueError, match="cannot predate"):
        capture_research_snapshot(result, req, backdated, saved_at=SAVED)


def test_retained_quote_reference_cannot_contain_credentials():
    req, result = inputs(right=Permission.ALLOWED)
    tainted = replace(
        result.quote.quote,
        source_reference="https://vendor.test/quote?apikey=PRIVATE-SYNTHETIC-KEY",
    )
    with pytest.raises(ValueError, match="credential-free"):
        capture_research_snapshot(
            replace(result, quote=replace(result.quote, quote=tainted)),
            req, thesis(), saved_at=SAVED
        )


def test_exponent_notation_in_exact_decimals_roundtrips():
    request, result = inputs(right=Permission.ALLOWED)
    income = replace(
        result.annual_facts[0], metric="revenue",
        value=Decimal("1E+8"), unit=ValueUnit.MONEY,
    )
    rec = capture_research_snapshot(
        replace(result, annual_facts=(income,)), request, thesis(), saved_at=SAVED
    )
    assert import_snapshot_json(export_snapshot_json(rec)) == rec


def test_markdown_escapes_formatting_in_user_authored_notes():
    request, result = inputs()
    snap = capture_research_snapshot(
        result, request, thesis(statement="**bad** [link](x) # header"),
        saved_at=SAVED,
    )
    text = render_snapshot_markdown(snap)
    assert "\\*\\*bad\\*\\*" in text
    assert "\\[link\\]" in text
