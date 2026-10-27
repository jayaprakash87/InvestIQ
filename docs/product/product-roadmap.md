# InvestIQ — Product Strategy and Roadmap

> **Status:** Finalized planning baseline · **Version:** 2.0 · **Date:** 2026-10-27  
> **Implementation baseline:** InvestIQ v0.1.1 (the released open-source Python toolkit).  
> **Decision:** Connected, provider-agnostic investment research with freshness-aware retrieval, optional shared/cloud cache, and immutable reproducible research snapshots.  
> **Nature:** Public product direction and acceptance criteria; **not** a statement that these future features already exist, a guaranteed delivery schedule, or investment advice.

## 1. Executive decision

**InvestIQ will be a connected Investment Research OS, not a local-only company-data application.** A company's share price, quote/volume and news change within a session; consensus estimates, corporate actions and fundamental filings change on other schedules. We cannot treat a copy on an individual's computer as today's market truth. Nor can we overwrite old research inputs whenever market data changes.

We therefore separate two jobs:

1. **Current research view:** Retrieve provider-entitled data on demand, expose its actual market timestamp, entitlement/delay, market session and freshness, and update calculations when those inputs change.
2. **Historical decision view:** Preserve the exact evidence, quote reference or permitted captured value, explicit assumptions, calculation/method versions and creation time for a saved thesis. Reproduce it later without querying today's feed.

**Target architecture:** provider adapters → normalized market/fundamental evidence → freshness-aware retrieval/cache → deterministic research engine → interfaces; a separate immutable research history store records deliberate decisions. Managed cloud infrastructure is an **optional deployment**, not a dependency for using or contributing to the public Python library.

**Next release: v0.2 — Connected Company Research.** A user can select a supported listed instrument, fetch appropriately recent quotes and sourced financial facts under the applicable provider entitlement, calculate a traceable company view, and explicitly save/replay a thesis snapshot. The first vertical slice may be a CLI. Do not build a heavy web app or streaming backend before this journey works.

**Why this, not new AI skills or stock rankings?** v0.1.1 has tested arithmetic, evidence models, five portable research skills and a synthetic end-to-end example. It does **not** have a connected price/fundamental source, accurate freshness semantics, research update/reconciliation, or a real-company end-to-end journey. This is the limiting product gap.

## 2. Product purpose and users

**Mission.** Make company research current *when viewed* and reproducible *when revisited*: show what is sourced, what is assumed, what changes, what is unknown and how conclusions depend on inputs.

**Primary user:** independent investment researcher investigating one or several equities over time. **Secondary:** an analyst, educator or team running repeatable research and peer reviews. **Enabling user:** developer embedding vendor-neutral research and valuation modules.

**Product positioning:** an open-source, evidence-centered research workflow, differentiated by clear information freshness, analytical consistency, explainable assumptions and investment decision history. It is not a brokerage, investment adviser, high-frequency terminal, personal stock picker or guaranteed-alpha engine.

**Experience principles**
- **Freshness visible, never implied.** Show “real-time”, “delayed”, “end-of-day”, “historical” or “unavailable” **only when supported** by actual provider/plan metadata; otherwise mark timeliness unknown.
- **Factual vs hypothetical.** Preserve source-reported facts and analyst/AI-derived interpretations separately. An input price and a valuation target are not both “the stock price”.
- **Supported geography before broad claims.** First supported issuer and venue coverage depends on the chosen licensed data providers. SEC/EDGAR supplies US filing data, not live US/EU stock quotations.
- **Online when needed, offline when justified.** Connectivity supports current research; offline replay supports accountability. The two must never silently substitute for one another.
- **Public and private boundaries.** Repository contains synthetic or redistributable examples only; personal theses, provider credentials and licensed datasets stay in user-controlled storage.
- **Reusable by anyone.** Business logic stays in the portable Python core; cloud hosting, GUI, data providers and AI are adapters, not mandatory product dependencies.

## 3. What exists versus what must be built

