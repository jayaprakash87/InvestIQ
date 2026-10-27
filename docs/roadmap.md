# InvestIQ Roadmap

**Canonical and finalized planning baseline:** [InvestIQ Product Strategy and Roadmap v2.0](product/product-roadmap.md) (2026-10-27).

**Architecture decision:** connected, provider-agnostic market/fundamental data; provider- and entitlement-aware freshness/cache; **optional** cloud deployment; **user-controlled immutable research snapshots**. Local storage is an allowed choice for *historical research*, never the sole source of current prices.

| Release | Direction |
| --- | --- |
| **v0.1.1 (released)** | Offline research library, five skills, provenance, valuation and synthetic example |
| **v0.2.0 (release candidate)** | BYOK quote / SEC annual facts, conservative connected analysis, explicit local rights-aware snapshots, CLI and synthetic acceptance; live provider smoke still requires credentials |
| **v0.3** | Comparisons, trends and industry-aware valuation |
| **v0.4** | Data-change intelligence, human-approved thesis updates and opt-in monitoring |
| **v0.5** | Optional local/hosted interface, gated by users, data licenses and cost |
| **v0.6+** | Point-in-time quant research only after bias/cost/data-quality gates |
| **v1.0** | Stable extensible open research platform |

Completed v0.2 implementation workstreams: (1) market-data contracts/ADR; (2) entitled provider adapters; (3) on-demand access/freshness/cache; (4) connected analysis; (5) durable snapshots and source-linked output; (6) integrated acceptance/release.

No web SaaS, live feed entitlement, trading or investment-fund capabilities are promised by this roadmap. **See the [full document](product/product-roadmap.md)** for requirements, non-goals, rollout gates, cost/security controls and provider evaluation.
