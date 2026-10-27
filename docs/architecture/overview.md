# InvestIQ Architecture — AI-First Research on a Trusted Financial Core

> **Current implementation:** v0.2.0 source release candidate: portable Python core, opt-in BYOK connected CLI, constrained annual facts, deliberate rights-aware snapshots and offline replay. **No shipped LLM agent or consumer UI.**
>
> **Proposed v0.3→v1.0 direction (not built):** an **open-source local-first AI investment research workspace** covering source-grounded company analysis, industry/peer economics, explainable scoring, valuation/entry scenarios, historical research review, optional private portfolio context and external installation. Start with a bounded personal AI research desk at v0.3. Existing provider rights/freshness/snapshot contracts remain mandatory. See [Roadmap v3.0](../product/product-roadmap.md), [v0.3 PRD](../product/ai-research-experience.md), [ADR 0009](../decisions/0009-ai-first-product-pivot.md) and historical [ADR 0003](../decisions/0003-connected-data-and-research-history.md).

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

## 2. Target AI-first architecture and stages (not yet deployed)

**First personal path (v0.3):** Start local task UI → synthetic sample or one-time guided entitled market/model connection → supported company search/question → security listing resolution → bounded AI coordinator → sourced/current data + deterministic calculations → integrated answer and bear case → explicit private, lawful thesis save.

**Separation of concerns:**

| Logical component | Status / responsibility | Cannot do |
| --- | --- | --- |
| **User task UI / setup wizard** | **Planned v0.3**: supported company lookup, clear coverage, question bar, source drill-down, scenario controls, user approval | Demand CIK/MIC/JSON or manual multi-prompt workflows for an otherwise supported issuer |
| **Bounded AI coordinator** | **Planned v0.3**: typed ResearchTask, allowlisted tool dispatch, consent, wall-time/steps/tokens limits, cancellation, source-linked interpretation | Invent official figures, perform authoritative arithmetic, bypass rights, execute trades or retain text silently |
| **Existing connected source adapters** | **v0.2**: SEC annual facts, Twelve Data BYOK close and rights/time/issuer semantics; expand **only when needed** for later financial/market coverage | Pretend source timeliness/retention is verified when UNKNOWN |
| **Existing deterministic research core** | **v0.2**: numeric evidence/valuation/history; future company quality, comparable metrics, scoring, entry conditions as typed domain functions | Depend on model SDKs, web frontend, prompt instructions or unrestricted provider APIs |
| **Evidence and claim evaluation** | **Planned v0.3+**: validate material financial source claims semantically, periods, units, price/session state and contradictions; version reports | Treat a correct citation identifier as proof the claim is supported |
| **Private research and user context** | v0.2 explicit lawful immutable snapshot; **v0.7** opt-in watchlist updates; **v0.8** optional private holdings | Use current quotes as past decision data or publish personal holdings |
| **Open-source packaging** | **v0.9–v1.0**: guided OS install, no-key synthetic walkthrough, permitted BYOK, secure export/import, versioned migrations and contributor adapters | Require central paid InvestIQ cloud service |

**Evolution:** v0.4 expands business/financial trend and economically valid peers; v0.5 adds versioned theme universes and factor scoring; v0.6 adds reverse-underwriting/conditional return hurdles; v0.7 adds lawful material-change intelligence; v0.8 adds private portfolio context. These are **separate progressively usable capability slices**, not a speculative full-service cloud platform.

**Deployment default:** local browser/task UI backed by minimal Python application/server code as justified. Assistant/skill/MCP interface is **optional additional distribution**, not an indefinite decision replacing the personal UI. Hosted accounts, licensed shared quote cache, identity/tenant isolation, remote private storage and streaming require separate demonstrated rights/economics/security authorization.

**Current vs past:** on-demand entitled quotes are refreshed provider inputs; immutable decisions record only lawful approved historical inputs. Quote licensing can prevent exact replay and must be reported as a limitation; never refill historical valuations from today's price.

