"""Small, deterministic, reusable investment research primitives."""

from .valuation import (
    ValuationScenario,
    annualized_return,
    cagr,
    evaluate_scenarios,
    forward_pe,
    required_eps_growth,
    scenario_return,
)

__all__ = [
    "ValuationScenario",
    "annualized_return",
    "cagr",
    "evaluate_scenarios",
    "forward_pe",
    "required_eps_growth",
    "scenario_return",
]