| Capability | Released v0.1.1 | Missing for connected product |
| --- | --- | --- |
| Python package, CLI, tests, MIT license | Implemented | Connected commands / packaging of optional adapters |
| Equity valuation math and scenarios | Positive-EPS multiple/CAGR/reverse-valuation primitives | Use timestamped entitled prices and dated fundamentals; additional valuation methods later |
| Attributed numeric evidence | Source, public/recorded times, observation vintages | Market quote/time-series contract, issuer identity and provider-specific normalization |
| Five reusable research skills | Portable procedures and structured report validator | Research inputs assembled from real sources; semantic/source checks |
| Thesis history | Hash-linked versions and JSONL import/export | A user-triggered save/replay workflow with storage adapters |
| Real market data | **Not shipped** | Licensed/BYOK quote provider, entitlement/delay metadata, refresh policies |
| Filings, estimates, news | **Not shipped** | Source adapters with quality, timestamps, licensing and availability guarantees |
| Shared cache/cloud data | **Not shipped** | Optional deployment and entitlement-aware cache when needed |
| Quant backtesting | **Not shipped** | Point-in-time universes, revisions, corporate actions, costs and independent validation |

**Key product distinction:** A live quote can change without creating a new `ThesisSnapshot`. A research snapshot is created only on explicit save (or an approved research workflow), not on every refresh, market tick or data-reconciliation job.

## 4. Data classes, refresh and retention policy

**Refresh policy is a capability, not a guarantee.** Exact timing is a configurable rule that must respect the provider plan, exchange entitlement, trading session and legal use. An illustrative TTL cannot transform delayed data into real-time data.

| Data class | Source / update pattern | Research-view behavior | History behavior |
| --- | --- | --- | --- |
| Last trade, bid/ask, price, volume | Quote REST or stream; session-sensitive | Fetch on request or subscribe only if entitled; show exchange timestamp, received timestamp, market/session, actual delay | Record the quote ID/value only when permitted and selected for an analysis; not every tick |
| Daily OHLCV / longer price history | Provider EOD/time-series API | Fetch current adjusted/unadjusted series with explicit currency, adjustment and cutoff | Preserve the input vintage/reference needed to reproduce saved calculations within license terms |
| Fundamentals | Regulatory filings / provider financial APIs | Refresh on new filing/amendment or scheduled checks; explicit fiscal period and announcement time | Preserve each report vintage and filing provenance; do not overwrite historic facts |
| Earnings estimates / revisions | Entitled consensus provider | Reconcile by source revision/event and provider TTL | Snapshot assumptions/estimates **only** when license permits; never pretend reconstructed consensus is historic |
| Corporate actions and instruments | Reference-data events | Invalidate affected prices, share counts, EPS bases and symbols; time-qualified mappings | Preserve effective dates and applied adjustment/mapping rules |
| FX | FX provider with timestamp and pair conventions | Fetch when conversions are needed; show conversion source/date and limitations | Preserve used rate or lawful reference for repeatable cross-currency results |
| News / company announcements | Provider feeds / filings | Event-driven polling or demand refresh with source timestamp, deduplication and disclosure of coverage | Keep selected references or summaries only under license; do not republish restricted bodies |
| Research theses and scenarios | Explicit researcher action | Compare current inputs with saved position; don't auto-change thesis | Append-only revisions with method/input digests and approved decision rationale |

**Market-time model (required contract):**
- Source/event time (`market_timestamp` or document publication time), response/ingestion time, normalized freshness assessment `as_of`, and viewer request time **are different timestamps**.
- Represent market/exchange, security/share class, quote currency, session/timezone, price kind (last/close/bid/ask/etc.), adjusted status, units, provider ID, delay classification (real-time/delayed/EOD/historical/unknown), known delay duration **if supplied**, and entitlement/reuse scope.
- Prevent a closed-market EOD quote or delayed feed from being labeled “live now”. Market holidays, after-hours, vendor outages and halted securities require explicit states or unknowns.
- No assumed global 24/7 equities market and no fabricated refresh SLA.

## 5. Architecture: logical layers and deployment modes

