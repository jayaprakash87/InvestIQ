"""Validate explicit, precision-safe research assumption wire records."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from investiq_core.evidence import InstrumentId, ResearchAssumption, ValueUnit


def example() -> ResearchAssumption:
    return ResearchAssumption(
        assumption_id="synthetic-growth",
        instrument=InstrumentId("DEMO", "XNAS", "USD"),
        parameter="growth",
        value=Decimal("0.105000"),
        unit=ValueUnit.RATIO,
        rationale="Hypothetical growth input",
        created_at=datetime(2025, 3, 1, tzinfo=UTC),
        evidence_ids=("example-eps",),
    )


def test_roundtrip_preserves_exact_decimal_and_references() -> None:
    x = example()
    assert ResearchAssumption.from_record(x.to_record()) == x
    assert x.to_record()["value"] == "0.105000"


def test_reject_binary_float_and_string_citation_list() -> None:
    x = example().to_record()
    x["value"] = 0.105
    with pytest.raises(TypeError, match="decimal string"):
        ResearchAssumption.from_record(x)
    x = example().to_record()
    x["evidence_ids"] = "example-eps"
    with pytest.raises(TypeError, match="JSON array"):
        ResearchAssumption.from_record(x)
