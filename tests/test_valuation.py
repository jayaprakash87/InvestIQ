import pytest

from investiq_core.valuation import (
    ValuationScenario,
    annualized_return,
    cagr,
    evaluate_scenarios,
    forward_pe,
    required_eps_growth,
    scenario_return,
)


def test_scenario_return_is_reproducible() -> None:
    result = scenario_return(
        start_eps=5.0, annual_eps_growth=0.10, years=3, terminal_pe=15.0,
        initial_price=75.0,
    )
    assert result == pytest.approx(0.331)


def test_cagr_and_price_return_are_not_interchangeable() -> None:
    assert cagr(start_value=75, end_value=99.825, years=3) == pytest.approx(0.10)
    assert annualized_return(total_return=0.331, years=3) == pytest.approx(0.10)
    assert cagr(start_value=100, end_value=0, years=2) == -1


def test_reverse_valuation_matches_forward_scenario() -> None:
    required = required_eps_growth(
        start_eps=5, years=3, terminal_pe=15, initial_price=75, target_annual_return=0.10
    )
    assert required == pytest.approx(0.10)
    assert forward_pe(price=75, forward_eps=5) == 15


def test_expected_terminal_value_not_weighted_average_of_cagrs() -> None:
    analysis = evaluate_scenarios(
        start_eps=5, initial_price=75, years=3,
        scenarios=[
            ValuationScenario("bear", 0.00, 10, 0.25),
            ValuationScenario("base", 0.10, 15, 0.50),
            ValuationScenario("bull", 0.20, 20, 0.25),
        ],
    )
    assert analysis.expected_terminal_price == pytest.approx(105.6125)
    assert analysis.expected_total_price_return == pytest.approx(105.6125 / 75 - 1)
    assert analysis.annualized_return_on_expected_price == pytest.approx(
        (105.6125 / 75) ** (1 / 3) - 1
    )
    weighted_cagr = sum(
        outcome.annualized_price_return * outcome.probability
        for outcome in analysis.outcomes
    )
    assert weighted_cagr != pytest.approx(analysis.annualized_return_on_expected_price)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"start_eps": 0},
        {"initial_price": 0},
        {"terminal_pe": -1},
        {"years": 0},
        {"years": 1.5},
        {"years": True},
        {"annual_eps_growth": -1},
        {"start_eps": float("nan")},
        {"terminal_pe": float("inf")},
        {"annual_eps_growth": True},
    ],
)
def test_invalid_inputs_are_rejected(kwargs: dict) -> None:
    params = {"start_eps": 5.0, "annual_eps_growth": 0.1, "years": 3,
              "terminal_pe": 15.0, "initial_price": 75.0}
    params.update(kwargs)
    with pytest.raises(ValueError):
        scenario_return(**params)


@pytest.mark.parametrize(
    "target", [-1.0, float("nan"), float("inf"), True],
)
def test_invalid_reverse_returns(target: float) -> None:
    with pytest.raises(ValueError):
        required_eps_growth(
            start_eps=5, years=3, terminal_pe=15,
            initial_price=75, target_annual_return=target,
        )


def test_negative_earnings_not_suitable_for_pe() -> None:
    with pytest.raises(ValueError):
        forward_pe(price=50, forward_eps=-2)
    with pytest.raises(ValueError):
        cagr(start_value=-10, end_value=5, years=3)
    with pytest.raises(ValueError):
        annualized_return(total_return=-1.01, years=2)


@pytest.mark.parametrize(
    "scenarios",
    [
        [],
        [ValuationScenario("base", 0.1, 20, 0.7)],
        [ValuationScenario("base", 0.1, 20, 0.5),
         ValuationScenario("base", 0.2, 10, 0.5)],
        [ValuationScenario("base", 0.1, 20, 0.5), "not a scenario"],
    ],
)
def test_scenario_structure_must_be_valid(scenarios: list) -> None:
    with pytest.raises(ValueError):
        evaluate_scenarios(start_eps=5, initial_price=100, years=3, scenarios=scenarios)


def test_invalid_scenario_assumptions() -> None:
    for values in [
        ("", 0.1, 20, 1),
        ("base", -1, 20, 1),
        ("base", 0.1, 0, 1),
        ("base", 0.1, 20, -0.1),
        ("base", 0.1, 20, 1.1),
    ]:
        with pytest.raises(ValueError):
            ValuationScenario(*values)
