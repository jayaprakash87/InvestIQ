"""Explicit, license-conscious connected-research snapshots and offline replay.

Never write a quote unless its source explicitly grants snapshot retention.
SEC annual facts are retained only for recognized public SEC Companyfacts
references. This is a private user-controlled record, not a provider cache.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from .application.connected_research import CompanyResearchRequest, CompanyResearchResult
from .evidence import ValueUnit
from .fundamentals import AnnualMetricFact
from .market import (
    IssuerId,
    MarketSession,
    Permission,
    PriceAdjustment,
    QuoteFreshness,
    QuoteKind,
    QuoteTimeliness,
)
from .thesis import ThesisSnapshot
from .valuation import ScenarioAnalysis, ValuationScenario, evaluate_scenarios

SNAPSHOT_SCHEMA = 1
REPLAY_METHOD = "connected-annual-pe-v1"
_SEC_REFERENCE = re.compile(
    r"https://data\.sec\.gov/api/xbrl/companyfacts/CIK([0-9]{10})\.json"
)


def _aware(value: datetime, label: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")
    return value.astimezone(UTC)


def _text(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must contain text")


def _decimal(value: Any, label: str) -> Decimal:
    if not isinstance(value, str) or not re.fullmatch(r"-?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?", value):
        raise ValueError(f"{label} must be a decimal string")
    result = Decimal(value)
    if not result.is_finite():
        raise ValueError(f"{label} must be finite")
    return result


@dataclass(frozen=True, slots=True)
class RetainedQuote:
    """Minimal permitted price input, intentionally omitting credentials/scopes."""

    price: Decimal
    currency: str
    quote_id: str
    source_reference: str
    provider: str
    event_at: datetime
    received_at: datetime
    kind: QuoteKind
    session: MarketSession
    timeliness: QuoteTimeliness
    adjustment: PriceAdjustment
    freshness_at_capture: QuoteFreshness

    def __post_init__(self) -> None:
        if not isinstance(self.price, Decimal) or not self.price.is_finite() or self.price <= 0:
            raise ValueError("retained price must be a positive finite Decimal")
        if not isinstance(self.currency, str) or not re.fullmatch(r"[A-Z]{3}", self.currency):
            raise ValueError("retained quote currency must be normalized")
        for name in ("quote_id", "source_reference", "provider"):
            _text(getattr(self, name), name)
        # Capturing a vendor URL containing its API key would leak a credential
        # into an otherwise private but exportable record.
        if (
            "?" in self.source_reference
            or "#" in self.source_reference
            or re.search(r"(?i)(api[_-]?key|access[_-]?token|bearer|secret)\s*[:=]", self.source_reference)
        ):
            raise ValueError("quote source reference must be credential-free")
        for name in ("event_at", "received_at"):
            _aware(getattr(self, name), name)
        if _aware(self.event_at, "event_at") > _aware(self.received_at, "received_at"):
            raise ValueError("retained quote has impossible timestamps")
        for name, cls in (
            ("kind", QuoteKind),
            ("session", MarketSession),
            ("timeliness", QuoteTimeliness),
            ("adjustment", PriceAdjustment),
            ("freshness_at_capture", QuoteFreshness),
        ):
            if not isinstance(getattr(self, name), cls):
                raise TypeError(f"{name} must be {cls.__name__}")


@dataclass(frozen=True, slots=True)
class ResearchSnapshot:
    """Immutable user-triggered inputs; integrity hash covers the entire record."""

    thesis: ThesisSnapshot
    saved_at: datetime
    researched_at: datetime
    issuer: IssuerId
    annual_facts: tuple[AnnualMetricFact, ...]
    quote: RetainedQuote | None
    share_basis_confirmed: bool
    share_basis_rationale: str | None
    max_quote_age_seconds: str
    scenario_years: int | None = None
    scenarios: tuple[ValuationScenario, ...] = ()
    method_version: str = REPLAY_METHOD
    schema_version: int = SNAPSHOT_SCHEMA

    def __post_init__(self) -> None:
        if not isinstance(self.thesis, ThesisSnapshot):
            raise TypeError("thesis must be ThesisSnapshot")
        if self.schema_version != SNAPSHOT_SCHEMA or self.method_version != REPLAY_METHOD:
            raise ValueError("unsupported snapshot schema or replay methodology")
        if self.thesis.method_version != self.method_version:
            raise ValueError("thesis and snapshot method versions must match")
        saved = _aware(self.saved_at, "saved_at")
        researched = _aware(self.researched_at, "researched_at")
        if saved < researched or saved != _aware(self.thesis.recorded_at, "thesis.recorded_at"):
            raise ValueError("snapshot time must equal thesis recording time, after research")
        if _aware(self.thesis.as_of, "thesis.as_of") > saved:
            raise ValueError("thesis information cutoff cannot follow recording")
        if _aware(self.thesis.as_of, "thesis.as_of") < researched:
            raise ValueError("current-research thesis cutoff cannot predate the connected analysis")
        if not isinstance(self.issuer, IssuerId):
            raise TypeError("issuer must be IssuerId")
        if not isinstance(self.annual_facts, tuple):
            raise TypeError("annual_facts must be a tuple")
        if len({fact.metric for fact in self.annual_facts}) != len(self.annual_facts):
            raise ValueError("duplicate annual metric in saved evidence")
        for fact in self.annual_facts:
            if not isinstance(fact, AnnualMetricFact) or fact.issuer != self.issuer:
                raise ValueError("annual fact must match issuer")
            match = _SEC_REFERENCE.fullmatch(fact.source_reference)
            if (
                match is None
                or self.issuer.namespace != "SEC_CIK"
                or int(match.group(1)) != int(self.issuer.value)
                or fact.taxonomy != "us-gaap"
            ):
                raise ValueError("only attributed SEC Companyfacts may be retained")
            if _aware(fact.retrieved_at, "fact.retrieved_at") > saved:
                raise ValueError("annual fact was retrieved after snapshot creation")
            if fact.filed_on >= researched.date():
                raise ValueError("same-day/late annual fact cannot be saved for research cutoff")
        if self.quote is not None:
            if not isinstance(self.quote, RetainedQuote):
                raise TypeError("quote must be RetainedQuote")
            if self.quote.currency != self.thesis.instrument.trading_currency:
                raise ValueError("retained quote currency must match listing")
            if _aware(self.quote.received_at, "received_at") > saved:
                raise ValueError("quote receipt cannot follow snapshot")
            if self.quote.kind != QuoteKind.CLOSE:
                raise ValueError("snapshot supports the price CLOSE kind only")
        if type(self.share_basis_confirmed) is not bool:
            raise TypeError("share_basis_confirmed must be boolean")
        if self.share_basis_confirmed:
            _text(self.share_basis_rationale, "share_basis_rationale")
        elif self.share_basis_rationale is not None:
            raise ValueError("unconfirmed basis must not carry a confirmation rationale")
        if _decimal(self.max_quote_age_seconds, "max_quote_age_seconds") <= 0:
            raise ValueError("max_quote_age_seconds must be positive")
        if (self.scenario_years is None) != (not self.scenarios):
            raise ValueError("scenario_years and scenarios must be supplied together")
        if self.scenario_years is not None and (
            type(self.scenario_years) is not int or self.scenario_years <= 0
        ):
            raise ValueError("scenario_years must be positive integer")
        if not isinstance(self.scenarios, tuple) or any(
            not isinstance(s, ValuationScenario) for s in self.scenarios
        ):
            raise TypeError("scenarios must be a tuple of ValuationScenario")
        # The existing thesis ledger's evidence/assumption IDs require their
        # own separately retained FinancialObservation/ResearchAssumption objects.
        # PR 5 uses independently attributed annual facts and scenario inputs.
        if self.thesis.evidence_ids or self.thesis.assumption_ids:
            raise ValueError("external thesis IDs need independently archived source objects")

    def to_record(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "method_version": self.method_version,
            "thesis": self.thesis.to_record(),
            "saved_at": self.saved_at.isoformat(),
            "researched_at": self.researched_at.isoformat(),
            "issuer": {"namespace": self.issuer.namespace, "value": self.issuer.value},
            "annual_facts": [
                {
                    "metric": f.metric, "value": str(f.value), "unit": f.unit.value,
                    "currency": f.currency, "period_start": f.period_start.isoformat(),
                    "period_end": f.period_end.isoformat(), "accession": f.accession,
                    "filed_on": f.filed_on.isoformat(), "source_reference": f.source_reference,
                    "taxonomy": f.taxonomy, "tag": f.tag,
                    "retrieved_at": f.retrieved_at.isoformat(),
                }
                for f in self.annual_facts
            ],
            "quote": (
                {
                    "price": str(self.quote.price), "currency": self.quote.currency,
                    "quote_id": self.quote.quote_id,
                    "source_reference": self.quote.source_reference,
                    "provider": self.quote.provider,
                    "event_at": self.quote.event_at.isoformat(),
                    "received_at": self.quote.received_at.isoformat(),
                    "kind": self.quote.kind.value, "session": self.quote.session.value,
                    "timeliness": self.quote.timeliness.value,
                    "adjustment": self.quote.adjustment.value,
                    "freshness_at_capture": self.quote.freshness_at_capture.value,
                }
                if self.quote is not None else None
            ),
            "quote_omitted": self.quote is None,
            "share_basis_confirmed": self.share_basis_confirmed,
            "share_basis_rationale": self.share_basis_rationale,
            "max_quote_age_seconds": self.max_quote_age_seconds,
            "scenario_years": self.scenario_years,
            "scenarios": [
                {
                    "name": s.name, "annual_eps_growth": s.annual_eps_growth,
                    "terminal_pe": s.terminal_pe, "probability": s.probability,
                }
                for s in self.scenarios
            ],
        }

    @classmethod
    def from_record(cls, raw: dict[str, Any]) -> ResearchSnapshot:
        if not isinstance(raw, dict):
            raise TypeError("snapshot payload must be an object")
        thesis = ThesisSnapshot.from_record(raw["thesis"])
        issuer = IssuerId(**raw["issuer"])
        fact_rows = raw["annual_facts"]
        if not isinstance(fact_rows, list):
            raise TypeError("annual_facts must be a list")
        facts = tuple(
            AnnualMetricFact(
                issuer=issuer, metric=f["metric"], value=_decimal(f["value"], "annual value"),
                unit=ValueUnit(f["unit"]), currency=f["currency"],
                period_start=date.fromisoformat(f["period_start"]),
                period_end=date.fromisoformat(f["period_end"]),
                accession=f["accession"], filed_on=date.fromisoformat(f["filed_on"]),
                source_reference=f["source_reference"], taxonomy=f["taxonomy"],
                tag=f["tag"], retrieved_at=datetime.fromisoformat(f["retrieved_at"]),
            )
            for f in fact_rows
        )
        q = raw["quote"]
        if (q is None) != raw["quote_omitted"]:
            raise ValueError("quote omission marker is inconsistent")
        quote = (
            RetainedQuote(
                price=_decimal(q["price"], "price"),
                currency=q["currency"], quote_id=q["quote_id"],
                source_reference=q["source_reference"], provider=q["provider"],
                event_at=datetime.fromisoformat(q["event_at"]),
                received_at=datetime.fromisoformat(q["received_at"]),
                kind=QuoteKind(q["kind"]), session=MarketSession(q["session"]),
                timeliness=QuoteTimeliness(q["timeliness"]),
                adjustment=PriceAdjustment(q["adjustment"]),
                freshness_at_capture=QuoteFreshness(q["freshness_at_capture"]),
            )
            if q is not None else None
        )
        series = raw["scenarios"]
        if not isinstance(series, list):
            raise TypeError("scenarios must be a list")
        return cls(
            thesis=thesis, saved_at=datetime.fromisoformat(raw["saved_at"]),
            researched_at=datetime.fromisoformat(raw["researched_at"]), issuer=issuer,
            annual_facts=facts, quote=quote,
            share_basis_confirmed=raw["share_basis_confirmed"],
            share_basis_rationale=raw["share_basis_rationale"],
            max_quote_age_seconds=raw["max_quote_age_seconds"],
            scenario_years=raw["scenario_years"],
            scenarios=tuple(ValuationScenario(**s) for s in series),
            method_version=raw["method_version"], schema_version=raw["schema_version"],
        )

    @property
    def digest(self) -> str:
        return hashlib.sha256(_canonical(self.to_record())).hexdigest()


@dataclass(frozen=True, slots=True)
class ReplayedResearch:
    snapshot_digest: str
    annual_pe_proxy: Decimal | None
    scenarios: ScenarioAnalysis | None
    warnings: tuple[str, ...]


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def capture_research_snapshot(
    result: CompanyResearchResult,
    request: CompanyResearchRequest,
    thesis: ThesisSnapshot,
    *,
    saved_at: datetime,
) -> ResearchSnapshot:
    """Explicit save-intent conversion, not an automatic on-fetch hook.

    The quote is withheld entirely unless rights.snapshot=ALLOWED.
    """
    if not isinstance(result, CompanyResearchResult) or not isinstance(
        request, CompanyResearchRequest
    ):
        raise TypeError("capture requires connected result and request")
    if thesis.instrument != request.listing.instrument:
        raise ValueError("thesis instrument differs from researched instrument")
    expected_issuer = f"{request.listing.issuer.namespace}:{request.listing.issuer.value}"
    if result.issuer != expected_issuer:
        raise ValueError("research result issuer differs from selected listing")
    q = result.quote.quote
    if q.instrument != thesis.instrument:
        raise ValueError("quote instrument differs from thesis")
    _aware(saved_at, "saved_at")
    if _aware(thesis.recorded_at, "recorded_at") != _aware(saved_at, "saved_at"):
        raise ValueError("thesis recording time must match explicit save")
    captured = None
    if q.rights.snapshot is Permission.ALLOWED:
        captured = RetainedQuote(
            price=q.price, currency=q.currency, quote_id=q.quote_id,
            source_reference=q.source_reference, provider=q.provider,
            event_at=q.event_at, received_at=q.received_at, kind=q.kind,
            session=q.session, timeliness=q.timeliness, adjustment=q.adjustment,
            freshness_at_capture=result.quote.freshness,
        )
    record = ResearchSnapshot(
        thesis=thesis, saved_at=saved_at, researched_at=result.observed_at,
        issuer=request.listing.issuer, annual_facts=result.annual_facts, quote=captured,
        share_basis_confirmed=request.analyst_confirmed_share_basis,
        share_basis_rationale=request.share_basis_rationale,
        max_quote_age_seconds=str(Decimal(str(request.max_quote_age.total_seconds()))),
        scenario_years=request.scenario_years, scenarios=request.scenarios,
    )
    replay_snapshot(record)  # fail early on impossible/incompatible captured assumptions
    return record


def replay_snapshot(snapshot: ResearchSnapshot) -> ReplayedResearch:
    """Offline deterministic replay. Does not call providers or current clocks."""
    if not isinstance(snapshot, ResearchSnapshot):
        raise TypeError("snapshot must be ResearchSnapshot")
    eps = next((f for f in snapshot.annual_facts if f.metric == "diluted_eps"), None)
    price = snapshot.quote
    warnings: list[str] = []
    pe: Decimal | None = None
    analysis: ScenarioAnalysis | None = None
    if price is None:
        warnings.append(
            "Price and all price-derived outputs withheld: source snapshot rights not granted."
        )
    elif eps is None:
        warnings.append("No retained annual diluted EPS; P/E unavailable.")
    elif eps.value <= 0:
        warnings.append("Nonpositive diluted EPS; P/E is not applicable.")
    elif eps.unit != ValueUnit.MONEY_PER_SHARE or eps.currency != price.currency:
        warnings.append("Retained EPS and quote currency/unit mismatch; no implicit FX.")
    elif _aware(price.event_at, "event_at").date() <= eps.filed_on:
        warnings.append("Quote event date is not after EPS filing date.")
    elif not snapshot.share_basis_confirmed:
        warnings.append("No analyst-confirmed share/split basis; annual P/E withheld.")
    elif price.freshness_at_capture is not QuoteFreshness.WITHIN_POLICY:
        warnings.append("Quote was not fresh under the saved policy at capture.")
    else:
        pe = price.price / eps.value
        if snapshot.scenarios:
            analysis = evaluate_scenarios(
                start_eps=float(eps.value), initial_price=float(price.price),
                years=snapshot.scenario_years, scenarios=snapshot.scenarios,
            )
    if snapshot.scenarios and analysis is None:
        warnings.append("Requested scenario evaluation unavailable for retained inputs.")
    if price is not None:
        warnings.append("This is historical captured data, NOT an updated live quote.")
    warnings.append("Annual EPS is reported, not forward or TTM; no intraday SEC release proof.")
    return ReplayedResearch(snapshot.digest, pe, analysis, tuple(warnings))
