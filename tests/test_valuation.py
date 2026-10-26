import pytest

from investiq_core.valuation import scenario_return


def test_scenario_return_is_reproducible() -> None:
    result = scenario_return(
        start_eps=5.0, annual_eps_growth=0.10, years=3, terminal_pe=15.0,
        initial_price=75.0,
    )
    assert result == pytest.approx(0.331)


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
    ],
)
def test_invalid_inputs_are_rejected(kwargs: dict) -> None:
    params = {"start_eps": 5.0, "annual_eps_growth": 0.1, "years": 3,
              "terminal_pe": 15.0, "initial_price": 75.0}
    params.update(kwargs)
    with pytest.raises(ValueError):
        scenario_return(**params)
