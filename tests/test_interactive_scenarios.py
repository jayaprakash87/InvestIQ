"""PR5 deterministic hypothetical scenario UI contract and numerical guards."""

from __future__ import annotations

from math import isclose

import pytest

from investiq_core.interactive_scenarios import evaluate_hypothetical
from investiq_core.valuation import ValuationScenario, evaluate_scenarios


def inputs():
    return {
        "start_eps": 4.0,
        "initial_price": 75.0,
        "years": 5,
        "scenarios": [
            {"name": "bear", "annual_growth_percent": -5, "terminal_pe": 10, "weight_percent": 25},
            {"name": "base", "annual_growth_percent": 5, "terminal_pe": 15, "weight_percent": 50},
            {"name": "bull", "annual_growth_percent": 15, "terminal_pe": 20, "weight_percent": 25},
        ],
    }


def test_workbench_uses_canonical_python_core_without_prices_from_providers():
    values = inputs()
    result = evaluate_hypothetical(values)
    expected = evaluate_scenarios(
        start_eps=4.0, initial_price=75.0, years=5,
        scenarios=[
            ValuationScenario("bear", -0.05, 10, 0.25),
            ValuationScenario("base", 0.05, 15, 0.5),
            ValuationScenario("bull", 0.15, 20, 0.25),
        ],
    )
    assert result["mode"] == "manual_hypothetical_no_provider_data"
    assert result["method"] == "investiq_core.valuation.evaluate_scenarios"
    assert result["currency_assumption"] == "USD"
    assert result["weighted_terminal_price"] == expected.expected_terminal_price
    assert result["annualized_return_on_weighted_price_percent"] == (
        expected.annualized_return_on_expected_price * 100
    )
    assert len(result["outcomes"]) == 3
    assert result["outcomes"][0]["terminal_price"] == expected.outcomes[0].terminal_price
    assert result["outcomes"][1]["total_price_return_percent"] == (
        expected.outcomes[1].total_price_return * 100
    )
    assert "not statistically calibrated" in " ".join(result["disclosures"]).lower()
    assert "no model" in " ".join(result["disclosures"]).lower() or (
        "AI response" in " ".join(result["disclosures"])
    )


def test_assumption_change_recalculates_immediately_and_deterministically():
    base = inputs()
    baseline = evaluate_hypothetical(base)
    assert baseline["input_sha256"] == evaluate_hypothetical(base)["input_sha256"]
    altered = inputs()
    altered["scenarios"][1]["terminal_pe"] = 18
    recalculated = evaluate_hypothetical(altered)
    assert recalculated["weighted_terminal_price"] > baseline["weighted_terminal_price"]
    assert recalculated["input_sha256"] != baseline["input_sha256"]
    assert base["scenarios"][1]["terminal_pe"] == 15  # no input mutation
    assert isclose(
        recalculated["annualized_return_on_weighted_price_percent"],
        ((recalculated["weighted_terminal_price"] / 75.0) ** (1 / 5) - 1) * 100,
    )
    # Price-return CAGR on weighted terminal price, NOT weighted average of CAGRs.
    average_cagr = sum(
        x["annualized_price_return_percent"] * x["weight_percent"] / 100
        for x in recalculated["outcomes"]
    )
    assert not isclose(average_cagr, recalculated["annualized_return_on_weighted_price_percent"])


@pytest.mark.parametrize("modify", [
    lambda x: x.update({"start_eps": 0}),
    lambda x: x.update({"start_eps": -2}),
    lambda x: x.update({"start_eps": float("nan")}),
    lambda x: x.update({"start_eps": "4"}),
    lambda x: x.update({"initial_price": 0}),
    lambda x: x.update({"initial_price": float("inf")}),
    lambda x: x.update({"years": True}),
    lambda x: x.update({"years": 5.5}),
    lambda x: x.update({"years": 16}),
    lambda x: x.update({"random": "extra"}),
    lambda x: x["scenarios"][0].update({"annual_growth_percent": -100}),
    lambda x: x["scenarios"][0].update({"annual_growth_percent": 201}),
    lambda x: x["scenarios"][0].update({"terminal_pe": 0}),
    lambda x: x["scenarios"][1].update({"weight_percent": -1}),
    lambda x: x["scenarios"][1].update({"weight_percent": 40}),
    lambda x: x["scenarios"][1].update({"name": "bear"}),
    lambda x: x["scenarios"].pop(),
    lambda x: x["scenarios"][0].update({"api_key": "unexpected-secret"}),
])
def test_invalid_or_unsupported_assumptions_fail_closed(modify):
    request = inputs()
    modify(request)
    with pytest.raises((ValueError, TypeError)):
        evaluate_hypothetical(request)


def test_no_auto_quote_or_ai_sources_in_payload_contract():
    result = evaluate_hypothetical(inputs())
    assert result["inputs"]["start_eps"] == 4.0
    assert result["inputs"]["initial_price"] == 75.0
    assert result["inputs"]["scenarios"][0]["name"] == "bear"
    assert result["disclosures"]
    assert "quote" not in result
    assert "model_executed" not in result
    assert "provider" not in result


def test_interactive_browser_requires_fresh_model_consent_and_invalidate_scenarios():
    from importlib.resources import files

    js = files("investiq_core").joinpath("web", "connect.js").read_text("utf-8")
    html = files("investiq_core").joinpath("web", "index.html").read_text("utf-8")
    assert "innerHTML" not in js
    assert "textContent" in js
    assert 'questionHistory = questionHistory.slice(-5)' in js
    assert 'consent_external_sec_data: $("ai-consent").checked' in js
    assert '$("ai-consent").checked = false' in js
    assert "Earlier questions and answers are" in html
    assert "scenarioGeneration += 1" in js
    assert "generation !== scenarioGeneration" in js
    assert "selected !== candidate" in js
    assert '"/api/v1/research/scenarios"' in js
    assert "manualScenarioInputs()" in js
    assert "scenario-form" in html
    assert "Hypothetical" in html
