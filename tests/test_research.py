"""Structural/temporal skills contract tests with synthetic data, not AI quality tests."""

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from investiq_core.evidence import (
    EvidenceSource,
    FinancialObservation,
    InstrumentId,
    ObservationKind,
    ResearchAssumption,
    ValueUnit,
)
from investiq_core.research import (
    SUPPORTED_SKILLS,
    FindingKind,
    ResearchFinding,
    ResearchReport,
    extract_evidence_ids,
    validate_research_report,
)


def at(day: int) -> datetime:
    return datetime(2025, 3, day, 12, tzinfo=UTC)


def example():
    source = EvidenceSource(
        reference="synthetic:source", publisher="Synthetic Test",
        published_at=at(1), retrieved_at=at(2),
    )
    subject = InstrumentId("DEMO", "XNAS", "USD")
    observation = FinancialObservation(
        observation_id="revenue-1", instrument=subject,
        metric="revenue", value=Decimal("125.50"),
        unit=ValueUnit.MONEY, currency="USD",
        kind=ObservationKind.REPORTED, source=source,
        effective_at=at(1) - timedelta(days=90),
        publicly_available_at=at(1), recorded_at=at(3),
    )
    assumption = ResearchAssumption(
        assumption_id="growth-1", instrument=subject,
        parameter="annual_growth", value=Decimal("0.1"), unit=ValueUnit.RATIO,
        rationale="Synthetic hypothetical growth", created_at=at(4),
    )
    report = ResearchReport(
        skill="financial-analysis", subjects=(subject,), as_of=at(10),
        findings=(
            ResearchFinding("f1", FindingKind.REPORTED_FACT, "Revenue was 125.50.", ("revenue-1",)),
            ResearchFinding("f2", FindingKind.ASSUMPTION, "Growth is hypothesized.", (),
                            ("growth-1",)),
            ResearchFinding("f3", FindingKind.INFERENCE, "Research needs validation.",
                            ("revenue-1",), ("growth-1",)),
            ResearchFinding("f4", FindingKind.DATA_GAP, "Cash flow is missing."),
        ),
    )
    return observation, assumption, report


def test_synthetic_contract_roundtrip_and_validation() -> None:
    obs, assumption, report = example()
    assert ResearchReport.from_record(json.loads(json.dumps(report.to_record()))) == report
    validate_research_report(report, evidence=[obs], assumptions=[assumption])
    assert extract_evidence_ids(report) == frozenset({"revenue-1"})


def test_public_sample_bundle_can_be_loaded_and_validated() -> None:
    file = Path(__file__).resolve().parents[1] / "examples/synthetic_research_bundle.json"
    bundle = json.loads(file.read_text(encoding="utf-8"))
    evidence = [FinancialObservation.from_record(item) for item in bundle["evidence"]]
    report = ResearchReport.from_record(bundle["report"])
    validate_research_report(report, evidence=evidence, assumptions=[])
    assert bundle["description"].startswith("Purely synthetic")


@pytest.mark.parametrize("kind", [FindingKind.REPORTED_FACT, FindingKind.EXTERNAL_ESTIMATE,
                                   FindingKind.ASSUMPTION, FindingKind.INFERENCE])
def test_unsupported_claim_without_citations_rejected(kind: FindingKind) -> None:
    obs, assumption, report = example()
    bad = replace(report, findings=(ResearchFinding("bad", kind, "Unproven"),))
    with pytest.raises(ValueError, match="requires|must cite"):
        validate_research_report(bad, evidence=[obs], assumptions=[assumption])


def test_future_observation_and_future_hypothesis_rejected() -> None:
    obs, assumption, report = example()
    later_source = EvidenceSource(
        reference="synthetic:future", publisher="Synthetic Test",
        published_at=at(11), retrieved_at=at(12),
    )
    later = replace(
        obs, source=later_source, publicly_available_at=at(11), recorded_at=at(12)
    )
    fact_report = replace(report, findings=(report.findings[0],))
    with pytest.raises(ValueError, match="not publicly available"):
        validate_research_report(fact_report, evidence=[later])
    later_hypothesis = replace(assumption, created_at=at(11))
    assumption_report = replace(report, findings=(report.findings[1],))
    with pytest.raises(ValueError, match="created after"):
        validate_research_report(assumption_report, evidence=[], assumptions=[later_hypothesis])


def test_recorded_basis_is_stricter_than_public_basis() -> None:
    obs, _, report = example()
    cutoff = at(2)
    report = replace(report, as_of=cutoff, findings=(report.findings[0],))
    validate_research_report(report, evidence=[obs])
    with pytest.raises(ValueError, match="not recorded"):
        validate_research_report(report, evidence=[obs], basis="recorded")


def test_cross_company_citations_must_be_in_scope() -> None:
    obs, _, report = example()
    foreign = replace(obs, instrument=InstrumentId("OTHER", "XNYS", "USD"))
    report = replace(report, findings=(report.findings[0],))
    with pytest.raises(ValueError, match="instrument not included"):
        validate_research_report(report, evidence=[foreign])


