"""Model-agnostic research output contracts and deterministic evidence validation.

Checks structural grounding, time availability, and provenance classes.
These checks DO NOT establish whether natural-language claims faithfully
summarize their cited source. Human/source-grounded evaluation is still required.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from .evidence import (
    FinancialObservation,
    InstrumentId,
    ObservationKind,
    ResearchAssumption,
)

SUPPORTED_SKILLS = frozenset({
    "business-analysis",
    "financial-analysis",
    "valuation-analysis",
    "peer-comparison",
    "thesis-challenge",
})


class FindingKind(str, Enum):
    REPORTED_FACT = "reported_fact"
    EXTERNAL_ESTIMATE = "external_estimate"
    ASSUMPTION = "assumption"
    INFERENCE = "inference"
    DATA_GAP = "data_gap"


def _text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty text")


def _utc_aware(value: datetime, name: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


def _ids(values: tuple[str, ...], name: str) -> None:
    if not isinstance(values, tuple) or any(
        not isinstance(value, str) or not value.strip() for value in values
    ):
        raise ValueError(f"{name} must be a tuple of nonempty identifiers")
    if len(values) != len(set(values)):
        raise ValueError(f"{name} must not contain duplicates")


@dataclass(frozen=True, slots=True)
class ResearchFinding:
    finding_id: str
    kind: FindingKind
    text: str
    evidence_ids: tuple[str, ...] = ()
    assumption_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _text(self.finding_id, "finding_id")
        _text(self.text, "text")
        if not isinstance(self.kind, FindingKind):
            raise TypeError("kind must be a FindingKind")
        _ids(self.evidence_ids, "evidence_ids")
        _ids(self.assumption_ids, "assumption_ids")

    def to_record(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "kind": self.kind.value,
            "text": self.text,
            "evidence_ids": list(self.evidence_ids),
            "assumption_ids": list(self.assumption_ids),
        }

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> ResearchFinding:
        evidence_ids = record.get("evidence_ids", [])
        assumption_ids = record.get("assumption_ids", [])
        if not isinstance(evidence_ids, list) or not isinstance(assumption_ids, list):
            raise TypeError("JSON evidence_ids and assumption_ids must be arrays")
        return cls(
            finding_id=record["finding_id"],
            kind=FindingKind(record["kind"]),
            text=record["text"],
            evidence_ids=tuple(evidence_ids),
            assumption_ids=tuple(assumption_ids),
        )


@dataclass(frozen=True, slots=True)
class ResearchReport:
    skill: str
    subjects: tuple[InstrumentId, ...]
    as_of: datetime
    findings: tuple[ResearchFinding, ...]
    questions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.skill not in SUPPORTED_SKILLS:
            raise ValueError("skill must be a supported skill name")
        if not isinstance(self.subjects, tuple) or not self.subjects or any(
            not isinstance(subject, InstrumentId) for subject in self.subjects
        ):
            raise ValueError("subjects must be a nonempty tuple of InstrumentId")
        if len(self.subjects) != len(set(self.subjects)):
            raise ValueError("subjects cannot contain duplicates")
        _utc_aware(self.as_of, "as_of")
        if not isinstance(self.findings, tuple) or not self.findings or any(
            not isinstance(finding, ResearchFinding) for finding in self.findings
        ):
            raise ValueError("findings must be a nonempty tuple of ResearchFinding")
        ids = [finding.finding_id for finding in self.findings]
        if len(ids) != len(set(ids)):
            raise ValueError("finding_id must be unique within a report")
        if not isinstance(self.questions, tuple):
            raise TypeError("questions must be a tuple")
        for question in self.questions:
            _text(question, "question")
        if self.skill == "peer-comparison" and len(self.subjects) < 2:
            raise ValueError("peer-comparison requires at least two instruments")

    def to_record(self) -> dict[str, Any]:
        return {
            "skill": self.skill,
            "as_of": self.as_of.isoformat(),
            "subjects": [
                {
                    "ticker": subject.ticker,
                    "venue": subject.venue,
                    "trading_currency": subject.trading_currency,
                }
                for subject in self.subjects
            ],
            "findings": [finding.to_record() for finding in self.findings],
            "questions": list(self.questions),
        }

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> ResearchReport:
        subjects = record["subjects"]
        findings = record["findings"]
        questions = record.get("questions", [])
        if any(not isinstance(value, list) for value in (subjects, findings, questions)):
            raise ValueError("JSON subjects, findings and questions must be arrays")
        return cls(
            skill=record["skill"],
            as_of=datetime.fromisoformat(record["as_of"]),
            subjects=tuple(InstrumentId(**subject) for subject in subjects),
            findings=tuple(ResearchFinding.from_record(f) for f in findings),
            questions=tuple(questions),
        )


def validate_research_report(
    report: ResearchReport,
    *,
    evidence: Iterable[FinancialObservation],
    assumptions: Iterable[ResearchAssumption] = (),
    basis: Literal["public", "recorded"] = "public",
) -> None:
    """Validate time, references, claim *categories*, and instrument coverage.

    Does not verify the semantic content of `finding.text` or that its numbers
    are derived correctly. Do not advertise passing reports as fact-checked.
    """
    if not isinstance(report, ResearchReport):
        raise TypeError("report must be a ResearchReport")
    if basis not in ("public", "recorded"):
        raise ValueError("basis must be 'public' or 'recorded'")
    evidence_by_id: dict[str, FinancialObservation] = {}
    for item in evidence:
        if not isinstance(item, FinancialObservation):
            raise TypeError("evidence must contain FinancialObservation")
        if item.observation_id in evidence_by_id:
            raise ValueError("duplicate observation ID in evidence")
        evidence_by_id[item.observation_id] = item

    assumptions_by_id: dict[str, ResearchAssumption] = {}
    for item in assumptions:
        if not isinstance(item, ResearchAssumption):
            raise TypeError("assumptions must contain ResearchAssumption")
        if item.assumption_id in assumptions_by_id:
            raise ValueError("duplicate assumption ID")
        assumptions_by_id[item.assumption_id] = item

    subjects = set(report.subjects)

    def resolve_evidence(evidence_id: str, cutoff: datetime) -> FinancialObservation:
        item = evidence_by_id.get(evidence_id)
        if item is None:
            raise ValueError(f"unknown evidence ID: {evidence_id}")
        if item.instrument not in subjects:
            raise ValueError("evidence instrument not included in report subjects")
        if item.publicly_available_at > cutoff:
            raise ValueError("evidence not publicly available by required cutoff")
        if basis == "recorded" and item.recorded_at > cutoff:
            raise ValueError("evidence was not recorded by required cutoff")
        return item

    for finding in report.findings:
        if finding.kind == FindingKind.DATA_GAP:
            if finding.evidence_ids or finding.assumption_ids:
                raise ValueError("data_gap must not pretend to have substantiating inputs")
            continue
        if finding.kind == FindingKind.REPORTED_FACT:
            if not finding.evidence_ids or finding.assumption_ids:
                raise ValueError("reported_fact must cite observations and no assumptions")
        elif finding.kind == FindingKind.EXTERNAL_ESTIMATE:
            if not finding.evidence_ids or finding.assumption_ids:
                raise ValueError("external_estimate must cite observations and no assumptions")
        elif finding.kind == FindingKind.ASSUMPTION:
            if not finding.assumption_ids or finding.evidence_ids:
                raise ValueError("assumption must cite assumptions and no observed facts")
        elif (
            finding.kind == FindingKind.INFERENCE
            and not finding.evidence_ids
            and not finding.assumption_ids
        ):
            raise ValueError("inference requires evidence or assumptions")

        for evidence_id in finding.evidence_ids:
            item = resolve_evidence(evidence_id, report.as_of)
            if finding.kind == FindingKind.REPORTED_FACT and (
                item.kind != ObservationKind.REPORTED
            ):
                raise ValueError("reported_fact must cite only reported observations")
            if finding.kind == FindingKind.EXTERNAL_ESTIMATE and (
                item.kind not in (ObservationKind.ESTIMATE, ObservationKind.CONSENSUS)
            ):
                raise ValueError("external_estimate must cite only external estimates")

        for assumption_id in finding.assumption_ids:
            assumption = assumptions_by_id.get(assumption_id)
            if assumption is None:
                raise ValueError(f"unknown assumption ID: {assumption_id}")
            if assumption.instrument not in subjects:
                raise ValueError("assumption instrument not included in report subjects")
            if assumption.created_at > report.as_of:
                raise ValueError("assumption was created after report cutoff")
            # An assumption must not evade provenance controls via its own citations.
            # Validate against when the assumption was first made, not just this report date.
            for supporting_id in assumption.evidence_ids:
                support = resolve_evidence(supporting_id, assumption.created_at)
                if support.instrument != assumption.instrument:
                    raise ValueError("assumption support instrument does not match hypothesis")


def extract_evidence_ids(report: ResearchReport) -> frozenset[str]:
    """Collect the precise observation IDs referenced by report findings."""
    return frozenset(
        evidence_id for finding in report.findings for evidence_id in finding.evidence_ids
    )
