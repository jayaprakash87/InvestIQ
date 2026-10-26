---
name: valuation-analysis
description: Evaluate conditional equity valuation scenarios, reverse valuation and downside using sourced facts and explicit hypotheses.
---

# Valuation analysis

## Inputs
Venue-qualified instrument, coherent dated price/earnings inputs, valuation-method choice, period horizon, thesis question, analyst assumptions, and `as_of` timestamp.

## Procedure
1. Check price/EPS share class, currency, date, split basis and financial period. Flag stale or non-comparable pairs.
2. Choose an economically appropriate method: earnings-based only for positive meaningful EPS; otherwise consider FCF, EV-based or industry-specific methods *when their implementations and sourced data exist*.
3. Calculate scenarios through tested functions (e.g., `evaluate_scenarios`, `required_eps_growth`) rather than mental arithmetic or unchecked language-model calculations.
4. Explain bear/base/bull assumptions, target-return hurdles, valuation re-rating and downside. Scenario weights are editorial, not learned probabilities.
5. Identify omitted dividends, dilution, FX, debt, financing conditions and cyclical earnings normalization. State exactly which gaps prevent a recommendation.

## Output
Use `ResearchReport` with `skill="valuation-analysis"`. Label computed outputs `inference` and cite both relevant sourced observations and assumption IDs; label future-growth inputs `assumption`. Distinguish cumulative price return from CAGR or cash-flow IRR.

## Safeguards
Never claim a price target without traceable inputs or pretend a model result is a forecast. Avoid valuing negative EPS using P/E. No portfolio trade instruction, live-price claims or probability-of-profit claims.