**Technical constraints:** keep domain pure, typed ports at actual I/O boundaries, separate AI prompt/model/tool version from economic-method versions, source-to-claim checks, prompt-injection isolation and deterministic math. No unapproved multi-agent, vector store, microservices or unbounded background polling.

## 3. Actual code modules versus planned additions

| Module / boundary | Current implementation | Future progression / exclusions |
| --- | --- | --- |
| `evidence.py`, `market.py`, `fundamentals.py` | **Implemented v0.1–v0.2**: `InstrumentId`, `IssuerId`, `IssuerListing`, `MarketQuote`, freshness/permission models, observed financial facts and source vintages | More accounting metrics and supported security coverage only through verified input semantics; never label unknown quote timing live |
| `ports.py`, `adapters/*` | **Implemented v0.2**: provider-neutral quote/filing/fundamental ports, SEC/Twelve Data adapters, sanitized bounded HTTP | v0.3 cited issuer narrative/document evidence; v0.4+ quarterly/TTM/FCF/FX/market expansions subject to rights |
| `application/connected_data.py` | **Implemented v0.2**: `ConnectedDataService`, quote/filing on-demand data, freshness, rights-aware optional bounded cache and retries | No unconditional provider fallback, centrally hosted cache or market-feed redistribution |
| `application/connected_research.py` | **Implemented v0.2**: `ConnectedResearchService` for constrained annual issuer analysis and qualified valuation | Add v0.3 AI research task orchestration separately; v0.4 valid peers and trends |
| `valuation.py`, `research.py`, `thesis.py` | **Implemented**: deterministic scenario/return helpers, report structure validation and hash-linked thesis records | Sector-specific research comparisons, versioned scoring (v0.5), expanded underwriting (v0.6); never trust LLM generated numeric authority |
| `research_snapshot.py`, `snapshot_store.py` | **Implemented v0.2**: `ResearchSnapshot`, `LocalSnapshotStore`, explicit lawful capture/immutable offline replay and export | v0.7 source-aware research change analysis, v0.8 private positions; no restricted quote storage |
| `connected_cli.py`, `cli.py` | **Implemented v0.2**: developer CLI, synthetic demo and explicit connected research/replay | Preserve public CLI compatibility after local UI is added |
| **Local UI, AI orchestration, source claim evaluation** | **Not implemented** | **v0.3 planned**: local task UI, guided BYOK/model setup, bounded tool coordinator, semantic evidence tests, scenario interaction |
| **Scoring / monitor / portfolio / OSS packaging** | **Not implemented** | **v0.5/v0.7/v0.8/v0.9–v1.0 respectively**, only after earlier user journeys and source/rights quality gates |

### Research record concepts

- **`MarketQuote` (v0.2 existing):** qualified listing, quote kind/value/currency, market event time, session/adjustment, original provider, observed timeliness, reuse rights; caller-supplied freshness check. Provider claims of real-time are not self-verifying.
- **`CompanyResearchResult` (v0.2 existing):** transient connected company result with attributable quote/annual facts, calculation eligibility and errors. May change when permitted data refresh.
- **`ResearchSnapshot` (v0.2 existing):** immutably captured, explicitly approved, rights-aware research input manifest/assumptions and thesis lineage. A price and its valuation may be omitted due to default-denied quote retention.
- **Planned v0.3 `ResearchTask` / AI research run:** supported question, selected instrument, bounded allowlisted tool trace, explainable answer, source-claim relationship, failed/missing evidence and transient model context by default.
- **Planned v0.5 scoring record:** factor definitions, versioned weights and cutoff, sector/horizon/peer group, source coverage and rank evidence.
- **Planned v0.7/0.8 investor state:** opt-in private watchlist, checkpoint/delta tracking and separately permissioned holdings; not publicly stored in the open-source repository.

## 4. Data access, freshness and source semantics

