"""Deterministic, no-provider scenario sandbox using existing InvestIQ math.

All inputs are user-authored hypothetical values and never substituted from
unverified SEC EPS or an unlicensed/mismatched quote. Nothing is saved.
"""

from __future__ import annotations

import hashlib
import json
from math import isfinite
from typing import Any

from .valuation import ValuationScenario, evaluate_scenarios

_NAMES = ("bear", "base", "bull")


def _number(value: Any, label: str, *, lower: float, upper: float) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (float, int))
        or not isfinite(value)
        or not lower <= value <= upper
    ):
        raise ValueError(f"{label} must be finite and between {lower} and {upper}")
    return float(value)


def evaluate_hypothetical(data: dict[str, Any]) -> dict[str, Any]:
    """Validate a deliberately small investor-controlled scenario schema."""
    if not isinstance(data, dict) or set(data) != {
        "start_eps", "initial_price", "years", "scenarios",
    }:
        raise ValueError("Expected exactly EPS, entry price, years and scenarios")
    eps = _number(data["start_eps"], "hypothetical EPS", lower=0.01, upper=100_000)
    entry = _number(data["initial_price"], "hypothetical entry price", lower=0.01, upper=1e6)
    years = data["years"]
    if type(years) is not int or not 1 <= years <= 15:
        raise ValueError("Scenario horizon must be a whole number of years from 1 to 15")
    raw = data["scenarios"]
    if not isinstance(raw, list) or len(raw) != 3:
        raise ValueError("Exactly three distinct bear/base/bull scenarios are required")
    scenarios: list[ValuationScenario] = []
    normalized: list[dict[str, float | str]] = []
    for expected, item in zip(_NAMES, raw, strict=True):
        if not isinstance(item, dict) or set(item) != {
            "name", "annual_growth_percent", "terminal_pe", "weight_percent",
        } or item["name"] != expected:
            raise ValueError("Scenarios must be bear, base and bull with supported fields")
        growth = _number(
            item["annual_growth_percent"], expected + " growth percent",
            lower=-95, upper=200,
        )
        multiple = _number(
            item["terminal_pe"], expected + " terminal P/E", lower=0.1, upper=100,
        )
        weight = _number(
            item["weight_percent"], expected + " weight percent", lower=0, upper=100,
        )
        scenarios.append(ValuationScenario(
            name=expected, annual_eps_growth=growth / 100,
            terminal_pe=multiple, probability=weight / 100,
        ))
        normalized.append({
            "name": expected, "annual_growth_percent": growth,
            "terminal_pe": multiple, "weight_percent": weight,
        })
    if abs(sum(s["weight_percent"] for s in normalized) - 100) > 1e-9:
        raise ValueError("Subjective scenario weights must add up to exactly 100%")
    result = evaluate_scenarios(
        start_eps=eps, initial_price=entry, years=years, scenarios=scenarios,
    )
    input_values = {
        "start_eps": eps, "initial_price": entry,
        "years": years, "scenarios": normalized,
    }
    digest = hashlib.sha256(
        json.dumps(input_values, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "mode": "manual_hypothetical_no_provider_data",
        "method": "investiq_core.valuation.evaluate_scenarios",
        "currency_assumption": "USD",
        "input_sha256": digest,
        "inputs": input_values,
        "outcomes": [{
            "name": outcome.name,
            "weight_percent": outcome.probability * 100,
            "terminal_price": outcome.terminal_price,
            "total_price_return_percent": outcome.total_price_return * 100,
            "annualized_price_return_percent": outcome.annualized_price_return * 100,
        } for outcome in result.outcomes],
        "weighted_terminal_price": result.expected_terminal_price,
        "weighted_price_return_percent": result.expected_total_price_return * 100,
        "annualized_return_on_weighted_price_percent": (
            result.annualized_return_on_expected_price * 100
        ),
        "disclosures": [
            "All EPS, entry-price, growth, terminal P/E and weights are hypothetical user inputs.",
            "Numbers are deterministic price-only scenarios, not model predictions or recommendations.",
            "Weights are subjective, not statistically calibrated outcome probabilities.",
            "EPS and entry price must refer to the same share class, USD currency and split basis; compatibility is not independently verified.",
            "The calculation excludes dividends, dilution, taxes, fees and multiple changes before the terminal year.",
            "Weighted terminal price is calculated before annualizing; scenario CAGRs are not averaged.",
            "This is not based on live quotes, provider EPS, an AI response or a saved thesis.",
        ],
    }
