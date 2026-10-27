# InvestIQ Architecture — AI-First Research on a Trusted Financial Core

> **Current implementation:** v0.2.0 source release candidate: portable Python core, opt-in BYOK connected CLI, constrained annual facts, deliberate rights-aware snapshots and offline replay. **No shipped LLM agent or consumer UI.**
>
> **Proposed v0.3 direction (not built):** an accessible AI-first, source-grounded investment research journey with bounded model tools, reliable deterministic math, critical thesis challenge and explicit private-history control. Existing provider rights/freshness/snapshot contracts remain mandatory. See [Roadmap v3.0](../product/product-roadmap.md), [v0.3 PRD](../product/ai-research-experience.md), [ADR 0009](../decisions/0009-ai-first-product-pivot.md) and historical [ADR 0003](../decisions/0003-connected-data-and-research-history.md).

Engineering practices for these boundaries are defined by the [Engineering Blueprint](../engineering/engineering-blueprint.md). It is a policy for future work, not evidence that conditional tooling or services already exist.

## 1. Implementation history and actual v0.2 baseline

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

**Historical note:** The preceding v0.1.1 tree is preserved for release history. The cumulative v0.2 source described below **does** add opt-in provider adapters, connected analysis and rights-aware private snapshots. None of that establishes live-provider entitlement, a public hosted feed or an AI consumer research application. Each PR subsection describes the state **at that PR**, not the complete final v0.2 state.

### v0.2 PR 1 domain contracts (implemented; historical stage)

`market.py` defines issuer-to-listing lineage, sourced quotes, quote timeliness, reuse rights and caller-policy freshness. `fundamentals.py` contains filing references and a narrow financial metric catalog. `ports.py` declares optional-provider capabilities, requests and categorized failures using async Protocol interfaces. None of these modules makes network requests or grants market-data entitlements. See [ADR 0004](../decisions/0004-provider-neutral-data-contracts.md) and [connected data contracts](../methodology/connected-data-contracts.md).

### v0.2 PR 2 adapters (implemented, opt-in)

`adapters/sec_edgar.py` lists recent SEC submissions by explicit CIK; `adapters/twelve_data.py` fetches a BYOK, venue-verified minute-candle CLOSE price with **UNKNOWN** plan timeliness and default-denied reuse. `adapters/_http.py` provides bounded, no-redirect HTTPS JSON transport and synthetic-test injection. No provider calls occur at import. **At PR 2,** cache, Companyfacts normalization and snapshots were not yet integrated; the subsequent PRs added those constrained capabilities. A public hosted service and account management are still absent. See [ADR 0005](../decisions/0005-provider-selection.md) and [provider setup/limitations](../methodology/provider-adapters.md).

### v0.2 PR 3 connected source orchestration (implemented)

`application/connected_data.py` provides on-demand quote and filing use cases, source-age validation, bounded retry policy and rights-aware in-process quote caching. The cache is **disabled for provider responses without explicit caching rights**, including the currently integrated Twelve Data adapter. `QuoteCachePort` is a future shared cache contract, not a hosted implementation. **At PR 3,** Companyfacts mapping, valuation and snapshot storage were not yet added; PRs 4–6 subsequently implemented the limited connected analysis and snapshot workflows described below. No frontend was added. See [ADR 0006](../decisions/0006-connected-data-service.md) and [usage](../methodology/connected-data-service.md).

### v0.2 PR 4 connected issuer analysis (implemented; constrained)

`adapters/sec_companyfacts.py` fetches and conservatively filters SEC annual 10-K US-GAAP facts. `fundamentals.AnnualMetricFact` and the corresponding `FundamentalsProvider` port preserve accession, filing date, fiscal period, value units and exact `Decimal`. `application/connected_research.py` combines compatible issuer/listing mapping, reported annual EPS and price observations, with explicit freshness/FX/share-basis eligibility. No quote/data persistence, automatic rankings, forward/TTM valuations, complete fiscal normalization or new CLI/web interface is implied. See [ADR 0007](../decisions/0007-connected-research-analysis.md) and [connected research use](../methodology/connected-research.md).

### v0.2 PR 5 research snapshots (implemented)

