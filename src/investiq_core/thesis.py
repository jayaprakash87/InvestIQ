"""Immutable, chain-linked investment research theses.

Portable research-history records; not investment advice, trading actions,
private holdings storage or tamper-proof proof of authorship.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from .evidence import FinancialObservation, InstrumentId, ResearchAssumption


class ThesisStage(str, Enum):
    RESEARCHING = "researching"
    WATCHING = "watching"
    CHALLENGED = "challenged"
    ARCHIVED = "archived"


def _text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must contain text")


def _time(value: datetime, name: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


def _ids(values: tuple[str, ...], label: str) -> None:
    if not isinstance(values, tuple) or any(
        not isinstance(v, str) or not v.strip() for v in values
    ):
        raise ValueError(f"{label} must contain only nonempty strings in a tuple")
    if len(values) != len(set(values)):
        raise ValueError(f"{label} cannot contain duplicate values")


def _json_strings(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise TypeError(f"{field} must be a JSON array")
    return tuple(value)


@dataclass(frozen=True, slots=True)
class ThesisSnapshot:
    """One immutable vintage of a research thesis; versioned by content hash.

    `as_of` is the stated information cutoff. `recorded_at` is the actual
    time the snapshot was captured. Backfilled snapshots are not proof that
    a historical recommendation was genuinely made at `as_of`.
    """

    thesis_id: str
    revision: int
    instrument: InstrumentId
    as_of: datetime
    recorded_at: datetime
    method_version: str
    stage: ThesisStage
    statement: str
    revision_reason: str
    evidence_ids: tuple[str, ...] = ()
    assumption_ids: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    invalidation_triggers: tuple[str, ...] = ()
    parent_digest: str | None = None

    def __post_init__(self) -> None:
        for label in ("thesis_id", "method_version", "statement", "revision_reason"):
            _text(getattr(self, label), label)
        if not isinstance(self.revision, int) or isinstance(self.revision, bool) or self.revision < 1:
            raise ValueError("revision must be a positive integer")
        if not isinstance(self.instrument, InstrumentId):
            raise TypeError("instrument must be an InstrumentId")
        if not isinstance(self.stage, ThesisStage):
            raise TypeError("stage must be a ThesisStage")
        _time(self.as_of, "as_of")
        _time(self.recorded_at, "recorded_at")
        if self.recorded_at < self.as_of:
            raise ValueError("recorded_at cannot precede the as_of research cutoff")
        for label in ("evidence_ids", "assumption_ids", "risks", "invalidation_triggers"):
            _ids(getattr(self, label), label)
        if self.revision == 1 and self.parent_digest is not None:
            raise ValueError("first revision cannot have a parent digest")
        if self.revision > 1 and (
            not isinstance(self.parent_digest, str)
            or re.fullmatch(r"[a-f0-9]{64}", self.parent_digest) is None
        ):
            raise ValueError("subsequent revisions require a SHA-256 parent digest")

    def to_record(self) -> dict[str, Any]:
        return {
            "thesis_id": self.thesis_id,
            "revision": self.revision,
            "instrument": {
                "ticker": self.instrument.ticker,
                "venue": self.instrument.venue,
                "trading_currency": self.instrument.trading_currency,
            },
            "as_of": self.as_of.isoformat(),
            "recorded_at": self.recorded_at.isoformat(),
            "method_version": self.method_version,
            "stage": self.stage.value,
            "statement": self.statement,
            "revision_reason": self.revision_reason,
            "evidence_ids": list(self.evidence_ids),
            "assumption_ids": list(self.assumption_ids),
            "risks": list(self.risks),
            "invalidation_triggers": list(self.invalidation_triggers),
            "parent_digest": self.parent_digest,
        }

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> ThesisSnapshot:
        return cls(
            thesis_id=record["thesis_id"],
            revision=record["revision"],
            instrument=InstrumentId(**record["instrument"]),
            as_of=datetime.fromisoformat(record["as_of"]),
            recorded_at=datetime.fromisoformat(record["recorded_at"]),
            method_version=record["method_version"],
            stage=ThesisStage(record["stage"]),
            statement=record["statement"],
            revision_reason=record["revision_reason"],
            evidence_ids=_json_strings(record.get("evidence_ids", []), "evidence_ids"),
            assumption_ids=_json_strings(record.get("assumption_ids", []), "assumption_ids"),
            risks=_json_strings(record.get("risks", []), "risks"),
            invalidation_triggers=_json_strings(
                record.get("invalidation_triggers", []), "invalidation_triggers"
            ),
            parent_digest=record.get("parent_digest"),
        )

    @property
    def digest(self) -> str:
        """Stable digest over canonical JSON; not an external signature."""
        canonical = json.dumps(
            self.to_record(), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True, slots=True)
class ThesisChange:
    field: str
    before: Any
    after: Any


def compare_thesis_revisions(
    previous: ThesisSnapshot, current: ThesisSnapshot
) -> tuple[ThesisChange, ...]:
    """Return ordered content changes after verifying direct ancestry."""
    if previous.thesis_id != current.thesis_id or previous.instrument != current.instrument:
        raise ValueError("cannot compare unrelated investment theses")
    if current.revision != previous.revision + 1 or current.parent_digest != previous.digest:
        raise ValueError("the second revision must directly follow the first")
    fields = (
        "method_version", "stage", "statement", "revision_reason",
        "evidence_ids", "assumption_ids", "risks", "invalidation_triggers",
    )
    return tuple(
        ThesisChange(name, getattr(previous, name), getattr(current, name))
        for name in fields
        if getattr(previous, name) != getattr(current, name)
    )


def validate_thesis_history(
    snapshots: Iterable[ThesisSnapshot],
    *,
    evidence: Iterable[FinancialObservation] = (),
    assumptions: Iterable[ResearchAssumption] = (),
    basis: Literal["public", "recorded"] = "public",
) -> tuple[ThesisSnapshot, ...]:
    """Check ancestry and referenced inputs for historical consistency.

    Never assert that `as_of` proves a vintage existed historically: only
    independently timestamped source systems can establish that.
    """
    if basis not in ("public", "recorded"):
        raise ValueError("basis must be 'public' or 'recorded'")
    history = tuple(snapshots)
    if not history or any(not isinstance(s, ThesisSnapshot) for s in history):
        raise ValueError("history must contain at least one ThesisSnapshot")
    observations: dict[str, FinancialObservation] = {}
    for item in evidence:
        if not isinstance(item, FinancialObservation):
            raise TypeError("evidence must contain FinancialObservation")
        if item.observation_id in observations:
            raise ValueError("duplicate evidence IDs")
        observations[item.observation_id] = item
    hypotheses: dict[str, ResearchAssumption] = {}
    for item in assumptions:
        if not isinstance(item, ResearchAssumption):
            raise TypeError("assumptions must contain ResearchAssumption")
        if item.assumption_id in hypotheses:
            raise ValueError("duplicate assumption IDs")
        hypotheses[item.assumption_id] = item

    def verify_observation(key: str, subject: InstrumentId, cutoff: datetime) -> None:
        item = observations.get(key)
        if item is None:
            raise ValueError(f"unknown evidence ID: {key}")
        if item.instrument != subject:
            raise ValueError("evidence instrument does not match thesis")
        if item.publicly_available_at > cutoff:
            raise ValueError("evidence not publicly available at research cutoff")
        if basis == "recorded" and item.recorded_at > cutoff:
            raise ValueError("evidence not recorded at research cutoff")

    previous = None
    for snapshot in history:
        if previous is None:
            if snapshot.revision != 1:
                raise ValueError("a history must begin at revision 1")
        else:
            if (
                snapshot.thesis_id != previous.thesis_id
                or snapshot.instrument != previous.instrument
                or snapshot.revision != previous.revision + 1
                or snapshot.parent_digest != previous.digest
            ):
                raise ValueError("broken thesis revision ancestry")
            if snapshot.as_of < previous.as_of or snapshot.recorded_at < previous.recorded_at:
                raise ValueError("thesis revisions cannot move backwards in time")
        for key in snapshot.evidence_ids:
            verify_observation(key, snapshot.instrument, snapshot.as_of)
        for key in snapshot.assumption_ids:
            hypothesis = hypotheses.get(key)
            if hypothesis is None:
                raise ValueError(f"unknown assumption ID: {key}")
            if hypothesis.instrument != snapshot.instrument:
                raise ValueError("assumption instrument does not match thesis")
            if hypothesis.created_at > snapshot.as_of:
                raise ValueError("assumption was created after research cutoff")
            for supporting_key in hypothesis.evidence_ids:
                verify_observation(supporting_key, snapshot.instrument, hypothesis.created_at)
        previous = snapshot
    return history


def export_thesis_jsonl(snapshots: Iterable[ThesisSnapshot]) -> str:
    """Canonical newline-delimited JSON suitable for privately stored research."""
    return "".join(
        json.dumps(s.to_record(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
        for s in snapshots
    )


def import_thesis_jsonl(raw: str) -> tuple[ThesisSnapshot, ...]:
    """Parse snapshots; independently validate lineage/evidence before trusting them."""
    if not isinstance(raw, str):
        raise TypeError("JSONL input must be a string")
    return tuple(
        ThesisSnapshot.from_record(json.loads(line))
        for line in raw.split("\\n")
        if line.strip()
    )
