# InvestIQ Architecture — Connected Research, Reproducible Decisions

> **Current implementation:** v0.1.1 portable Python core and synthetic offline CLI.
>
> **Approved target direction (not yet built):** provider-agnostic connected investment data, freshness-aware access and optional caching; explicit, immutable research snapshots stored locally **or** in a properly governed cloud service. See [Product Roadmap v2.0](../product/product-roadmap.md) and [ADR 0003](../decisions/0003-connected-data-and-research-history.md).

## 1. Current implemented modules (v0.1.1)

```text
src/investiq_core/
  evidence.py    Numeric observations, source attribution, assumptions and dates
  valuation.py   Pure valuation and return calculations
  research.py    Structural research report/provenance validation
  thesis.py      Hash-linked versioned research theses and JSONL serialization
  workflow.py    Synthetic demonstration with integrated validation
  cli.py         Offline, vendor-independent entry point
  __main__.py    python -m investiq_core
skills/
  */SKILL.md     Five portable research instructions
tests/           Public synthetic and negative-case automated tests
```

There is **no live/delayed price provider, cloud cache, cloud database, web UI or live-data ingestion capability in v0.1.1**. Do not interpret this target description as deployed functionality.

## 2. Target logical components

```text
 CLI | optional Web / API | portable AI research skills
                        |
                Research application
                   /          \
                  v            v
        Current research     Saved decision/replay
              view                 |
                  |                 v
         Data access facade     Snapshot repository
          + normalization     (local or cloud adapter)
                  |                 |
          Source freshness       Immutable versions
          and entitlement        source/input manifests
                  |
    Provider quote/fundamental/news adapters
                  |
    Optional bounded in-process / shared cache
                  |
           Entitled market providers
```

**Source of current data:** provider API/stream and its entitlement, never a private copy presumed current. **Source of historical decision:** saved, versioned research evidence and assumptions, never a silently refreshed quote.

## 3. Module boundaries

| Boundary | Responsibility | Not responsible for |
| --- | --- | --- |
| `domain/evidence` | instrument/issuer identity, units, timestamps, provenance and vintages | Vendor HTTP, broker sessions |
| `domain/market` (planned) | normalized quote, session, delay/freshness and entitlement semantics | Claiming all prices are live |
| `providers/*` (planned) | provider API auth, capabilities, normalization, rate limits and failures | Investment scoring |
| `data_access` (planned) | request orchestration, provider selection, safe fallback, optional cache | Hiding source/delay changes |
| `research/valuation` | deterministic calculations on qualified inputs | Fetching live quotes during math |
| `research/snapshot` (planned) | deliberate save/replay, immutable research decisions and version manifests | Capturing every tick |
| `storage/*` (planned) | adapter for user-controlled durable snapshots | Becoming an exchange-data redistribution backend |
| `interface/*` | CLI, export and optional later web/AI integration | Duplicating financial domain logic |

### Distinct record types

**NormalizedQuote** (planned): venue-qualified instrument, quote kind/value/currency, source event timestamp, provider retrieval/ingestion timestamp, session, original provider, as-of/delay classification, adjustment basis and license/entitlement context. The response exposes whether fresh, stale, closed-session, delayed, EOD, historical or unknown **when justified**.

**CurrentResearchView** (planned): transient view with input IDs, freshness flags and deterministic calculations. It can change when provider information changes.

**ResearchSnapshot** (planned): immutable saved input manifest and analyst hypotheses plus calculation version, source vintages and hash-linked thesis reference. Created by explicit save, not by view/price refresh.

**RecordedSource**: filing/consensus observation with economic period, exact public availability or uncertainty qualifier, retrieval time and rights/provenance.

## 4. Data access, freshness and source semantics

- Cache TTL and admissible freshness depend on category, provider plan, entitlement, trading session and market. Do not globally assume a seconds-level quote TTL or quarter-level fundamentals TTL.
- All data-returning services must supply source, event time, retrieval time, provider entitlement/delay, currency, market and freshness/staleness status as supported.
- Delayed/EOD data are **not** real-time data. Closed-market last prices must be visibly dated. Unknown timestamps cannot be converted into invented “now” values.
- Provider fallbacks must not silently mix adjusted/unadjusted prices, delay classes, share classes, currencies, fiscal definitions or source licenses.
- Cache key isolation must include provider, symbol/venue, data shape, quote kind, market session, adjustment, currency and entitlement scope. A premium cached response must not be shared with an unauthorized user.
- Use bounded refresh, rate-limit/backoff, timeout, provenance and fail-closed behavior. A shared cache or streaming system is justified only by usage measurements and licenses.

## 5. Deployment and persistence

**First vertical slice:** direct provider calls from an optional client/adapter with BYOK and bounded in-process caching. No mandatory cloud. The portable core still works offline on synthetic/user-supplied evidence.

**Conditional cloud service:** self-hosted or managed data-access gateway, centrally controlled secrets, provider licensing, cache, tenant/entitlement partitioning, monitoring and cost controls. No commitment to hosted real-time market distribution before exchange rights are established.

**Durable research:** pluggable, separately secured storage (local for an individual's private snapshots, managed cloud for permitted team/hosted usage). Local persistence for saved *research history* is valid and portable; local-only static copies should **never** be treated as the primary continuously current market feed.

**Replay boundary:** capture lawful input values or durable permitted reference; preserve original quote times, assumptions, source and model versions. If an input cannot legally be retained/replayed, state the limitation instead of claiming perfect reproducibility.

## 6. Security, legal and quality gates

- Provider secrets must not appear in URLs logged publicly, checked-in fixtures, PRs or source files.
- SEC filings and all external text are untrusted content, never instructions to execute.
- Provider data use, caching, display and downstream redistribution need explicit rights. The MIT software license is not an exchange-data license.
- Do not include restricted datasets, user holdings, private research or identifiable personal details in the repository.
- Confirm API quota costs, identity corrections, corporate actions, user session/timezone changes, outages and missing observations with deterministic negative-case tests.
- Preserve architecture-level contract tests and v0.1 synthetic offline regression suite. A docs-only plan does not change the released API behavior.

**Architectural development starts at the source/price contract, not a local database, streaming bus, website or market-scoring model.**
