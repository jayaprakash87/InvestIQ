---
name: business-analysis
description: Analyze the business model, economic drivers, competitive durability and risks of a publicly traded company.
---

# Business analysis

## Inputs
Instrument identifier (ticker, venue, currency), research question, analysis `as_of` timestamp, dated evidence, and clearly separated assumptions. Do not assume access to real-time quotes, private portfolios, or a market-data provider.

## Procedure
1. Identify products/services, who pays, revenue mechanisms, customer and supplier concentration, and economic dependencies. Mark unknowns explicitly.
2. Explain value-chain position and what creates customer value (switching costs, regulation, IP, distribution, capacity or network effects). Differentiate evidence from narrative.
3. Examine unit economics, capital intensity, competitive durability and industry-specific operating metrics only where suitable.
4. Identify disconfirming evidence and structural risks; do not conflate an excellent business with an attractive price.
5. Cite source observation IDs for numerical claims. Where material qualitative source documents are unavailable, label conclusions as tentative inferences or gaps—not sourced facts.

## Output
Emit the shared `ResearchReport` contract with `skill="business-analysis"`, subject, `as_of`, and findings classified as `reported_fact`, `external_estimate`, `assumption`, `inference`, or `data_gap`. Provide open questions and counterarguments.

## Safeguards
Never invent TAM, market share, management claims or competitive advantages. No buy/sell advice, personal allocations or unverified promises of return. Use `data_gap` for missing source material. Structural validator cannot certify qualitative evidence.
