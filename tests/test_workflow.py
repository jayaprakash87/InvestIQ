"""End-to-end offline synthetic research and CLI acceptance tests."""

import json
from copy import deepcopy

import pytest

from investiq_core.cli import main
from investiq_core.workflow import build_synthetic_bundle, validate_bundle


def test_complete_demo_validates_both_historical_views() -> None:
    bundle = build_synthetic_bundle()
    assert bundle["synthetic"] is True
    result = validate_bundle(bundle, basis="recorded")
    assert result["validation"] == "structural_only"
    assert result["evidence_count"] == 2
    assert result["thesis_revision_count"] == 2
    assert result["finding_count"] == 3
    assert result["scenario_analysis"]["expected_terminal_price"] == pytest.approx(105.6125)
    assert validate_bundle(bundle, basis="public")["finding_count"] == 3


def test_reject_fictitious_missing_growth_provenance() -> None:
    bundle = build_synthetic_bundle()
    bundle["valuation"]["base_growth_assumption_id"] = "unknown-hypothesis"
    with pytest.raises(ValueError, match="growth"):
        validate_bundle(bundle)


def test_reject_divergence_between_base_scenario_and_research_assumption() -> None:
    bundle = build_synthetic_bundle()
    bundle["valuation"]["scenarios"][1]["annual_eps_growth"] = 0.15
    with pytest.raises(ValueError, match="base scenario"):
        validate_bundle(bundle)


def test_reject_malformed_or_stale_evidence() -> None:
    bundle = build_synthetic_bundle()
    bundle["valuation"]["eps_evidence_id"] = "absent"
    with pytest.raises(ValueError, match="EPS"):
        validate_bundle(bundle)
    bundle = build_synthetic_bundle()
    bundle["evidence"][0]["publicly_available_at"] = "2025-04-01T12:00:00+00:00"
    with pytest.raises(ValueError):
        validate_bundle(bundle)


def test_demo_cli_generates_valid_json_and_validation_cli_reads_it(tmp_path, capsys) -> None:
    path = tmp_path / "fictional-investiq-research.json"
    assert main(["demo", "--output", str(path)]) == 0
    assert path.exists()
    assert json.loads(path.read_text())["synthetic"] is True
    capsys.readouterr()
    assert main(["validate", str(path), "--basis", "recorded"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["thesis_revision_count"] == 2
    assert output["validation"] == "structural_only"


def test_cli_can_print_example_without_file(capsys) -> None:
    assert main(["demo"]) == 0
    assert json.loads(capsys.readouterr().out)["synthetic"] is True


def test_cli_rejects_invalid_input_with_nonzero_status(tmp_path, capsys) -> None:
    bad = tmp_path / "invalid.json"
    bad.write_text('{"schema_version":"99"}', encoding="utf-8")
    assert main(["validate", str(bad)]) == 2
    assert "validation failed" in capsys.readouterr().err.lower()
    assert main(["validate", str(tmp_path / "absent.json")]) == 2


def test_json_roundtrip_preserves_research_and_assumptions() -> None:
    original = build_synthetic_bundle()
    restored = json.loads(json.dumps(original))
    assert validate_bundle(restored)["assumption_count"] == 1
    assert original == restored


def test_invalid_bundle_type_and_schema_fail_closed() -> None:
    with pytest.raises(TypeError, match="JSON object"):
        validate_bundle([])
    bundle = build_synthetic_bundle()
    bundle["schema_version"] = "0.2"
    with pytest.raises(ValueError, match="schema_version"):
        validate_bundle(bundle)
    bundle = build_synthetic_bundle()
    bundle["thesis_history"] = {}
    with pytest.raises(TypeError, match="JSON array"):
        validate_bundle(bundle)


def test_snapshot_corruption_detected() -> None:
    bundle = deepcopy(build_synthetic_bundle())
    bundle["thesis_history"][0]["statement"] = "Silently rewritten history"
    with pytest.raises(ValueError, match="ancestry"):
        validate_bundle(bundle)