def test_consensus_cannot_be_labeled_as_reported_fact() -> None:
    obs, _, report = example()
    estimate = replace(obs, kind=ObservationKind.CONSENSUS)
    report = replace(report, findings=(report.findings[0],))
    with pytest.raises(ValueError, match="only reported"):
        validate_research_report(report, evidence=[estimate])
    estimate_report = replace(
        report, findings=(ResearchFinding(
            "e1", FindingKind.EXTERNAL_ESTIMATE, "Estimated metric", ("revenue-1",)
        ),),
    )
    validate_research_report(estimate_report, evidence=[estimate])


def test_unknown_and_duplicate_references_rejected() -> None:
    obs, _, report = example()
    report = replace(report, findings=(report.findings[0],))
    with pytest.raises(ValueError, match="unknown evidence"):
        validate_research_report(report, evidence=[])
    with pytest.raises(ValueError, match="duplicate observation"):
        validate_research_report(report, evidence=[obs, obs])


def test_synthetic_finding_cannot_falsely_cite_research_hypothesis_as_fact() -> None:
    obs, assumption, report = example()
    bogus = replace(report, findings=(ResearchFinding(
        "f1", FindingKind.REPORTED_FACT, "Claim", ("revenue-1",), ("growth-1",)
    ),))
    with pytest.raises(ValueError, match="no assumptions"):
        validate_research_report(bogus, evidence=[obs], assumptions=[assumption])


def test_model_agnostic_skills_have_required_instruction_structure() -> None:
    root = Path(__file__).resolve().parents[1] / "skills"
    assert len(SUPPORTED_SKILLS) == 5
    for name in SUPPORTED_SKILLS:
        content = (root / name / "SKILL.md").read_text(encoding="utf-8")
        assert content.startswith("---\nname: " + name + "\n")
        for heading in ("# ", "## Inputs", "## Procedure", "## Output", "## Safeguards"):
            assert heading in content


def test_peer_comparison_requires_multiple_instruments() -> None:
    _, _, report = example()
    with pytest.raises(ValueError, match="at least two"):
        replace(report, skill="peer-comparison")


def test_duplicate_finding_ids_and_naive_date_rejected() -> None:
    _, _, report = example()
    with pytest.raises(ValueError, match="unique"):
        replace(report, findings=(report.findings[0], report.findings[0]))
    with pytest.raises(ValueError, match="timezone"):
        replace(report, as_of=datetime(2025, 3, 10, 12))


def test_report_does_not_accept_bare_ticker_or_unknown_skill() -> None:
    _, _, report = example()
    with pytest.raises(ValueError, match="supported skill"):
        replace(report, skill="personal-stock-picker")
    with pytest.raises(ValueError, match="InstrumentId"):
        replace(report, subjects=("DEMO",))


def test_invalid_json_arrays_are_not_reinterpreted_as_characters() -> None:
    _, _, report = example()
    record = report.to_record()
    record["findings"][0]["evidence_ids"] = "revenue-1"
    with pytest.raises(TypeError, match="must be arrays"):
        ResearchReport.from_record(record)
    record = report.to_record()
    record["questions"] = "What is known?"
    with pytest.raises(ValueError, match="must be arrays"):
        ResearchReport.from_record(record)


def test_assumption_support_must_exist_and_be_available_at_creation() -> None:
    obs, assumption, report = example()
    cited_assumption = replace(assumption, evidence_ids=("missing-observation",))
    assumption_only = replace(report, findings=(report.findings[1],))
    with pytest.raises(ValueError, match="unknown evidence"):
        validate_research_report(
            assumption_only, evidence=[], assumptions=[cited_assumption]
        )

    future_assumption = replace(assumption, created_at=at(2), evidence_ids=("revenue-1",))
    with pytest.raises(ValueError, match="not recorded"):
        validate_research_report(
            assumption_only, evidence=[obs], assumptions=[future_assumption], basis="recorded"
        )

    future_source = EvidenceSource(
        reference="synthetic:later", publisher="Synthetic Test",
        published_at=at(5), retrieved_at=at(6),
    )
    future_observation = replace(
        obs, source=future_source, publicly_available_at=at(5), recorded_at=at(6)
    )
    with pytest.raises(ValueError, match="not publicly available"):
        validate_research_report(
            assumption_only, evidence=[future_observation], assumptions=[future_assumption]
        )


def test_assumption_support_cannot_cross_instrument_even_within_comparison() -> None:
    obs, assumption, report = example()
    other = InstrumentId("OTHER", "XNYS", "USD")
    peer_report = replace(
        report, skill="peer-comparison", subjects=(obs.instrument, other),
        findings=(report.findings[1],),
    )
    cross_company = replace(
        obs, instrument=other,
    )
    referenced = replace(assumption, evidence_ids=("revenue-1",))
    with pytest.raises(ValueError, match="support instrument"):
        validate_research_report(
            peer_report, evidence=[cross_company], assumptions=[referenced]
        )
