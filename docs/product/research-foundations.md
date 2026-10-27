# InvestIQ — Research Foundations and Product Requirement Traceability

> **Status:** Product discovery evidence and requirement traceability · **Date:** 2026-10-27
> **Scope:** Representative research workflows previously explored by the project owner. This is a **public product-method reference**, not a portfolio record, verified stock recommendation, current security ranking, or uploaded dataset.
> **Links:** [Product Roadmap](product-roadmap.md) · [v0.3 Personal Research Desk PRD](ai-research-experience.md) · [Research validation](validation-plan.md).

## Why InvestIQ exists

The motivating problem is **repeatable, independent investment underwriting**, not a chatbot that writes stock summaries. Manual research has repeatedly required assembling company fundamentals and market data, understanding business economics and value-chain relationships, challenging assumptions, ranking firms within relevant sectors, calculating returns under different entry prices, and revisiting conclusions as new data arrive.

Spreadsheets and general-purpose LLM conversations helped explore that method, but require manual refreshing, repeated prompts, inconsistent assumption transfer and frequent checks of whether data are current, peer comparisons valid, or rankings defensible. InvestIQ should make that repeatable workflow accessible **first to its creator**, then to any open-source adopter.

## Actual research families explored

| Prior research family | Observed research questions and artifacts | Product requirement | Earliest full roadmap milestone |
| --- | --- | --- | --- |
| **AI infrastructure value chain** | AI equipment, foundries, packaging, optics, networking, power and thermal, cloud; a 194-listed-name / 23-segment research map with variable verification coverage | Sector/value-chain taxonomy, valid entity and segment relationships, ranked/unranked separation and transparent gaps | v0.5 |
| **AI / physical AI screening** | 150-company AI universe and physical-AI scorecards with qualitative and quantitative dimensions | Extensible screened research universe, confidence/coverage, transparent factor weighting, no fabricated financial inputs | v0.5 |
| **Company economics and relative positioning** | Broadcom vs semiconductor peers; Coherent vs Fabrinet vs Amkor vs Vertiv; optical suppliers vs assembly/test vs power/thermal businesses | Business-model decomposition, true peers vs complementary value-chain exposure, competitive advantage, concentration, margins and cyclicality | v0.4 |
| **Valuation and scenario underwriting** | Forward vs trailing multiples; FCF yield, cash conversion, EPS CAGR, exit multiple, sensitivity, required entry price for hypothetical return hurdles | Valuation with correct dated market/fiscal bases, separate bear/base/bull assumptions and conditional annualized outcomes; exact provenance | v0.6 |
| **Rankings that changed with market conditions** | Multi-factor quality, AI exposure, growth, moat, valuation, financial risk, size optionality, rerating and short-term vs multi-year perspectives | Configurable explainable scorecards, changes attributable to price vs fundamentals vs method/weight changes; rank confidence | v0.5–v0.7 |
| **Short-term catalysts vs compounding thesis** | Queries about 3–6-month upside versus multi-year return, and why prices fell while thesis seemed intact | Separate horizons, catalyst/event vs quality/valuation signals, explicit uncertainty and no unsupported multibagger probability | v0.5–v0.7 |
| **Energy / industrial infrastructure** | Schneider, Vertiv, Siemens Energy, GE Vernova, ABB; alternative subsector names, cyclical recovery and capital intensity | Multiple research universes, industry-specific factors and fair comparisons for industrials, power, data centers and utilities | v0.4–v0.6 |
| **Quality industrial and business-services companies** | Rollins, Cintas, Ecolab, Fastenal, Sherwin-Williams, Copart; trend-aware business quality screens | Cross-sector industry templates, durable ROIC/margins/FCF and valuation/reinvestment tradeoffs | v0.5–v0.6 |
| **Portfolio construction and decision process** | Theme concentration, differing stock roles, risk budget and whether to deploy capital now versus wait for entry thresholds | Opt-in holdings, watchlist vs actual positions vs hypothetical allocations, overlapping exposures, rules and scenarios | v0.8 |
| **Research continuity and trust** | User challenged rankings, asked for full-sheet recreation rather than incremental patching, requested updated price basis, trend and FCF adjustments | Saved versioned methodology, refresh-at-use, immutable prior decisions, change explanations, audit of the *entire* computation and contradictions | v0.3–v0.7 |

**Historical-workbook examples (source references, not data for redistribution):**
- `AI_Infrastructure_Stock_Ranking_2026.xlsx` — growth, valuation, exposure, moat, risk and rerating weights.
- `AI_Infrastructure_Investment_Portfolio_2026_REVISED.xlsx` and `AI_Infrastructure_Investment_Decision_Book_2026_v2.xlsx` — IRR sensitivity, entry conditions and hypothetical allocation workflows.
- `AI_Value_Chain_Master_Investment_Ranking_2026-10-14(1).xlsx` — 194 companies, 23 AI value-chain layers, uneven price/valuation coverage and explicit ranking limitations.
- `AI_Investment_Research_Phase_2_Complete.xlsx` — qualitative AI theme/quality/valuation/risk screening across 150 names.
- Physical AI research workbook versions — company categories, economic moat and physical-AI exposure scoring.

These workbooks were exploratory and contain as-of values, subjective ratings and in some cases incomplete/uneven data. **Do not ingest or redistribute them as current facts, claim prospective accuracy, or silently transfer investor-specific allocation decisions into public defaults.** A future lawful import tool may let a user bring their own historical work in privately.

