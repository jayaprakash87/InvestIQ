"""Synthetic examples only. No personal holdings or licensed market data."""

import json
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from investiq_core.evidence import (
    EvidenceSource,
    FinancialObservation,
    InstrumentId,
    ObservationKind,
    Redistribution,
    ResearchAssumption,
    ValueUnit,
    observations_as_of,
)


def time(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, 12, tzinfo=UTC)


def sample(**overrides: object) -> FinancialObservation:
    source = EvidenceSource(
        reference="synthetic:demo-quarter",
        publisher="Synthetic example",
        published_at=time(2025, 3, 1),
        retrieved_at=time(2025, 3, 4),
        redistribution=Redistribution.PERMITTED,
    )
    params = {
        "observation_id": "rev-1",
        "instrument": InstrumentId("TEST", "XNAS", "USD"),
        "metric": "revenue",
        "value": Decimal("125.50"),
        "unit": ValueUnit.MONEY,
        "kind": ObservationKind.REPORTED,
        "source": source,
        "effective_at": time(2024, 12, 31),
        "publicly_available_at": time(2025, 3, 1),
        "recorded_at": time(2025, 3, 5),
        "currency": "USD",
        "period_start": date(2024, 10, 1),
        "period_end": date(2024, 12, 31),
    }
    params.update(overrides)
    return FinancialObservation(**params)


def test_roundtrip_preserves_decimal_source_and_dates() -> None:
    observation = sample()
    record = observation.to_record()
    assert json.loads(json.dumps(record)) == record
    assert isinstance(record["value"], str)
    assert FinancialObservation.from_record(record) == observation


def test_float_json_value_is_rejected() -> None:
    record = sample().to_record()
    record["value"] = 125.5
    with pytest.raises(TypeError, match="decimal string"):
        FinancialObservation.from_record(record)


@pytest.mark.parametrize(
    "changes",
    [
        {"value": 125.5},
        {"value": Decimal("NaN")},
        {"unit": ValueUnit.RATIO},
        {"currency": "US"},
        {"currency": None},
        {"metric": "Revenue Growth"},
        {"recorded_at": time(2025, 3, 2)},
        {"publicly_available_at": time(2025, 2, 1)},
        {"period_start": None},
        {"period_start": date(2025, 1, 1)},
        {"effective_at": datetime(2024, 12, 31)},
        {"supersedes": "rev-1"},
    ],
)
def test_invalid_observation_contracts(changes: dict) -> None:
    with pytest.raises(ValueError):
        sample(**changes)


def test_venue_disambiguates_same_ticker() -> None:
    assert InstrumentId("TEST", "XNYS", "USD") != InstrumentId("TEST", "XNAS", "USD")


def test_rejects_invalid_venue_and_source_timestamps() -> None:
    with pytest.raises(ValueError):
        InstrumentId("TEST", "NASDAQ", "USD")
    with pytest.raises(ValueError):
        EvidenceSource("x", "Synthetic", time(2025, 1, 1), published_at=time(2025, 2, 1))


def test_historical_public_view_keeps_original_until_revision_is_known() -> None:
    original = sample()
    revised_source = EvidenceSource(
        reference="synthetic:revision",
        publisher="Synthetic example",
        published_at=time(2025, 4, 1),
        retrieved_at=time(2025, 4, 2),
    )
    revision = replace(
        original,
        observation_id="rev-2",
        value=Decimal("123.10"),
        source=revised_source,
        publicly_available_at=time(2025, 4, 1),
        recorded_at=time(2025, 4, 3),
        supersedes="rev-1",
    )
    assert observations_as_of([original, revision], cutoff=time(2025, 3, 20)) == (original,)
    assert observations_as_of([original, revision], cutoff=time(2025, 4, 5)) == (revision,)
    assert observations_as_of(
        [original, revision], cutoff=time(2025, 4, 2), basis="recorded"
    ) == (original,)


def test_public_knowability_is_distinct_from_local_capture() -> None:
    item = sample()
    cutoff = time(2025, 3, 3)
    assert observations_as_of([item], cutoff=cutoff, basis="public") == (item,)
    assert observations_as_of([item], cutoff=cutoff, basis="recorded") == ()


def test_rejects_duplicate_ids_and_revision_cycles() -> None:
    first = sample()
    with pytest.raises(ValueError, match="duplicate"):
        observations_as_of([first, first], cutoff=time(2026, 1, 1))

    a = replace(first, supersedes="rev-2")
    b = replace(first, observation_id="rev-2", supersedes="rev-1")
    with pytest.raises(ValueError, match="cyclic"):
        observations_as_of([a, b], cutoff=time(2026, 1, 1))


def test_assumptions_are_explicit_not_mislabeled_as_facts() -> None:
    assumption = ResearchAssumption(
        assumption_id="base-growth",
        instrument=InstrumentId("TEST", "XNAS", "USD"),
        parameter="annual_eps_growth",
        value=Decimal("0.12"),
        unit=ValueUnit.RATIO,
        rationale="Hypothetical example, not sourced financial guidance",
        created_at=time(2025, 3, 6),
        evidence_ids=("rev-1",),
    )
    assert assumption.value == Decimal("0.12")
    with pytest.raises(ValueError):
        replace(assumption, rationale="  ")

def test_cross_instrument_revision_is_rejected() -> None:
    first = sample()
    revision = replace(
        first, observation_id="rev-2",
        instrument=InstrumentId("OTHER", "XNAS", "USD"),
        supersedes="rev-1",
    )
    with pytest.raises(ValueError, match="revision must preserve"):
        observations_as_of([first, revision], cutoff=time(2026, 1, 1))

def test_datetime_fiscal_endpoints_do_not_corrupt_wire_roundtrip() -> None:
    with pytest.raises(ValueError, match="not datetimes"):
        sample(period_start=time(2024, 10, 1), period_end=time(2024, 12, 31))


def test_transitive_supersession_across_late_backfill() -> None:
    v1 = sample()
    v2_source = EvidenceSource(
        reference="synthetic:v2",
        publisher="Synthetic example",
        published_at=time(2025, 3, 10),
        retrieved_at=time(2025, 3, 11),
    )
    v3_source = EvidenceSource(
        reference="synthetic:v3",
        publisher="Synthetic example",
        published_at=time(2025, 3, 20),
        retrieved_at=time(2025, 3, 21),
    )
    v2 = replace(
        v1, observation_id="rev-2", value=Decimal("123"),
        source=v2_source, publicly_available_at=time(2025, 3, 10),
        recorded_at=time(2025, 4, 10), supersedes="rev-1",
    )
    v3 = replace(
        v1, observation_id="rev-3", value=Decimal("122"),
        source=v3_source, publicly_available_at=time(2025, 3, 20),
        recorded_at=time(2025, 3, 22), supersedes="rev-2",
    )
    # v2 is excluded from recorded view, but its lineage is still meaningful.
    assert observations_as_of(
        [v1, v2, v3], cutoff=time(2025, 3, 30), basis="recorded"
    ) == (v3,)
