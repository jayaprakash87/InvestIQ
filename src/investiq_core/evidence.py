"""Point-in-time research evidence contracts.

The public-information view answers 'what could have been publicly known then?'.
The recorded-information view answers 'what had this dataset actually captured?'.
They are intentionally different to avoid conflating historical backtests with
replay of a particular researcher's records.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Literal


class ValueUnit(str, Enum):
    """RATIO values are fractions: Decimal('0.15') represents 15%."""

    MONEY = "money"
    MONEY_PER_SHARE = "money_per_share"
    RATIO = "ratio"
    SHARES = "shares"
    COUNT = "count"


class ObservationKind(str, Enum):
    REPORTED = "reported"
    CONSENSUS = "consensus"
    ESTIMATE = "estimate"
    DERIVED = "derived"


class Redistribution(str, Enum):
    UNKNOWN = "unknown"
    PERMITTED = "permitted"
    RESTRICTED = "restricted"


def _aware(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be a timezone-aware datetime")


def _nonempty(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonempty string")


def _value_and_currency(value: Decimal, unit: ValueUnit, currency: str | None) -> None:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError("value must be a finite Decimal; do not silently round floats")
    if not isinstance(unit, ValueUnit):
        raise TypeError("unit must be a ValueUnit")
    is_monetary = unit in (ValueUnit.MONEY, ValueUnit.MONEY_PER_SHARE)
    if is_monetary != (currency is not None):
        raise ValueError("currency must be present exactly for monetary units")
    if currency is not None and not re.fullmatch(r"[A-Z]{3}", currency):
        raise ValueError("currency must be a three-letter uppercase ISO currency code")


@dataclass(frozen=True, slots=True)
class InstrumentId:
    """Venue-specific identity. A bare ticker is not a globally unique key."""

    ticker: str
    venue: str  # ISO 10383 MIC, e.g. XNAS, XNYS
    trading_currency: str

    def __post_init__(self) -> None:
        if not isinstance(self.ticker, str) or not re.fullmatch(
            r"[A-Z0-9][A-Z0-9.\-]{0,19}", self.ticker
        ):
            raise ValueError("ticker must use a normalized venue-specific symbol")
        if not isinstance(self.venue, str) or not re.fullmatch(r"[A-Z0-9]{4}", self.venue):
            raise ValueError("venue must be a four-character ISO 10383 MIC")
        if not isinstance(self.trading_currency, str) or not re.fullmatch(
            r"[A-Z]{3}", self.trading_currency
        ):
            raise ValueError("trading_currency must be a three-letter uppercase code")


@dataclass(frozen=True, slots=True)
class EvidenceSource:
    """A source reference is not a grant of data redistribution rights."""

    reference: str
    publisher: str
    retrieved_at: datetime
    published_at: datetime | None = None
    url: str | None = None
    redistribution: Redistribution = Redistribution.UNKNOWN

    def __post_init__(self) -> None:
        _nonempty(self.reference, "reference")
        _nonempty(self.publisher, "publisher")
        _aware(self.retrieved_at, "retrieved_at")
        if self.published_at is not None:
            _aware(self.published_at, "published_at")
            if self.published_at > self.retrieved_at:
                raise ValueError("source publication cannot follow retrieval")
        if self.url is not None and (
            not isinstance(self.url, str)
            or not (self.url.startswith("https://") or self.url.startswith("http://"))
        ):
            raise ValueError("source URL must be absolute HTTP(S)")
        if not isinstance(self.redistribution, Redistribution):
            raise TypeError("redistribution must be a Redistribution value")


@dataclass(frozen=True, slots=True)
class FinancialObservation:
    """Immutable, attributed numeric observation with distinct temporal axes.

    effective_at: economic instant described (not the date the fact was known).
    publicly_available_at: earliest verified public availability of THIS version.
    recorded_at: when this record was persisted into this research dataset.

    Revision history is explicit through supersedes; historic queries must never
    substitute a newer/restated observation for a previous vintage.
    """

    observation_id: str
    instrument: InstrumentId
    metric: str
    value: Decimal
    unit: ValueUnit
    kind: ObservationKind
    source: EvidenceSource
    effective_at: datetime
    publicly_available_at: datetime
    recorded_at: datetime
    currency: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    supersedes: str | None = None

    def __post_init__(self) -> None:
        _nonempty(self.observation_id, "observation_id")
        if not isinstance(self.instrument, InstrumentId):
            raise TypeError("instrument must be an InstrumentId")
        if not isinstance(self.metric, str) or not re.fullmatch(
            r"[a-z][a-z0-9_]*", self.metric
        ):
            raise ValueError("metric must be a lowercase snake_case identifier")
        _value_and_currency(self.value, self.unit, self.currency)
        if not isinstance(self.kind, ObservationKind):
            raise TypeError("kind must be an ObservationKind")
        if not isinstance(self.source, EvidenceSource):
            raise TypeError("source must be an EvidenceSource")
        for name in ("effective_at", "publicly_available_at", "recorded_at"):
            _aware(getattr(self, name), name)
        if self.source.published_at is not None and (
            self.publicly_available_at < self.source.published_at
        ):
            raise ValueError("public availability cannot precede source publication")
        if self.publicly_available_at > self.source.retrieved_at:
            raise ValueError("public availability cannot follow source retrieval")
        if self.recorded_at < self.source.retrieved_at:
            raise ValueError("recorded_at cannot precede source retrieval")
        if (self.period_start is None) != (self.period_end is None):
            raise ValueError("fiscal periods require both start and end")
        if self.period_start is not None:
            if not isinstance(self.period_start, date) or not isinstance(self.period_end, date):
                raise ValueError("fiscal period endpoints must be dates")
            if self.period_start > self.period_end:
                raise ValueError("fiscal period start must not follow end")
        if self.supersedes is not None:
            _nonempty(self.supersedes, "supersedes")
            if self.supersedes == self.observation_id:
                raise ValueError("an observation cannot supersede itself")

    def to_record(self) -> dict[str, Any]:
        """JSON-compatible representation. Decimal is serialized as a string."""
        source = self.source
        return {
            "observation_id": self.observation_id,
            "instrument": {
                "ticker": self.instrument.ticker,
                "venue": self.instrument.venue,
                "trading_currency": self.instrument.trading_currency,
            },
            "metric": self.metric,
            "value": str(self.value),
            "unit": self.unit.value,
            "kind": self.kind.value,
            "currency": self.currency,
            "effective_at": self.effective_at.isoformat(),
            "publicly_available_at": self.publicly_available_at.isoformat(),
            "recorded_at": self.recorded_at.isoformat(),
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "supersedes": self.supersedes,
            "source": {
                "reference": source.reference,
                "publisher": source.publisher,
                "url": source.url,
                "published_at": source.published_at.isoformat() if source.published_at else None,
                "retrieved_at": source.retrieved_at.isoformat(),
                "redistribution": source.redistribution.value,
            },
        }

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> FinancialObservation:
        """Parse the documented wire format. Reject floating-point JSON numbers."""
        raw_value = record["value"]
        if not isinstance(raw_value, str):
            raise TypeError("value must be a decimal string in the wire format")
        try:
            value = Decimal(raw_value)
        except InvalidOperation as exc:
            raise ValueError("invalid decimal string") from exc
        instrument = InstrumentId(**record["instrument"])
        source_record = record["source"]
        source = EvidenceSource(
            reference=source_record["reference"],
            publisher=source_record["publisher"],
            url=source_record.get("url"),
            published_at=(
                datetime.fromisoformat(source_record["published_at"])
                if source_record.get("published_at") is not None else None
            ),
            retrieved_at=datetime.fromisoformat(source_record["retrieved_at"]),
            redistribution=Redistribution(source_record.get("redistribution", "unknown")),
        )
        return cls(
            observation_id=record["observation_id"],
            instrument=instrument,
            metric=record["metric"],
            value=value,
            unit=ValueUnit(record["unit"]),
            kind=ObservationKind(record["kind"]),
            source=source,
            currency=record.get("currency"),
            effective_at=datetime.fromisoformat(record["effective_at"]),
            publicly_available_at=datetime.fromisoformat(record["publicly_available_at"]),
            recorded_at=datetime.fromisoformat(record["recorded_at"]),
            period_start=(
                date.fromisoformat(record["period_start"])
                if record.get("period_start") is not None else None
            ),
            period_end=(
                date.fromisoformat(record["period_end"])
                if record.get("period_end") is not None else None
            ),
            supersedes=record.get("supersedes"),
        )


@dataclass(frozen=True, slots=True)
class ResearchAssumption:
    """Researcher-supplied hypothesis, intentionally separate from sourced observations."""

    assumption_id: str
    instrument: InstrumentId
    parameter: str
    value: Decimal
    unit: ValueUnit
    rationale: str
    created_at: datetime
    scenario: str = "base"
    currency: str | None = None
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _nonempty(self.assumption_id, "assumption_id")
        if not isinstance(self.instrument, InstrumentId):
            raise TypeError("instrument must be an InstrumentId")
        _nonempty(self.parameter, "parameter")
        _nonempty(self.rationale, "rationale")
        _nonempty(self.scenario, "scenario")
        _aware(self.created_at, "created_at")
        _value_and_currency(self.value, self.unit, self.currency)
        if not isinstance(self.evidence_ids, tuple) or any(
            not isinstance(item, str) or not item.strip() for item in self.evidence_ids
        ):
            raise ValueError("evidence_ids must be a tuple of nonempty strings")


def observations_as_of(
    observations: Iterable[FinancialObservation],
    *,
    cutoff: datetime,
    basis: Literal["public", "recorded"] = "public",
) -> tuple[FinancialObservation, ...]:
    """Return visible observation vintages, hiding only *known* superseded versions.

    'public': records that were publicly available by cutoff, even if ingested later.
    'recorded': records actually captured by cutoff AND publicly available by cutoff.
    These are filters, not proof that an external historical feed is revision-safe.
    """
    _aware(cutoff, "cutoff")
    if basis not in ("public", "recorded"):
        raise ValueError("basis must be 'public' or 'recorded'")
    indexed: dict[str, FinancialObservation] = {}
    for item in observations:
        if not isinstance(item, FinancialObservation):
            raise TypeError("all observations must be FinancialObservation instances")
        if item.observation_id in indexed:
            raise ValueError(f"duplicate observation_id: {item.observation_id}")
        indexed[item.observation_id] = item

    # Cross-instrument revisions and cyclic lineage can otherwise hide valid data.
    for item in indexed.values():
        if item.supersedes is not None and item.supersedes in indexed:
            previous = indexed[item.supersedes]
            if (
                previous.instrument != item.instrument
                or previous.metric != item.metric
                or previous.period_start != item.period_start
                or previous.period_end != item.period_end
            ):
                raise ValueError("a revision must preserve instrument, metric and period")

    # Inconsistent revision lineage can otherwise hide the entire history.
    for item in indexed.values():
        visited: set[str] = set()
        cursor: FinancialObservation | None = item
        while cursor is not None:
            if cursor.observation_id in visited:
                raise ValueError("cyclic supersedes chain")
            visited.add(cursor.observation_id)
            cursor = indexed.get(cursor.supersedes) if cursor.supersedes else None

    visible = [
        item for item in indexed.values()
        if item.publicly_available_at <= cutoff
        and (basis == "public" or item.recorded_at <= cutoff)
    ]
    ids = {item.observation_id for item in visible}
    superseded = {item.supersedes for item in visible if item.supersedes in ids}
    return tuple(item for item in visible if item.observation_id not in superseded)