`research_snapshot.py` provides an explicit user-initiated capture from connected analysis, a versioned immutable input manifest and offline valuation replay. It retains SEC annual facts and **only quotes with explicit snapshot rights**, so current Twelve Data prices remain excluded from persisted outputs. `snapshot_store.py` adds private create-only local files, revision lineage checks, corruption detection and JSON/Markdown exporters. It reuses the existing `ThesisSnapshot` chain; no cloud, hosted auth or automatic market data persistence is implied. See [ADR 0008](../decisions/0008-private-research-snapshots.md) and [usage](../methodology/research-snapshots.md).

### v0.2 PR 6 connected CLI and acceptance

`connected_cli.py` and the legacy-compatible `cli.py` provide an explicit, user-supplied listing/CIK research command and a network-free saved-decision replay command. Importing CLI code and running the synthetic demo never starts network calls. `tests/test_release_acceptance.py` exercises actual SEC/quote adapters with injected synthetic HTTP and the full CLI save/replay sequence. Real provider entitlements are **not** validated by fake HTTP. See [connected CLI guide](../methodology/connected-cli.md) and [release acceptance](../engineering/release-acceptance-v0.2.md).

## 2. Target AI-first logical architecture (v0.3 — not deployed)

**Top-down investor journey:** Natural-language investment question or supported company search → qualified issuer/security selection → bounded AI research orchestration → entitled dated evidence and deterministic calculations → integrated answer with source drill-down, strongest counterargument and data gaps → explicit user-controlled decision save.

**Execution and trust boundaries:**

1. **UI or assistant-native integration (planned):** simple question entry, responsive answer and scenario controls, source timing, uncertainty, consent and research-save actions. No mandatory CIK/API key/CLI for a supported nontechnical consumer flow.
2. **ResearchTask / bounded coordinator (planned):** choose narrow allowlisted tools, operate within step/time/token/API budgets, return typed success/partial/error outputs, and never treat external text as commands.
3. **Existing financial core (v0.2):** issuer identity, permitted data adapters, source freshness/entitlements, qualified fundamentals, deterministic valuation and research-report/thesis contracts. Domain logic never calls the LLM.
4. **Claims and thesis challenge (planned):** checked source IDs, time/currency semantics, semantic evidence faithfulness and specific falsifiable bear-case reasoning; a cited ID alone is not enough.
5. **Research continuity:** existing **explicit, immutable, rights-aware** historical snapshots remain separate from transient current quotations. v0.4 may introduce opt-in investor context and material-change monitoring only after v0.3 validation.

**Runtime distribution not decided:** Test a thin standalone task UI against an assistant/skill/MCP integration using the same core tools. Cloud identity, shared licensed cache, relational storage and encryption controls are required if hosted user data make them necessary; no assumed free global real-time feed. Avoid queues, microservices, complex agents and vector infrastructure without demonstrated use.

### Planned boundary contracts

| Boundary | Purpose | Must not do |
| --- | --- | --- |
| ResearchTask and UI | Typed question, supported instrument resolution, as-of scope, user approvals and evidence/status rendering | Require developers' setup or hide ambiguous securities |
| AI orchestration tools | Allowlisted identity, sourced retrieval, deterministic analysis, scenario follow-ups, challenge and deliberate save | Make up quotes, perform authoritative free-form calculations, execute trades or bypass consent |
| Semantic evidence check | Material source-to-claim support, numerical/time/issuer fidelity, missing and conflicting sources | Claim semantic certainty from citation ID validation |
| Financial domain core | Stable, versioned evidence/calculations and licensed-source controls | Depend on model SDKs, browsers or provider network logic |
| Optional investor context (v0.4) | Private approved watchlists/preferences, saved thesis-delta evidence and deletion/export | Continuously collect private holdings or rewrite prior theses |

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
| `interface/*` | Existing CLI/export; **planned v0.3 AI/task UI or assistant integration** | Duplicating financial calculations or hiding provider/model uncertainty |

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

**The v0.2 source/price contract exists. v0.3 architecture now starts at a validated, safe, accessible investor task and bounded research-tool boundary — not another platform-first backend expansion.**
