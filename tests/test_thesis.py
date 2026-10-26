"""Thesis memory tests use synthetic examples and no investor positions."""

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from investiq_core.evidence import (
    EvidenceSource, FinancialObservation, InstrumentId,
    ObservationKind, ResearchAssumption, ValueUnit,
)
from investiq_core.thesis import (
    ThesisSnapshot, ThesisStage, compare_thesis_revisions,
    export_thesis_jsonl, import_thesis_jsonl, validate_thesis_history,
)


def dt(day: int) -> datetime:
    return datetime(2025, 3, day, 12, tzinfo=UTC)


def example():
    subject = InstrumentId("DEMO", "XNAS", "USD")
    source = EvidenceSource(
        reference="synthetic:statement", publisher="Synthetic Fixture",
        published_at=dt(1), retrieved_at=dt(2),
    )
    observation = FinancialObservation(
        observation_id="synthetic:rev", instrument=subject, metric="revenue",
        value=Decimal("125"), unit=ValueUnit.MONEY, currency="USD",
        kind=ObservationKind.REPORTED, source=source,
        effective_at=dt(1), publicly_available_at=dt(1), recorded_at=dt(3),
    )
    assumption = ResearchAssumption(
        assumption_id="synthetic:growth", instrument=subject,
        parameter="growth", value=Decimal("0.10"), unit=ValueUnit.RATIO,
        rationale="Fictional scenario", created_at=dt(4),
        evidence_ids=("synthetic:rev",),
    )
    initial = ThesisSnapshot(
        thesis_id="synthetic-thesis", revision=1, instrument=subject,
        as_of=dt(5), recorded_at=dt(6),
        method_version="v0.1", stage=ThesisStage.RESEARCHING,
        statement="Initial fictional thesis.",
        revision_reason="New public research case",
        evidence_ids=("synthetic:rev",), assumption_ids=("synthetic:growth",),
        risks=("Customer concentration",), invalidation_triggers=("Lost major customer",),
    )
    updated = replace(
        initial, revision=2, parent_digest=initial.digest, as_of=dt(7),
        recorded_at=dt(8), statement="Revised fictional thesis.",
        revision_reason="Updated synthetic risk interpretation",
        stage=ThesisStage.CHALLENGED, risks=("Customer concentration", "Margin pressure"),
    )
    return observation, assumption, initial, updated


def test_thesis_roundtrip_and_diff() -> None:
    evidence, assumption, a, b = example()
    assert a.digest == ThesisSnapshot.from_record(a.to_record()).digest
    chain = validate_thesis_history([a, b], evidence=[evidence], assumptions=[assumption])
    assert chain == (a, b)
    restored = import_thesis_jsonl(export_thesis_jsonl(chain))
    assert restored == chain
    assert restored[0].digest == a.digest
    changes = compare_thesis_revisions(a, b)
    assert {c.field for c in changes} == {
        "statement", "revision_reason", "stage", "risks"
    }
    assert a.statement == "Initial fictional thesis."


def test_modified_original_breaks_ancestry() -> None:
    evidence, assumption, a, b = example()
    changed = replace(a, statement="Backdated manipulation")
    with pytest.raises(ValueError, match="ancestry"):
        validate_thesis_history([changed, b], evidence=[evidence], assumptions=[assumption])


def test_thesis_rejects_wrong_version_parent_and_subject() -> None:
    _, _, a, b = example()
    with pytest.raises(ValueError, match="parent"):
        replace(a, parent_digest="0" * 64)
    with pytest.raises(ValueError, match="parent"):
        replace(b, parent_digest=None)
    with pytest.raises(ValueError, match="revision"):
        replace(a, revision=True)
    with pytest.raises(ValueError, match="unrelated"):
        compare_thesis_revisions(a, replace(b, thesis_id="another-thesis"))


def test_asof_and_recorded_time_are_separate() -> None:
    _, _, a, _ = example()
    with pytest.raises(ValueError, match="recorded_at"):
        replace(a, recorded_at=dt(4))
    with pytest.raises(ValueError, match="timezone"):
        replace(a, as_of=datetime(2025, 3, 5, 12))


def test_reject_future_citations_and_unknown_assumptions() -> None:
    evidence, assumption, a, _ = example()
    with pytest.raises(ValueError, match="unknown assumption"):
        validate_thesis_history([a], evidence=[evidence])
    future_assumption = replace(assumption, created_at=dt(7))
    with pytest.raises(ValueError, match="created after"):
        validate_thesis_history([a], evidence=[evidence], assumptions=[future_assumption])
    with pytest.raises(ValueError, match="not recorded"):
        validate_thesis_history(
            [a], evidence=[replace(evidence, recorded_at=dt(7))],
            assumptions=[assumption], basis="recorded",
        )


def test_assumption_cannot_cite_missing_evidence() -> None:
    evidence, assumption, a, _ = example()
    bad = replace(assumption, evidence_ids=("not-found",))
    with pytest.raises(ValueError, match="unknown evidence"):
        validate_thesis_history([a], evidence=[evidence], assumptions=[bad])


def test_chain_cannot_skip_version_or_reverse_time() -> None:
    evidence, assumption, a, b = example()
    with pytest.raises(ValueError, match="ancestry"):
        validate_thesis_history(
            [a, replace(b, revision=3)], evidence=[evidence], assumptions=[assumption]
        )
    b_backwards = replace(b, as_of=dt(5), recorded_at=dt(5))
    with pytest.raises(ValueError, match="backwards"):
        validate_thesis_history(
            [a, b_backwards], evidence=[evidence], assumptions=[assumption]
        )


def test_missing_and_corrupt_json_are_rejected() -> None:
    _, _, a, _ = example()
    record = a.to_record()
    record["evidence_ids"] = "synthetic:rev"
    with pytest.raises(TypeError, match="JSON array"):
        ThesisSnapshot.from_record(record)
    with pytest.raises(ValueError):
        import_thesis_jsonl("not a JSONL record")
    with pytest.raises(ValueError, match="at least one"):
        validate_thesis_history([])


def test_open_research_thesis_can_have_explicit_gaps() -> None:
    _, _, a, _ = example()
    speculative = replace(
        a, evidence_ids=(), assumption_ids=(), stage=ThesisStage.RESEARCHING,
        statement="Research needed: unknown business economics",
    )
    assert validate_thesis_history([speculative]) == (speculative,)