```text
InvestIQ Interfaces (CLI first; optional later web UI / API / AI skills)
                           |
         Research Application / Orchestration
                           |
    +----------------------+----------------------+
    |                                             |
    v                                             v
Current Information View                   Research Decision View
- on-demand quotations                     - explicitly saved thesis/version
- filing and estimate refresh              - exact input manifest + provenance
- quality and freshness metadata           - methodology/calculation versions
    |                                       - repeatable offline replay
    v                                             |
Provider-neutral Data Access                       v
- Security/issuer resolver                 Durable, user-controlled history
- Quote/fundamental/news adapters          - local or cloud repository adapter
- normalization + entitlements             - immutable versions + audit
    |
    v
Optional cache and refresh service
- in-process cache for single user
- shared managed cache only when justified
- provider/source/entitlement isolation
    |
    v
Licensed provider REST, feed, filing API or user-supplied data
```

**Dependency rule:** provider adapters and persistence depend on documented domain interfaces; valuation math and research logic must not import vendor SDKs or require a running cloud service.

### Supported deployment choices

| Mode | User / usage | Architecture | Decision |
| --- | --- | --- | --- |
| **Library or CLI + bring-your-own provider key** | Developers and independent researchers | Provider APIs on demand, optional bounded in-process cache, local/private thesis snapshots | **First implementation, no cloud prerequisite** |
| **Self-hosted connected service** | Small teams, technical operators | Shared API process, optional database and cache, user/tenant-controlled secrets and entitlement isolation | Supported design target; not mandatory in v0.2 |
| **Centrally hosted InvestIQ service** | Multi-user public product | Data-access gateway, managed provider contracts, entitlement-aware cache, identity/auth, secure durable research store and monitoring | **Conditional future capability**; needs licensing, demand, budget and security review |
| **Full streaming/lakehouse** | Large-scale quant / historical data science | Licensed historical market feed, high-volume storage, bias controls, strategy experiment services | Not justified for v0.2 |

Do **not** provision Redis, Kafka, Event Hubs, Databricks, microservices or a multi-tenant SaaS just to implement v0.2. Keep adapters swappable and documented, allowing these components where operational need later justifies them.

### Cache is not the source of truth

- Adapter-backed cache is an *optimization*. On cache hit, return original source/event timestamp, entitlement/delay class, provider reference, expiry and freshness status. Expired entries are not magically current.
- Define cache policy **per data category/provider/entitlement**. Quote TTL may be seconds or longer depending on actual feed terms; fundamental refresh may follow filings; estimates and news follow separate terms.
- Key cache entries by provider, instrument + venue, quote/series kind, session/time range, currency, adjustment flags and **entitlement/license scope**. Never serve a premium licensed item to an unauthorized caller via a shared cache.
- Stampede protection, backoff, 429 handling, timeouts, circuit-breaking and bounded fallbacks are required before shared deployment.
- Provider fallback requires semantic compatibility and re-labeling of source, timestamp, delay and coverage. Do **not** silently replace live price with delayed/EOD or mix an adjusted series with an unadjusted one.
- If a source is offline, show stale-with-timestamp when explicitly allowed, or fail clearly. Never silently invent or forward-fill unverified prices.

### Saved research snapshots

A user-triggered `save` records:
- instrument/issuer identity and exact calculation inputs (or legally permitted durable source references);
- source IDs, publication/event and retrieval times, data status and quote delay classification;
- assumptions and optional selected price, method/contract versions, scenario parameters and research summary;
- immutable hash-linked thesis version and reviewer rationale.

On `replay`, use the saved admissible input manifest. **Never call today's live feed while pretending to reproduce an old thesis.** When source rights prohibit retention of values, indicate non-reproducibility limitations; do not promise exact offline replay.

Storage location is a separate adapter: local SQLite/private files may serve a single researcher, while a secure managed cloud store may serve permitted hosted deployments. Neither choice makes the underlying *market* data local-only.

## 6. Data-provider strategy and licensing gates

**Avoid a single mandated provider.** Publish small provider-neutral interfaces and one end-to-end adapter at a time; establish coverage, rights, latency and identity semantics before choosing the default.

