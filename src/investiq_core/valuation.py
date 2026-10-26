"""Deterministic, explicitly conditional equity-valuation arithmetic.

All prices/EPS must refer to the same share class, currency, and split basis.
Financial source provenance and timing live in investiq_core.evidence.
Results are scenarios, not investment advice or statistical predictions.
No cash dividends, repurchases, dilution or transaction costs are modelled.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from math import isclose, isfinite


def _finite(value: float, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise ValueError(f"{label} must be a finite number")


def _positive(value: float, label: str) -> None:
    _finite(value, label)
    if value <= 0:
        raise ValueError(f"{label} must be positive")


def _years(value: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError("years must be a positive integer")


def _growth(value: float) -> None:
    _finite(value, "annual_eps_growth")
    if value <= -1:
        raise ValueError("annual_eps_growth must be greater than -100%")


def _terminal_price(start_eps: float, annual_eps_growth: float, years: int, terminal_pe: float) -> float:
    _positive(start_eps, "start_eps")
    _growth(annual_eps_growth)
    _years(years)
    _positive(terminal_pe, "terminal_pe")
    try:
        price = start_eps * (1 + annual_eps_growth) ** years * terminal_pe
    except OverflowError as exc:
        raise ValueError("terminal price overflow") from exc
    if not isfinite(price):
        raise ValueError("terminal price must be finite")
    return price


def forward_pe(*, price: float, forward_eps: float) -> float:
    """Forward P/E proxy, valid only for positive forward earnings per share."""
    _positive(price, "price")
    _positive(forward_eps, "forward_eps")
    multiple = price / forward_eps
    if not isfinite(multiple):
        raise ValueError("calculated P/E multiple must be finite")
    return multiple


def cagr(*, start_value: float, end_value: float, years: int) -> float:
    """Compound annual growth rate; start must be positive; end may be zero.

    Use only for economically comparable periods. Negative earnings are invalid.
    """
    _positive(start_value, "start_value")
    _finite(end_value, "end_value")
    _years(years)
    if end_value < 0:
        raise ValueError("end_value cannot be negative")
    ratio = end_value / start_value
    if not isfinite(ratio):
        raise ValueError("growth ratio must be finite")
    return ratio ** (1 / years) - 1


def annualized_return(*, total_return: float, years: int) -> float:
    """Annualized return from a cumulative *price* return, excluding dividends."""
    _finite(total_return, "total_return")
    _years(years)
    if total_return < -1:
        raise ValueError("total_return cannot be less than -100%")
    return (1 + total_return) ** (1 / years) - 1


def scenario_return(
    *,
    start_eps: float,
    annual_eps_growth: float,
    years: int,
    terminal_pe: float,
    initial_price: float,
) -> float:
    """Projected cumulative price return, not annualized; dividends excluded.

    EPS and terminal multiple are *user-specified hypothetical assumptions*.
    Invalid for non-positive earnings or where P/E is not economically relevant.
    """
    _positive(initial_price, "initial_price")
    result = _terminal_price(start_eps, annual_eps_growth, years, terminal_pe) / initial_price - 1
    if not isfinite(result):
        raise ValueError("calculated price return must be finite")
    return result


def required_eps_growth(
    *,
    start_eps: float,
    years: int,
    terminal_pe: float,
    initial_price: float,
    target_annual_return: float,
) -> float:
    """Reverse P/E valuation: annual EPS growth needed for a target price CAGR.

    Does not account for dividends, dilution or multiple path.
    """
    _positive(start_eps, "start_eps")
    _positive(terminal_pe, "terminal_pe")
    _positive(initial_price, "initial_price")
    _years(years)
    _finite(target_annual_return, "target_annual_return")
    if target_annual_return <= -1:
        raise ValueError("target_annual_return must be greater than -100%")
    required_terminal_price = initial_price * (1 + target_annual_return) ** years
    if not isfinite(required_terminal_price):
        raise ValueError("required terminal price must be finite")
    denominator = start_eps * terminal_pe
    if denominator == 0 or not isfinite(denominator):
        raise ValueError("invalid reverse-valuation denominator")
    ratio = required_terminal_price / denominator
    if not isfinite(ratio):
        raise ValueError("required growth ratio must be finite")
    return ratio ** (1 / years) - 1


@dataclass(frozen=True, slots=True)
class ValuationScenario:
    """A subjective scenario, NOT an empirically calibrated probability."""

    name: str
    annual_eps_growth: float
    terminal_pe: float
    probability: float

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("scenario name must be nonempty")
        _growth(self.annual_eps_growth)
        _positive(self.terminal_pe, "terminal_pe")
        _finite(self.probability, "probability")
        if not 0 <= self.probability <= 1:
            raise ValueError("scenario probability must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class ScenarioOutcome:
    name: str
    probability: float
    terminal_price: float
    total_price_return: float
    annualized_price_return: float


@dataclass(frozen=True, slots=True)
class ScenarioAnalysis:
    outcomes: tuple[ScenarioOutcome, ...]
    expected_terminal_price: float
    expected_total_price_return: float
    annualized_return_on_expected_price: float


def evaluate_scenarios(
    *,
    start_eps: float,
    initial_price: float,
    years: int,
    scenarios: Iterable[ValuationScenario],
) -> ScenarioAnalysis:
    """Compute weighted *terminal values*; never average scenario CAGRs.

    Scenarios' probabilities are subjective assumptions; the resulting estimate
    is not a statistically calibrated expected return. Price return only.
    """
    _positive(start_eps, "start_eps")
    _positive(initial_price, "initial_price")
    _years(years)
    scenarios = tuple(scenarios)
    if not scenarios or any(not isinstance(s, ValuationScenario) for s in scenarios):
        raise ValueError("scenarios must be a nonempty sequence of ValuationScenario")
    if len({s.name for s in scenarios}) != len(scenarios):
        raise ValueError("scenario names must be unique")
    total_probability = sum(s.probability for s in scenarios)
    if not isclose(total_probability, 1.0, rel_tol=0, abs_tol=1e-9):
        raise ValueError("scenario probabilities must sum to 1")
    outcomes = []
    for scenario in scenarios:
        terminal_price = _terminal_price(
            start_eps, scenario.annual_eps_growth, years, scenario.terminal_pe
        )
        total_return = terminal_price / initial_price - 1
        outcomes.append(
            ScenarioOutcome(
                name=scenario.name,
                probability=scenario.probability,
                terminal_price=terminal_price,
                total_price_return=total_return,
                annualized_price_return=annualized_return(
                    total_return=total_return, years=years
                ),
            )
        )
    expected_price = sum(outcome.terminal_price * outcome.probability for outcome in outcomes)
    if not isfinite(expected_price):
        raise ValueError("expected price must be finite")
    return ScenarioAnalysis(
        outcomes=tuple(outcomes),
        expected_terminal_price=expected_price,
        expected_total_price_return=expected_price / initial_price - 1,
        annualized_return_on_expected_price=cagr(
            start_value=initial_price, end_value=expected_price, years=years
        ),
    )