## The investment research framework we should preserve

1. **Discover and define universe:** Theme, industry, suppliers, customers, competitors, substitutes, listed instruments, exchange/currency; differentiating *direct exposure* from narrative association.
2. **Understand economic engine:** products, revenue mix, drivers, unit economics, profit pool/value capture, competitive moat, concentration, investment cycle and displacement risks.
3. **Underwrite financial quality and trend:** historical revenue, growth, gross/operating margin, FCF conversion, ROIC, leverage, capex, dilution, customer/industry cycle; use reporting-basis comparable periods.
4. **Value against *current verified* price:** appropriate EV/earnings/FCF/DCF-style methods as available, reverse underwriting, time-horizon-specific return scenarios, uncertainty, multiple compression and cost/FX caveats.
5. **Score transparently:** separate thematic attractiveness, business quality, valuation, financial resilience, catalyst/momentum/short-term signals, forecast confidence and coverage. Weights and definitions must be exposed, versioned and user-configurable. Never manufacture a complete score when evidence is insufficient.
6. **Rank fairly:** compare true business peers with like-for-like metrics; complementary firms belong in a *value-chain map*, not necessarily the same valuation league table. Clearly separate "research priority", "quality", "valuation appeal" and "conditional return potential".
7. **Challenge and decide:** strongest bear case, falsification checkpoints, what price/condition could change the stance, uncertainty and data gaps; user owns the decision.
8. **Track and re-underwrite:** distinguish price-driven, earnings-driven, assumptions-driven, weighting-driven and source-revision-driven changes; never silently rewrite the initial decision.

## Essential example journeys and acceptance

### A. Company deep dive — first personal use (v0.3/v0.4)
"Analyze Broadcom using dated, supported financial evidence, explain moat and concentration risk, calculate only eligible valuation ratios, and state strongest reasons the attractive AI narrative might fail." No manually supplying a CIK or writing specialized prompts for supported issuers.

### B. Economic comparison (v0.4)
"Compare Coherent, Fabrinet, Amkor and Vertiv: explain **why they are not direct peers**, which AI infrastructure layers they serve, who captures margins, and present only relevant comparable financial fields." Do not pretend a single P/E-based score makes them economically comparable.

### C. Market-aware rank (v0.5)
"Rank supported optical/interconnect companies for research under explicit assumptions. Show the evidence, missing coverage, risk, score version and which ranks would change under alternate weights." A firm lacking supported quotes/valuation cannot be given a confident current-price rank.

### D. Price-to-opportunity question (v0.6)
"What entry price is compatible with a **hypothetical** 15% annualized three-year return under my EPS and terminal multiple assumptions?" Make the assumptions and arithmetic visible; do not convert scenario math into a guaranteed buy call.

### E. Return to a thesis (v0.7)
"Since my last approved research note, what changed in price, financial results, estimates (if available) and my assumptions?" If source retention prevents exact replay, show the gap and do not backfill with today's quote.

### F. Portfolio context (v0.8)
"Do my selected AI and energy exposure buckets overlap economically? How does a hypothetical additional position change concentration and risk?" Private positions never become public fixtures.

### G. New investor installs open-source InvestIQ (v0.9/v1.0)
Install the packaged app, explore a **clearly synthetic** sample with no accounts/keys, configure an authorized data/LLM provider through a setup wizard if desired, ask a supported question, inspect citations, save lawful decisions privately, update/export them and understand unsupported market coverage **without learning Python**.

## Product-design constraints learned from earlier iterations

- **Every "current" analysis needs an as-of and source-quality status.** Prior snapshots often mixed asynchronously fetched prices, missing markets and subjective growth forecasts.
- **No single magic composite score.** Horizon, industry, confidence and weights matter; old workbook rankings were challenged precisely because economic bases and data changed.
- **Do not use P/E alone:** track FCF, ROIC, margins, debt, capex, quality of earnings, growth, competitive moat, concentration, management execution and sector cycle.
- **Current market feed and saved thesis are separate.** Local/cloud history is user data; provider API remains the permitted current quote source.
- **Work should be automated, but the decision belongs to the user.** AI gathers and interprets; deterministic domain code computes; visible evidence and user-approved thresholds constrain conclusions.
- **Open-source and user-controlled from day one.** No required central backend or opaque proprietary data store; legitimate external market/LLM services may require user's credentials, charges and permissions; provide honest onboarding and synthetic demo.
- **Usefulness before breadth.** Prefer a reliable focused set of supported companies/markets and complete end-to-end research over dozens of half-functional templates and provider adapters.

## Working definition of v1.0

InvestIQ 1.0 is a **stable, documented, user-installable, source-connected (when configured), AI-assisted equity research workspace** with complete company research, appropriate comparisons, explainable screening, scenario/entry sensitivity, opt-in watchlists/history/change review and an optional portfolio context. Nontechnical use must not require CLI after installation. It is usable locally with genuine on-demand provider refresh when entitled; user research stays private by default. Other investors can install and run the same tested workflow with **their own** coverage, watchlists, scoring configuration and providers.

v1.0 is **not** all exchanges, every asset class, guaranteed predictive scoring, licensed global realtime redistribution, automated trading, managed money or a compulsory hosted cloud service.