**Candidate source classes (to evaluate, not implemented or committed):**
- **Company filings:** SEC EDGAR submissions / XBRL Companyfacts for eligible US issuers. Supplies reported corporate facts and filings, not streaming quotations. Respect fair access, user-agent guidance, and data context including amended statements and actual filing dates. <https://www.sec.gov/edgar/sec-api-documentation>
- **Consolidated fundamentals / estimates:** Financial Modeling Prep or other appropriately licensed APIs. Coverage, depth, caching and redistribution require plan-specific verification before selection. <https://site.financialmodelingprep.com/>
- **Equity market prices and historical bars:** Massive (formerly Polygon.io) or another entitled quote/history provider. REST vs WebSocket, real-time vs delayed/EOD, exchange permissions and use/redistribution rights depend on the contract and market. <https://massive.com/docs/>
- **Optional provider aggregation:** OpenBB or similar integration may help access multiple adapters, but it must remain optional and should not become core domain logic. <https://docs.openbb.co/>

**Provider decision matrix (must be completed before PR 2):**

| Criterion | Must demonstrate |
| --- | --- |
| Instruments and markets | Supported region, venue/MIC, issuer and share class; what is missing |
| Timeliness | Quote source timestamps, session coverage, plan-specific real-time/delayed/EOD entitlements |
| Historical correctness | Adjustments, amendments, corporate actions, estimates vintages, availability |
| Allowed use | Personal/BYOK vs hosted display, caching, redistribution, public examples and derived metrics |
| Engineering | Documented API, errors, rate limits, retry guidance, pagination, outage handling |
| Cost | Free/paid tiers, quota limits, estimated usage under representative research scenarios |
| Access/security | Credential handling, license isolation, no leakage in CI/public fixtures |

**Deployment policy:** an MIT-licensed client library can let users bring their own permitted API key. A public hosted service cannot assume the same commercial exchange data can be redistributed freely. If no legally usable live feed is available, v0.2 must **truthfully ship as delayed/EOD connected research** with explicit labeling, or remain at release-candidate status until its advertised minimum is met.

No public project fixture may embed copyrighted paid datasets or personal brokerage information. Public sources are not necessarily unrestricted to republish. Provider selection is a gated decision, not a promised coverage or latency guarantee.

## 7. Release roadmap (ordered, no fixed dates)

| Release | Theme | Core user outcome | Release gate |
| --- | --- | --- | --- |
| **v0.1.1 — Released** | Portable research toolkit | Run deterministic, source-aware *synthetic* research offline | Existing release verified |
| **v0.2 — Connected Company Research** | **NEXT** | Retrieve time-labeled real company fundamentals and appropriately current price, calculate and save a sourced research snapshot; replay when permitted | One real supported company, transparent price delay/entitlement, end-to-end reproducibility |
| **v0.3 — Fundamental & Peer Intelligence** | Compare with context | Track fundamental trends and compare genuinely comparable peers using time-aligned current inputs | Comparable periods/currency, sources, errors and sector distinctions |
| **v0.4 — Research Updates & Decision Intelligence** | Understand changes | Identify what changed in quotes, filings, estimates and explicit thesis assumptions; alert/review only on opt-in | Timed delta evidence, no automatic rewriting of historical theses |
| **v0.5 — Accessible Research Experience** | User-facing workspace | Interact through optional local/hosted GUI, inspect sources and scenario sensitivities without coding | User-tested usability, privacy, costs and licensed hosted feed gate |
| **v0.6+ — Quant Research Lab** | Empirical strategy testing | Explore risk-aware factor/portfolio hypotheses with historical data of demonstrable quality | Look-ahead/survivorship/corporate-action/cost and out-of-sample safeguards |
| **v1.0 — Stable Open Research Platform** | Mature interoperability | Dependable schemas, adapter ecosystem, documentation, stable user journeys and community contributions | External users, migration/compatibility policy, long-term maintenance and security posture |

These versions express direction, not guaranteed future releases. A fund, ETF, algorithmic mutual fund, autonomous trading platform or managed-account service is *not* a committed milestone.

## 8. v0.2 — Connected Company Research PRD

### User story

> “I select a supported company, obtain the freshest **legally available and correctly labeled** quote and sourced financials, see exactly when the numbers were valid, test a valuation, and choose whether to save a dated, reproducible thesis. Tomorrow's refreshed price should not erase yesterday's reasoning.”

