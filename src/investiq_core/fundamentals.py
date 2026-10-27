"""Small, provider-neutral financial metric catalog and filing reference contracts.

Concept-to-XBRL mapping, period normalization, restatements and source rights
belong to actual provider adapters and are NOT implied by this seed catalog.
"""

from __future__ import annotations

import re
from decimal import Decimal
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


@dataclass(frozen=True, slots=True)
class AnnualMetricFact:
    """One SEC-reported annual metric; not a certified intraday point-in-time fact.

    Filing date is date-only. The public release instant is *unknown*, and a
    later amendment or repeated value can describe an earlier fiscal period.
    """

    issuer: IssuerId
    metric: str
    value: Decimal
    unit: ValueUnit
    currency: str | None
    period_start: date
    period_end: date
    accession: str
    filed_on: date
    source_reference: str
    taxonomy: str
    tag: str
    retrieved_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.issuer, IssuerId):
            raise TypeError("issuer must be IssuerId")
        if self.metric not in {item.code for item in SEED_METRICS}:
            raise ValueError("metric must be a supported financial concept")
        if not isinstance(self.value, Decimal) or not self.value.is_finite():
            raise ValueError("reported metric must be a finite Decimal")
        if not isinstance(self.unit, ValueUnit):
            raise TypeError("unit must be ValueUnit")
        if self.unit in (ValueUnit.MONEY, ValueUnit.MONEY_PER_SHARE):
            if not isinstance(self.currency, str) or not re.fullmatch(r"[A-Z]{3}", self.currency):
                raise ValueError("monetary metrics require an ISO currency")
        elif self.currency is not None:
            raise ValueError("nonmonetary metrics must not include a currency")
        for name in ("period_start", "period_end", "filed_on"):
            v = getattr(self, name)
            if not isinstance(v, date) or isinstance(v, datetime):
                raise TypeError(f"{name} must be a date")
        if self.period_start > self.period_end or self.filed_on < self.period_end:
            raise ValueError("annual period and filing dates are inconsistent")
        if not 330 <= (self.period_end - self.period_start).days + 1 <= 395:
            raise ValueError("annual period must approximate a fiscal year")
        for name in ("accession", "source_reference", "taxonomy", "tag"):
            v = getattr(self, name)
            if not isinstance(v, str) or not v.strip():
                raise ValueError(f"{name} must be nonempty")
        if not isinstance(self.retrieved_at, datetime) or (
            self.retrieved_at.tzinfo is None or self.retrieved_at.utcoffset() is None
        ):
            raise ValueError("retrieved_at must be timezone-aware")
