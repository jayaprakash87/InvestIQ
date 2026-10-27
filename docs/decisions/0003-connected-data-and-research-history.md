# ADR 0003 — Connected market data, optional cache, immutable research decisions

**Status:** Accepted as roadmap-level architecture decision (2026-10-27).  
**Scope:** Target InvestIQ v0.2+ architecture. **Not an implemented system design for v0.1.1.**

## Context

InvestIQ v0.1.1 demonstrates analysis from fictional offline evidence. The initial v0.2 roadmap proposed a **local-only company workspace**. This is inadequate as the primary information layer: equity quotes, intraday volumes, estimates, corporate actions, disclosures and prices change on different schedules. Research also needs an unchanged historical record for accountability and replay.

A static local cache can be stale; conversely, a research snapshot should **not** mutate whenever a market quote updates.

## Decision

1. **Two information modes:** provider-backed `CurrentResearchView` for appropriately current data; explicitly saved `ResearchSnapshot` for versioned decisions and reproducibility.
2. **Provider-neutral interfaces:** adapters for quote/history, filings/fundamentals, estimates, FX and news with capability, identity, provenance and rights metadata. Do not hard-code any one paid provider.
3. **Truthful timeliness:** records preserve exchange event time, retrieval time, session, entitlement/delay status, currency, venue and whether data are real-time/delayed/EOD/historical/unknown. No invented freshness and no silent delayed-price fallback.
4. **Cache as optimization:** bounded in-process cache first, optional shared managed cache when scale and licensing justify it. Cache keys and reuse must respect user/source entitlements, quote kind, adjustment, session and provider.
5. **Portable open-source deployments:** support direct API/BYOK and private research snapshots without a cloud account. Self-hosted/managed services are optional future adapters, gated by source redistribution licenses, security and economic justification.
6. **Snapshot by explicit action:** live refresh changes calculated views but does not create an investment-thesis revision. Saving records lawful exact input manifests, assumptions, method versions, event/source times and linked thesis history.
7. **No automatic data replication license:** source retention, caching, serving users and replay must follow actual provider/exchange permissions. Where full offline replay is prohibited, record and disclose the limitation rather than copying restricted data.

## Alternatives considered

- **Local-only market database:** rejected as the main feed because values become stale; local storage remains valid for private historical decisions and offline imports.
- **Direct API with no abstraction:** possible small prototype but rejected as final design due to provider lock-in, incomplete data quality controls and inability to enforce consistent freshness.
- **Provider-agnostic APIs plus selective cache (chosen):** on-demand current information without prematurely building cloud infrastructure.
- **Immediate full cloud warehouse/streaming system:** deferred until quant/historical volume, update requirements, economics and data rights demonstrably require it.
- **Mandatory hosted commercial market feed:** rejected for initial public OSS distribution because a provider key/paid exchange right cannot be assumed for every user.

## Consequences

Positive: current research and saved decisions are correctly distinguished; a user can run the library locally while an operator may deploy licensed shared infrastructure later. Requirements for source transparency and historical replay become verifiable tests.

Costs: provider adapters, rate-limit/fallback handling, entitlement/caching rules, explicit issuer mapping, dynamic market sessions and lawful snapshot retention add complexity. Real-time availability can vary by exchange, geography and contract.

## Product/engineering follow-through

See [roadmap v2.0](../product/product-roadmap.md). The first implementation PR must define source/provider capability, quote session/timestamp/delay classification, issuer/instrument mapping, `CurrentResearchView` and `ResearchSnapshot` contracts. Do **not** first introduce a mandatory SQLite company-master repository, a hosted UI or high-throughput event streaming.