### Minimum end-to-end flow

1. **Resolve company and instrument**: support issuer/reporting identity separately from venue-qualified ticker/currency; no arbitrary ticker-only joins.
2. **Fetch on demand**: use a configured entitled quote provider and filing data provider. Return source/market time, received time, session, currency, availability/delay status and license capabilities.
3. **Normalize**: map a bounded financial statement metric catalog and valuation input contracts; validate period, units, share class, amendment and FX/adjustment semantics. Decline ambiguous conversions.
4. **Compute**: show sourced business fundamentals and calculations; derive price-sensitive P/E and scenario outputs from the selected quote timestamp. Clearly mark outdated, unavailable or inapplicable methods.
5. **Inspect and refresh**: report source links and freshness status; on refresh, fetch/calculate again, with safe fallback and visible differences. **No thesis revision from quote refresh alone.**
6. **Save explicitly**: preserve a versioned research snapshot, assumption and selected input manifest under the user-controlled storage backend, subject to source permissions.
7. **Replay**: reconstruct saved results without fresh calls wherever licensing and retention allow, and flag any non-replayable external dependencies.

### Must-have contracts

**A. Instrument and source identities:** issuer/reporting ID vs share class/instrument (venue MIC, currency, symbol effective dates); source provider and identifiers; versioned mapping resolution.

**B. Price and time:** quote kind, currency, market event time, provider observation time (if distinct), fetched/received time, exchange/session and timezone, entitlement, delayed duration if verifiable, adjusted status, staleness threshold/assessment, provider data rights.

**C. Fundamentals:** metric dictionary, filing/accession and report periods, public-availability qualification, revision/amendment lineage, reported vs derived vs consensus, comparable share/currency/accounting basis, missing and conflict diagnostics.

**D. Analysis:** `CurrentResearchView` and `ResearchSnapshot` are separate concepts. Current view may refresh; snapshots are immutable with source/method version references.

**E. Provider integration:** capabilities (quotes/financials/estimates/news), sync/async adapter interface, explicit failure modes, opt-in networking, BYOK secrets, rate limits, cache metadata, permitted reuse. No mandatory vendor SDK in the core.

### v0.2 acceptance criteria — all mandatory

1. **Genuine connected case:** analyze ≥1 supported real issuer and listed instrument using legally accessible filing source and one permitted price source. Label it according to *actual* provider real-time, delayed or EOD entitlement. Do not claim worldwide support.
2. **Freshness demonstration:** show price timestamp, market/session and effective delay/unknown with user-facing stale/closed-market messages. A forced late cache response cannot be reported as live.
3. **Change behavior:** after a new permitted quote, price-sensitive calculations change deterministically while earlier saved thesis snapshots remain unchanged. Refresh should not generate redundant thesis revisions.
4. **Financial provenance:** show source/report period, fiscal units, filing/publication qualifiers and amendment handling for each material reported metric; invalid, missing and incompatible facts fail clearly.
5. **Provider robustness:** exercise 401/403, 429, timeouts, provider outage, unsupported region, ambiguous symbols, missing historical vintages, currency and corporate-action mismatch, stale cache and entitlement-denied cases. Forbidden providers must not be bypassed via fallback.
6. **Reproducibility:** saved snapshot can be replayed from its permitted retained input manifest on a fresh installation without calling today's provider. Any legally unavailable retained inputs must be conspicuously disclosed.
7. **Licensing and security:** confirm plan/API rights for the chosen demo; redacted logs, no private keys or holdings in public Git, cache user/entitlement isolation if shared, documented quota/cost behavior.
8. **Developer/public usability:** fresh checkout/wheel, one supported connected company flow, CLI instructions, deterministic fixtures, CI and independent tester walkthrough. Do not invent usage statistics, provider speed or outcomes.
9. **Code quality:** numerical/semantic domain tests, adapter-contract tests, snapshot tests, installed-wheel smoke, minimal CI runs and no unresolved critical code/security findings.

**No implied promise:** v0.2 does not require real-time streaming, automated price updates every second, multi-region exchange support or a hosted cloud deployment; truthful delayed/EOD connected data is acceptable if clearly designated and useful.

