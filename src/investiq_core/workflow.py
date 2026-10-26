"""Offline research-workflow example and deterministic bundle validation.

A bundle combines attributed observations, researcher hypotheses, a report,
thesis vintages, and a separate hypothetical scenario calculation. This is
not financial advice or a source of current market prices.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal

from .evidence import (
    EvidenceSource,
    FinancialObservation,
    InstrumentId,
    ObservationKind,
    Redistribution,
    ResearchAssumption,
    ValueUnit,
)
from .research import (
    FindingKind,
    ResearchFinding,
    ResearchReport,
    validate_research_report,
)
from .thesis import ThesisSnapshot, ThesisStage, validate_thesis_history
from .valuation import ValuationScenario, evaluate_scenarios

BUNDLE_VERSION = "0.1"


def _utc(day: int) -> datetime:
    return datetime(2025, 3, day, 12, tzinfo=UTC)


def build_synthetic_bundle() -> dict[str, Any]:
    """Generate a fully fictional, reproducible end-to-end research example.

    Historical timestamps in this fixture illustrate temporal semantics.
    They do not describe research that was actually published in 2025.
    """
    instrument = InstrumentId("DEMO", "XNAS", "USD")
    source = EvidenceSource(
        reference="synthetic:fixture-statement",
        publisher="InvestIQ synthetic fixture",
        published_at=_utc(1),
        retrieved_at=_utc(2),
        redistribution=Redistribution.PERMITTED,
    )
    eps = FinancialObservation(
        observation_id="synthetic:eps:v1",
        instrument=instrument,
        metric="diluted_eps",
        value=Decimal(5),
        unit=ValueUnit.MONEY_PER_SHARE,
        currency="USD",
        kind=ObservationKind.REPORTED,
        source=source,
        effective_at=datetime(2024, 12, 31, 12, tzinfo=UTC),
        publicly_available_at=_utc(1),
        recorded_at=_utc(3),
    )
    revenue = FinancialObservation(
        observation_id="synthetic:revenue:v1",
        instrument=instrument,
        metric="revenue",
        value=Decimal("125.50"),
        unit=ValueUnit.MONEY,
        currency="USD",
        kind=ObservationKind.REPORTED,
        source=source,
        effective_at=datetime(2024, 12, 31, 12, tzinfo=UTC),
        publicly_available_at=_utc(1),
        recorded_at=_utc(3),
    )
    growth = ResearchAssumption(
        assumption_id="synthetic:base-growth",
        instrument=instrument,
        parameter="annual_eps_growth",
        value=Decimal("0.10"),
        unit=ValueUnit.RATIO,
        rationale="Illustrative growth assumption, not an analyst forecast",
        created_at=_utc(4),
        scenario="base",
        evidence_ids=(eps.observation_id,),
    )
    report = ResearchReport(
        skill="financial-analysis",
        subjects=(instrument,),
        as_of=_utc(15),
        findings=(
            ResearchFinding(
                "synthetic:f1",
                FindingKind.REPORTED_FACT,
                "In the fictional source, diluted EPS is USD 5 per share.",
                (eps.observation_id,),
            ),
            ResearchFinding(
                "synthetic:f2",
                FindingKind.ASSUMPTION,
                "Assume 10% annual EPS growth in the hypothetical base scenario.",
                assumption_ids=(growth.assumption_id,),
            ),
            ResearchFinding(
                "synthetic:f3",
                FindingKind.DATA_GAP,
                "There is no historical cash-flow series in this synthetic example.",
            ),
        ),
        questions=("Can comparable cash-flow observations be obtained?",),
    )
    initial = ThesisSnapshot(
        thesis_id="synthetic:demo-thesis",
        revision=1,
        instrument=instrument,
        as_of=_utc(15),
        recorded_at=_utc(16),
        method_version="0.1",
        stage=ThesisStage.RESEARCHING,
        statement="Hypothetical earnings growth could change a valuation scenario.",
        revision_reason="Synthetic first research snapshot",
        evidence_ids=(eps.observation_id, revenue.observation_id),
        assumption_ids=(growth.assumption_id,),
        risks=("Future growth assumptions could prove incorrect",),
        invalidation_triggers=("Illustrative EPS fails to grow",),
    )
    revised = replace(
        initial,
        revision=2,
        parent_digest=initial.digest,
        as_of=_utc(22),
        recorded_at=_utc(23),
        stage=ThesisStage.CHALLENGED,
        statement="Hypothetical earnings growth is uncertain and needs cash-flow corroboration.",
        revision_reason="Challenge an unsupported hypothetical growth narrative",
        risks=("Future growth assumptions could prove incorrect", "Missing cash-flow support"),
    )
    return {
        "schema_version": BUNDLE_VERSION,
        "synthetic": True,
        "description": "Fictional offline demonstration; no actual stock or investment advice.",
        "evidence": [eps.to_record(), revenue.to_record()],
        "assumptions": [growth.to_record()],
        "report": report.to_record(),
        "thesis_history": [initial.to_record(), revised.to_record()],
        "valuation": {
            "eps_evidence_id": eps.observation_id,
            "base_growth_assumption_id": growth.assumption_id,
            "hypothetical_entry_price": 75.0,
            "years": 3,
            "scenarios": [
                {"name": "bear", "annual_eps_growth": 0.0, "terminal_pe": 10.0,
                 "probability": 0.25},
                {"name": "base", "annual_eps_growth": 0.10, "terminal_pe": 15.0,
                 "probability": 0.50},
                {"name": "bull", "annual_eps_growth": 0.20, "terminal_pe": 20.0,
                 "probability": 0.25},
            ],
        },
    }


def _array(bundle: Mapping[str, Any], name: str) -> list[Any]:
    value = bundle[name]
    if not isinstance(value, list):
        raise TypeError(f"{name} must be a JSON array")
    return value


def validate_bundle(
    bundle: Mapping[str, Any], *, basis: Literal["public", "recorded"] = "public"
) -> dict[str, Any]:
    """Validate an offline research bundle and calculate its hypothetical scenarios.

    This checks structure, identities, provenance and basic calculations.
    It is NOT a semantic fact-check, financial audit, backtest or strategy.
    """
    if not isinstance(bundle, Mapping):
        raise TypeError("bundle must be a JSON object")
    if bundle.get("schema_version") != BUNDLE_VERSION:
        raise ValueError(f"bundle schema_version must be {BUNDLE_VERSION!r}")
    if basis not in ("public", "recorded"):
        raise ValueError("basis must be public or recorded")

    observations = tuple(
        FinancialObservation.from_record(item) for item in _array(bundle, "evidence")
    )
    assumptions = tuple(
        ResearchAssumption.from_record(item) for item in _array(bundle, "assumptions")
    )
    report = ResearchReport.from_record(bundle["report"])
    history = tuple(
        ThesisSnapshot.from_record(item) for item in _array(bundle, "thesis_history")
    )
    validate_research_report(report, evidence=observations, assumptions=assumptions, basis=basis)
    validate_thesis_history(history, evidence=observations, assumptions=assumptions, basis=basis)
    if history[-1].instrument not in report.subjects:
        raise ValueError("thesis instrument must appear in report subjects")

    valuation = bundle["valuation"]
    if not isinstance(valuation, Mapping):
        raise TypeError("valuation must be a JSON object")
    eps_candidates = [
        obs for obs in observations if obs.observation_id == valuation["eps_evidence_id"]
    ]
    if len(eps_candidates) != 1:
        raise ValueError("valuation must reference exactly one known EPS observation")
    eps = eps_candidates[0]
    if eps.unit != ValueUnit.MONEY_PER_SHARE or eps.metric != "diluted_eps":
        raise ValueError("valuation EPS reference must have diluted_eps per-share units")
    if eps.instrument != history[-1].instrument:
        raise ValueError("valuation EPS instrument must match thesis")
    if eps.publicly_available_at > report.as_of or (
        basis == "recorded" and eps.recorded_at > report.as_of
    ):
        raise ValueError("EPS observation unavailable at research cutoff")

    growth_candidates = [
        hypothesis for hypothesis in assumptions
        if hypothesis.assumption_id == valuation["base_growth_assumption_id"]
    ]
    if len(growth_candidates) != 1:
        raise ValueError("base valuation growth must reference exactly one hypothesis")
    growth = growth_candidates[0]
    if (
        growth.instrument != eps.instrument
        or growth.unit != ValueUnit.RATIO
        or growth.parameter != "annual_eps_growth"
        or growth.created_at > report.as_of
    ):
        raise ValueError("base growth hypothesis is inconsistent with report")
    # Validate support even when the valuation hypothesis is not cited by
    # the narrative report or thesis. Those validators only traverse cited IDs.
    for supporting_id in growth.evidence_ids:
        supporting = [
            item for item in observations if item.observation_id == supporting_id
        ]
        if len(supporting) != 1:
            raise ValueError("unknown or duplicate growth supporting evidence ID")
        item = supporting[0]
        if item.instrument != growth.instrument:
            raise ValueError("growth supporting evidence instrument mismatch")
        if item.publicly_available_at > growth.created_at:
            raise ValueError("growth supporting evidence not publicly available at creation")
        if basis == "recorded" and item.recorded_at > growth.created_at:
            raise ValueError("growth supporting evidence not recorded at creation")
    scenario_records = valuation["scenarios"]
    if not isinstance(scenario_records, list):
        raise TypeError("valuation scenarios must be a JSON array")
    scenarios = tuple(ValuationScenario(**item) for item in scenario_records)
    base_scenarios = [scenario for scenario in scenarios if scenario.name == "base"]
    if len(base_scenarios) != 1 or base_scenarios[0].annual_eps_growth != float(growth.value):
        raise ValueError("base scenario must match its referenced growth assumption")
    analysis = evaluate_scenarios(
        start_eps=float(eps.value),
        initial_price=valuation["hypothetical_entry_price"],
        years=valuation["years"],
        scenarios=scenarios,
    )
    return {
        "validation": "structural_only",
        "schema_version": BUNDLE_VERSION,
        "basis": basis,
        "evidence_count": len(observations),
        "assumption_count": len(assumptions),
        "finding_count": len(report.findings),
        "thesis_revision_count": len(history),
        "scenario_analysis": asdict(analysis),
        "disclaimer": (
            "Hypothetical price-only outcomes; no live price, dividends, "
            "transaction costs, investment advice or validated probabilities."
        ),
    }
