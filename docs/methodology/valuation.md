# Valuation Arithmetic and Scenario Conventions — v0.1

These are transparent **calculation primitives**, not stock forecasts, price targets or investment advice. Every input should be validated against attributed `FinancialObservation` records and explicitly entered `ResearchAssumption` values before production use.

## Formulas
- Forward P/E = price / positive forward EPS.
- CAGR = (end / start)^(1 / years) - 1; start positive and end nonnegative.
- Terminal EPS = positive starting EPS × (1 + assumed annual EPS growth)^years.
- Terminal price = terminal EPS × assumed terminal P/E.
- Cumulative **price** return = terminal price / entry price - 1.
- Annualized **price** return = (1 + cumulative price return)^(1 / years) - 1.
- Required EPS growth for target annual price return = (entry price × (1 + target return)^years / (starting EPS × terminal P/E))^(1 / years) - 1.

`evaluate_scenarios` uses explicit bear/base/bull (or other) inputs, weights, and the weighted terminal *price*. It annualizes that weighted terminal price. It intentionally does **not** take the average of scenario annualized return rates, which is a different and generally misleading aggregation.

Probabilities are subjective scenario weights, **not** statistically calibrated likelihoods. No factor or ranking receives automatic predictive credibility.

## Boundaries
- Prices and EPS must use the same instrument/share class, split adjustment and currency. No implied currency conversion.\n- In the offline research-bundle workflow, a hypothetical entry price is assumed to use the instrument's trading currency. The optional `hypothetical_entry_price_currency` field may state it explicitly; cross-currency EPS requires a separate, attributed FX conversion workflow and is **rejected** until one exists. The output includes `valuation_currency`. Legacy 0.1 bundles without the optional field retain this trading-currency convention.
- The EPS/P-E method is not applicable to non-positive earnings or industries where earnings multiples are misleading; choose an alternative economic model.
- These examples do not include cash dividends, buybacks, new equity issuance, debt financing changes, tax, leverage, slippage or management-execution risk.
- Compound growth is only meaningful for economically comparable periods; do not assume a trough or peak year represents normalized future earnings.
- Report both total and annualized price return with explicit time horizons; do not label either an IRR that includes cash flows.
- Floating-point arithmetic here is suitable for illustrative return sensitivity, not cash settlement/accounting. Sourced observations use `Decimal` in the evidence layer.
- Scenario output depends on analyst assumptions, as-of source quality and reproducible provenance, not any intrinsic predictive power of this calculation library.

## Synthetic illustration
```python
from investiq_core.valuation import ValuationScenario, evaluate_scenarios

result = evaluate_scenarios(
    start_eps=5, initial_price=75, years=3,
    scenarios=[
        ValuationScenario("bear", 0.00, 10, 0.25),
        ValuationScenario("base", 0.10, 15, 0.50),
        ValuationScenario("bull", 0.20, 20, 0.25),
    ]
)
print(round(result.expected_terminal_price, 4))  # 105.6125
```

The instruments, earnings assumptions, scenario weights and outcomes in this illustration are fictional.