### Implementation order — six outcome-based PRs

| PR | Outcome | Deliverable / acceptance | Dependency |
| --- | --- | --- | --- |
| **1. Provider-neutral market-data architecture** | Correct domain model before vendor integration | ADR, quote/fundamental/time/freshness/entitlement models, issuer mapping, capability/failure contracts, synthetic validation tests | v0.1.1 |
| **2. Provider adapters and source evaluation** | Real licensed/entitled data enters InvestIQ | SEC filing adapter plus one price-data provider selected via documented comparison; BYOK and deterministic test doubles, limits/errors/fallback rules | PR 1 |
| **3. Connected data service and cache** | One reliable research view | On-demand retrieval, normalization, source-specific freshness rules, in-process bounded cache, optional shared-cache interface; entitlement isolation and invalidation tests | PRs 1–2 |
| **4. Connected research analysis** | Current company view yields traceable analysis | Source-linked fundamentals, price-sensitive valuations, support for refresh and delay/staleness messaging, negative-EPS and currency guardrails | PRs 2–3 |
| **5. Durable research snapshots and outputs** | User controls what is saved | Portable storage interface, single-user private local implementation first with cloud-ready backend contract; explicit save/replay, Markdown/JSON reports, lawful retention limits | PRs 1–4 |
| **6. v0.2 integration and acceptance** | Release-quality usable connected workflow | Real-company walkthrough, provider terms verification, resilient negative-case suite, snapshot replay, user trial, complete documentation and release signoff | PRs 1–5 |

Keep **outcome-based** PR scope: combine related fixes/tests/docs in the same PR; never create one PR per helper or trigger redundant CI per micro-commit. Preserve CI and Codex review gates; substantial product choices get ADRs.

### Deliberate v0.2 non-goals

Hosted public SaaS, user sign-up and billing, global live market coverage, exchange redistribution licenses, large shared price database, multi-tenant authorization, cloud streaming infra, subscriptions, autonomous portfolio rebalancing, options/derivatives, order execution, AI-generated financial facts, automatic investment ratings or quantitative outperformance claims.

## 9. v0.3 — Fundamental trends and comparative intelligence

**User outcome:** compare compatible businesses and understand price/valuation context **as of a selected time**.

- Period-aligned revenue/earnings/FCF/cash-conversion and balance-sheet analysis; explicit adjusted vs unadjusted conventions and issuer metric applicability.
- Cross-company and cross-currency comparisons only with attributable FX timestamps, periods, inflation/reporting conventions where material.
- Peer group and value-chain relationships (competitor/supplier/substitute) instead of thematic pseudo-peers; industry packs for software, semiconductors, industrials, utilities etc.
- Add EV, FCF yield/DCF/reverse valuation methods when source definitions and debt/cash/share calculations can be validated. Inapplicable multiples remain N/A.
- Track short-horizon market/catalyst signals separately from multi-year business trajectory and current-price underwriting.
- Source-aware watchlists may be introduced as research collections, **not** investor holdings or trade recommendations.

**Gate:** two to five supported peers analyzed with consistent price-time context; correct rejection of misleading comparisons and unknown data.

## 10. v0.4 — Research updates and decision intelligence

**User outcome:** “Since my saved thesis, did the price change, did fundamentals/estimates change, or did my assumptions change?”

- Selective, permissioned refresh/polling (fundamentals/news/consensus), event reconciliation, as-of deltas and materiality thresholds.
- Explain quote-driven vs earnings-driven vs consensus-driven valuation changes; never manufacture a new investment hypothesis solely due to market ticks.
- Preserve earlier source vintages, methods and assumptions; explicit human-approved thesis revisions and change reasons.
- Alerting or watchlist updates are **opt-in** and scoped to source licensing, cost and supported schedules. No mandatory background agent.

**Gate:** reproduces prior research and explains real observed changes without hindsight contamination or silent provider shifts.

## 11. v0.5 — Optional research UX and hosted deployment

