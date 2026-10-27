"""Synthetic filing and metric-definition contracts without external ingestion."""

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta

import pytest

from investiq_core.evidence import ValueUnit
from investiq_core.fundamentals import (
    SEED_METRICS,
    FilingReference,
    MetricDefinition,
    PeriodType,
)
from investiq_core.market import IssuerId


def test_seed_metrics_have_unique_semantically_typed_periods() -> None:
    catalog = {item.code: item for item in SEED_METRICS}
    assert len(catalog) == len(SEED_METRICS)
    assert catalog["revenue"].period_type == PeriodType.DURATION
    assert catalog["cash_and_equivalents"].period_type == PeriodType.INSTANT
    assert catalog["diluted_eps"].unit == ValueUnit.MONEY_PER_SHARE
    assert catalog["diluted_shares"].unit == ValueUnit.SHARES
    assert catalog["capital_expenditures"].period_type == PeriodType.DURATION
    with pytest.raises(ValueError, match="snake_case"):
        MetricDefinition("Revenue 2026", "Bad code", ValueUnit.MONEY, PeriodType.DURATION)
    with pytest.raises(TypeError, match="PeriodType"):
        replace(catalog["revenue"], period_type="duration")


def test_filing_date_is_not_invented_intraday_publication_time() -> None:
    issuer = IssuerId("SEC_CIK", "0000123456")
    item = FilingReference(
        issuer=issuer,
        accession="synthetic:accession",
        form="10-K",
        filed_on=date(2026, 2, 26),
        source_reference="synthetic:filing",
        retrieved_at=datetime(2026, 2, 27, tzinfo=UTC),
    )
    assert item.publicly_available_at is None
    assert item.filed_on == date(2026, 2, 26)
    # When separately verified, the public instant is stored independently.
    assert replace(
        item, publicly_available_at=datetime(2026, 2, 26, 21, tzinfo=UTC)
    ).publicly_available_at != item.retrieved_at
    with pytest.raises(ValueError, match="cannot follow retrieval"):
        replace(
            item, publicly_available_at=item.retrieved_at + timedelta(days=1)
        )
    with pytest.raises(TypeError, match="date"):
        replace(item, filed_on=datetime(2026, 2, 26, tzinfo=UTC))
    with pytest.raises(ValueError, match="timezone-aware"):
        replace(item, retrieved_at=datetime(2026, 2, 27))
    with pytest.raises(ValueError, match="timezone-aware"):
        replace(item, retrieved_at=None)