- Cache TTL and admissible freshness depend on category, provider plan, entitlement, trading session and market. Do not globally assume a seconds-level quote TTL or quarter-level fundamentals TTL.
- All data-returning services must supply source, event time, retrieval time, provider entitlement/delay, currency, market and freshness/staleness status as supported.
- Delayed/EOD data are **not** real-time data. Closed-market last prices must be visibly dated. Unknown timestamps cannot be converted into invented “now” values.
- Provider fallbacks must not silently mix adjusted/unadjusted prices, delay classes, share classes, currencies, fiscal definitions or source licenses.
- Cache key isolation must include provider, symbol/venue, data shape, quote kind, market session, adjustment, currency and entitlement scope. A premium cached response must not be shared with an unauthorized user.
- Use bounded refresh, rate-limit/backoff, timeout, provenance and fail-closed behavior. A shared cache or streaming system is justified only by usage measurements and licenses.

## 5. Local-first open-source deployment and storage

**Existing v0.2:** The offline synthetic example needs no keys; connected CLI uses the user's authorized provider credentials, direct permitted API access and private explicit snapshots.

**v0.3 local Research Desk:**
1. Locally launch an accessible browser interface on supported Windows/Linux target environments. Use a small typed application/API boundary; do not move valuation arithmetic or source-entitlement decisions into the frontend.
2. Offer a clearly marked synthetic no-key demo or **one-time guided configuration** of authorized market-data and AI-model access. Do not imply the open-source MIT license grants exchange data rights or model usage credits. Never place secrets in the frontend bundle, logs, test fixtures or Git.
3. Use provider APIs to refresh current company inputs; provider/plan/market/session license policies control retrieval, caches and display. Save private research only when explicitly requested and legal; show missing replay inputs.
4. Local single-user mode should avoid false SaaS auth scaffolding. Bind local service to loopback only, defend origin/CSRF and secret leakage, and protect OS-local stored research. Hosted external access is a separate audited deployment.
5. Future optional quote caches, schedules, model adapters and portfolio stores require genuine demand, validated provider permissions and isolated/private storage.

**User-owned history and portability:** before external beta, provide versioned local data schemas, export/import, backup/restore, migration and explicit retention/deletion. Secrets are not exported by default. Research notes, user weights, saved scenarios, watchlists and holdings are not part of the public repository.

**v0.9/v1.0:** documented supported OS installation, no-key synthetic example, authorized BYOK wizard, accessible complete research-to-reassessment experience, open-source extension points, reproducible build/release and honest coverage matrix. No InvestIQ cloud backend is mandatory.

**Historical rule:** Old saved valuation cannot claim exact replay when a source forbids retention. Do not silently use a newer quote, adjusted series or revised fiscal value during replay.

## 6. Security, legal and quality gates

- Provider secrets must not appear in URLs logged publicly, checked-in fixtures, PRs or source files.
- SEC filings and all external text are untrusted content, never instructions to execute.
- Provider data use, caching, display and downstream redistribution need explicit rights. The MIT software license is not an exchange-data license.
- Do not include restricted datasets, user holdings, private research or identifiable personal details in the repository.
- Confirm API quota costs, identity corrections, corporate actions, user session/timezone changes, outages and missing observations with deterministic negative-case tests.
- Preserve architecture-level contract tests and v0.1 synthetic offline regression suite. A docs-only plan does not change the released API behavior.

**The v0.2 source/price contract exists. v0.3 architecture now starts at a validated, safe, accessible investor task and bounded research-tool boundary — not another platform-first backend expansion.**

## 7. Stable v1.0 technical definition

The open-source app and deterministic Python core support complete **company research → valid comparison → explainable screening → conditional valuation/entry analysis → approved thesis → documented change review** for a truthful set of supported issuers, with opt-in private portfolio context. Nontechnical daily operation requires no shell/programming once locally installed. External adopters can replace universes, weights, providers, supported model adapters and private state without modifying the core or sending data to InvestIQ servers.

Public API/schema and methodology versions, provider/time/rights controls, model semantic evaluation, installer/browser/accessibility tests, secure storage/migration/export, dependency/supply-chain rights checks and independent user acceptance are **release gates**. Worldwide market coverage, guaranteed alpha, full historical backtesting, unlicensed real-time public feeds and automated trading are outside v1.0.