- Simple chart/table/document interface, visible source/freshness badges and scenario what-if controls. Test whether a lightweight local UI suffices before a full SPA.
- Cloud-hosted multi-user operation is a **separate deployment decision**, gated on user demand, privacy/security design, broker-free account management and exchange/third-party data redistribution rights.
- If entitled licensed sharing and viable costs are absent, offer self-hosted/BYOK instead of a public “free live quote” promise.
- AI-generated drafting remains optional, provider-independent, subject to evaluation for missing citations and factual fidelity; deterministic calculations remain authoritative.

**Gate:** usability validated with independent users; entitlement, cloud cost and user-data protection addressed before public hosting.

## 12. v0.6+ quantitative research and hypothetical investment products

Conditional future work only after historic universe, delistings, corporate actions, FX, survivorship, revision timestamps, benchmark alignment, transaction costs and out-of-sample validation are available with appropriate data rights.

- Transparent factor research with predeclared rules and prospective paper portfolios, not post-hoc multibagger claims.
- Report turnover, exposures, drawdowns, economic regimes and failure scenarios before any claim of alpha.
- A strategy/index license, algorithmic ETF or mutual fund requires a separate business/regulatory plan and authorized partners. It is **not part of current InvestIQ development approval**.

## 13. Product metrics, governance and risk

**North-star:** share of new users who can generate a truthful, source-linked **current company research view** and deliberately save/reproduce one historical snapshot.

**Product quality measures** (measured in tests or by opt-in feedback; never default telemetry):
- Source/time attribution coverage: target **100% of official surfaced market prices and reported numeric claims**; real-time/delayed/EOD/unknown label visible.
- Data freshness: provider-class policy adherence; no fresh label for expired or unsupported cache entries.
- Current view vs saved thesis: deterministic calculation changes after input updates, **zero accidental history mutations**.
- User experience: documented time-to-first-research flow, provider setup friction, fail-closed errors and recovery.
- Economics: API requests per research workflow, cache hit rate by entitlement group, quota and cloud service costs **only where measured**.
- Responsible research: no undocumented estimate interpolation, trading guarantees, unlicensed public data distribution or fabricated provider behavior.

**Risk register**

| Risk | Mitigation / owner decision |
| --- | --- |
| Real-time data costs and exchange rights | BYOK/self-host first, verify provider entitlements, mark delay, host only when commercially licensed |
| Stale/incorrect price and after-hours sessions | Strict timestamps/session metadata, source-aware TTL, fail closed or display visibly stale data |
| False comparability and corporate actions | Explicit units/currency/share-class/revision mapping and negative-case tests |
| Vendor concentration | Small adapters, capability discovery, optional alternate provider with semantic consistency checks |
| Look-ahead and corrupted research history | Public vs recorded timestamps, immutable input manifests, no implicit refresh during replay |
| Privacy and secret leakage | No keys in repo, local private storage option, encrypted secure host store only after review |
| Overengineering / infrastructure spend | Start direct API calls and in-process cache; add shared cache/cloud only on measured need |
| AI hallucination and confident rankings | Evidence-linked drafts, semantic evaluation, deterministic arithmetic and human approval |

**Governance:** this document is the **final agreed v2.0 architecture/product planning baseline**. Future roadmap changes require explicit review/ADR and subsequent PR; “final” does not mean future user findings cannot change priorities. No product implementation is implied by merging these documents.

## 14. Immediate next action

Start **v0.2 PR 1: provider-neutral contracts and architecture ADR**. Define and test quote timestamp/entitlement/freshness models, issuer/security mappings, provider capability/failure types, a separate current-view versus saved-research boundary and a selected-provider comparison matrix.

**Do not** begin with SQLite-only persistence, a public web server, a streaming lakehouse or a new stock-scoring engine. First prove the live-or-delayed connected view and explicit history semantics, then add data providers and optional deployment components as needed.

---
**References for source-evaluation candidates:** [SEC EDGAR API documentation](https://www.sec.gov/edgar/sec-api-documentation) · [Massive market-data APIs](https://massive.com/docs/) · [Financial Modeling Prep](https://site.financialmodelingprep.com/) · [OpenBB](https://docs.openbb.co/). Their availability, products, contracts and quotas must be verified at implementation time. **No paid data entitlement or global live market coverage is assumed.**
