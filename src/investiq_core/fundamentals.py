"""Small, provider-neutral financial metric catalog and filing reference contracts.

Concept-to-XBRL mapping, period normalization, restatements and source rights
belong to actual provider adapters and are NOT implied by this seed catalog.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import Enum

from .evidence import ValueUnit
from .market import IssuerId


class PeriodType(str, Enum):
    INSTANT = "instant"
    DURATION = "duration"


@dataclass(frozen=True, slots=True)
class MetricDefinition:
    code: str
    description: str
    unit: ValueUnit
    period_type: PeriodType

    def __post_init__(self) -> None:
        if not isinstance(self.code, str) or not re.fullmatch(
            r"[a-z][a-z0-9_]*", self.code
        ):
            raise ValueError("metric code must be snake_case")
        if not isinstance(self.description, str) or not self.description.strip():
            raise ValueError("metric description must be nonempty")
        if not isinstance(self.unit, ValueUnit):
            raise TypeError("unit must be ValueUnit")
        if not isinstance(self.period_type, PeriodType):
            raise TypeError("period_type must be PeriodType")


SEED_METRICS: tuple[MetricDefinition, ...] = (
    MetricDefinition("revenue", "Reported revenue", ValueUnit.MONEY, PeriodType.DURATION),
    MetricDefinition(
        "operating_income", "Reported operating income", ValueUnit.MONEY, PeriodType.DURATION
    ),
    MetricDefinition("net_income", "Reported net income", ValueUnit.MONEY, PeriodType.DURATION),
    MetricDefinition(
        "diluted_eps", "Reported diluted earnings per share",
        ValueUnit.MONEY_PER_SHARE, PeriodType.DURATION
    ),
    MetricDefinition(
        "operating_cash_flow", "Cash flow from operations", ValueUnit.MONEY, PeriodType.DURATION
    ),
    MetricDefinition(
        "capital_expenditures", "Capital expenditures; source sign must be normalized explicitly",
        ValueUnit.MONEY, PeriodType.DURATION
    ),
    MetricDefinition(
        "cash_and_equivalents", "Cash and cash equivalents", ValueUnit.MONEY, PeriodType.INSTANT
    ),
    MetricDefinition(
        "total_debt", "Total interest-bearing debt (where source definitions permit)",
        ValueUnit.MONEY, PeriodType.INSTANT
    ),
    MetricDefinition(
        "diluted_shares", "Weighted average diluted shares", ValueUnit.SHARES, PeriodType.DURATION
    ),
)


@dataclass(frozen=True, slots=True)
class FilingReference:
    """Filing identity; a date-only filed_on is not a fabricated release time."""

    issuer: IssuerId
    accession: str
    form: str
    filed_on: date
    source_reference: str
    retrieved_at: datetime
    publicly_available_at: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.issuer, IssuerId):
            raise TypeError("issuer must be IssuerId")
        for name in ("accession", "form", "source_reference"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be nonempty")
        if not isinstance(self.filed_on, date) or isinstance(self.filed_on, datetime):
            raise TypeError("filed_on must be a date (not an assumed publication instant)")
        if (
            not isinstance(self.retrieved_at, datetime)
            or self.retrieved_at.tzinfo is None
            or self.retrieved_at.utcoffset() is None
        ):
            raise ValueError("retrieved_at must be timezone-aware")
        if self.publicly_available_at is not None and (
            not isinstance(self.publicly_available_at, datetime)
            or self.publicly_available_at.tzinfo is None
            or self.publicly_available_at.utcoffset() is None
        ):
            raise ValueError("publicly_available_at must be timezone-aware")
        if (
            self.publicly_available_at is not None
            and self.publicly_available_at.astimezone(UTC) > self.retrieved_at.astimezone(UTC)
        ):
            raise ValueError("public filing availability cannot follow retrieval")
