---
name: financial-analysis
description: Interpret reported income, cash flow and balance-sheet trends with explicit fiscal periods, units and provenance.
---

# Financial analysis

## Inputs
Venue-qualified instrument, analysis `as_of`, financial observations with fiscal-period coverage, publication dates and exact units, plus any scenario assumptions.

## Procedure
1. Group comparable reported financial periods; distinguish quarterly, TTM and fiscal-year values. Do not silently annualize quarters.
2. Assess sales growth, operating margins, cash conversion, leverage and reinvestment using metrics appropriate to the business.
3. Explicitly separate published facts, third-party estimates and derived or hypothetical calculations.
4. For ratios, ensure matched currency, accounting basis, fiscal period and correct denominators. Use tested `investiq_core` calculations when implemented; never trust free-form LLM arithmetic.
5. Detect missing filings, restatements, one-offs, dilution and peak/trough cyclicality. Describe uncertainties and metrics that cannot be compared.

## Output
Use `ResearchReport` with `skill="financial-analysis"`. Cite the precise observation IDs for each quantitative finding. Record absent earnings/cash data as `data_gap`; include limitations and follow-up questions.

## Safeguards
Do not infer factual numbers from memory. No invented growth rates or margins. Do not use financial observations that were not available at `as_of`. Never present EBITDA or forward EPS as reported GAAP earnings without verification.
