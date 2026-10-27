# InvestIQ Architecture — Connected Research, Reproducible Decisions

> **Current implementation:** v0.1.1 portable Python core and synthetic offline CLI.
>
> **Approved target direction (not yet built):** provider-agnostic connected investment data, freshness-aware access and optional caching; explicit, immutable research snapshots stored locally **or** in a properly governed cloud service. See [Product Roadmap v2.0](../product/product-roadmap.md) and [ADR 0003](../decisions/0003-connected-data-and-research-history.md).

Engineering practices for these boundaries are defined by the [Engineering Blueprint](../engineering/engineering-blueprint.md). It is a policy for future work, not evidence that conditional tooling or services already exist.

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

### v0.2 PR 1 domain contracts (implemented; adapters still planned)

`market.py` defines issuer-to-listing lineage, sourced quotes, quote timeliness, reuse rights and caller-policy freshness. `fundamentals.py` contains filing references and a narrow financial metric catalog. `ports.py` declares optional-provider capabilities, requests and categorized failures using async Protocol interfaces. None of these modules makes network requests or grants market-data entitlements. See [ADR 0004](../decisions/0004-provider-neutral-data-contracts.md) and [connected data contracts](../methodology/connected-data-contracts.md).

### v0.2 PR 2 adapters (implemented, opt-in)

`adapters/sec_edgar.py` lists recent SEC submissions by explicit CIK; `adapters/twelve_data.py` fetches a BYOK, venue-verified minute-candle CLOSE price with **UNKNOWN** plan timeliness and default-denied reuse. `adapters/_http.py` provides bounded, no-redirect HTTPS JSON transport and synthetic-test injection. No provider calls occur at import. **No cache, account management, financial-statement mapper, saved research workflow, or public hosted service has been added.** See [ADR 0005](../decisions/0005-provider-selection.md) and [provider setup/limitations](../methodology/provider-adapters.md).

### v0.2 PR 3 connected source orchestration (implemented)

`application/connected_data.py` provides on-demand quote and filing use cases, source-age validation, bounded retry policy and rights-aware in-process quote caching. The cache is **disabled for provider responses without explicit caching rights**, including the currently integrated Twelve Data adapter. `QuoteCachePort` is a future shared cache contract, not a hosted implementation. No XBRL financial-data normalization, company valuation workflow, historical thesis store or frontend has been added. See [ADR 0006](../decisions/0006-connected-data-service.md) and [usage](../methodology/connected-data-service.md).

### v0.2 PR 4 connected issuer analysis (implemented; constrained)

`adapters/sec_companyfacts.py` fetches and conservatively filters SEC annual 10-K US-GAAP facts. `fundamentals.AnnualMetricFact` and the corresponding `FundamentalsProvider` port preserve accession, filing date, fiscal period, value units and exact `Decimal`. `application/connected_research.py` combines compatible issuer/listing mapping, reported annual EPS and price observations, with explicit freshness/FX/share-basis eligibility. No quote/data persistence, automatic rankings, forward/TTM valuations, complete fiscal normalization or new CLI/web interface is implied. See [ADR 0007](../decisions/0007-connected-research-analysis.md) and [connected research use](../methodology/connected-research.md).

### v0.2 PR 5 research snapshots (implemented)

`research_snapshot.py` provides an explicit user-initiated capture from connected analysis, a versioned immutable input manifest and offline valuation replay. It retains SEC annual facts and **only quotes with explicit snapshot rights**, so current Twelve Data prices remain excluded from persisted outputs. `snapshot_store.py` adds private create-only local files, revision lineage checks, corruption detection and JSON/Markdown exporters. It reuses the existing `ThesisSnapshot` chain; no cloud, hosted auth or automatic market data persistence is implied. See [ADR 0008](../decisions/0008-private-research-snapshots.md) and [usage](../methodology/research-snapshots.md).

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
