"""Deterministic valuation arithmetic.

Inputs must be explicit, date-aligned and attributed by calling applications.
No probabilities or future earnings growth are inferred from past observations.
"""

from math import isfinite


def scenario_return(
    *,
    start_eps: float,
    annual_eps_growth: float,
    years: int,
    terminal_pe: float,
    initial_price: float,
) -> float:
    """Return projected *price* return (not CAGR), excluding dividends and dilution.

    Terminal price = start_eps * (1 + growth)**years * terminal_pe.
    Growth and terminal multiple are hypothetical assumptions, not forecasts.
    This EPS/P-E model is not suitable for non-positive earnings.
    """
    values = (start_eps, annual_eps_growth, terminal_pe, initial_price)
    if not all(isfinite(x) for x in values):
        raise ValueError("Inputs must be finite")
    if start_eps <= 0 or terminal_pe <= 0 or initial_price <= 0:
        raise ValueError("EPS, P/E, and price must be positive")
    if not isinstance(years, int) or isinstance(years, bool) or years <= 0:
        raise ValueError("years must be a positive integer")
    if annual_eps_growth <= -1:
        raise ValueError("annual_eps_growth must be greater than -100%")
    terminal_price = start_eps * (1 + annual_eps_growth) ** years * terminal_pe
    if not isfinite(terminal_price):
        raise ValueError("Calculated terminal price must be finite")
    return terminal_price / initial_price - 1
