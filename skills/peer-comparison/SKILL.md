---
name: peer-comparison
description: Compare two or more public securities using comparable operating economics, evidence and valuation assumptions.
---

# Peer comparison

## Inputs
At least two venue-qualified instruments, shared cutoff `as_of`, explicit comparison question and source-backed observations per company.

## Procedure
1. Check whether each company occupies the same economic value-chain layer. Label direct competitors, substitutes, suppliers, or unrelated thematic exposures.
2. Normalize fiscal periods, units, currencies, revenue recognition, accounting adjustments and segment coverage *before* comparing metrics.
3. Compare growth trajectory, margins/returns, capital intensity, durability, valuation, size and relevant sector operating metrics.
4. Report risks of misleading comparisons and identify missing data separately for each instrument.
5. Draw only supported relative conclusions; rankings must state their objectives and assumptions, never imply that 'best company' equals 'best entry price'.

## Output
Use `ResearchReport` with `skill="peer-comparison"` and all compared subjects. Cite exact observation IDs. If comparable evidence is unavailable, return a `data_gap` rather than a numerical league table.

## Safeguards
Never blend incomparable valuation ratios as if interchangeable. No fabricated industry averages or peer growth estimates. No portfolio-specific ranking or real-money allocation.
