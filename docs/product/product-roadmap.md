# InvestIQ Product Strategy and Roadmap

> **Status:** Proposed for community review · **Version:** 1.0 · **Updated:** 2026-10-27  
> **Baseline:** InvestIQ v0.1.1, verified against the public `main` branch on 2026-10-27.  
> **Audience:** Maintainers, individual investors conducting their own research, financial researchers, educators, and open-source contributors.  
> **Scope:** Product outcomes and release sequence; not a promise of dates, investment returns, or regulated services.

## 1. Executive decision

**Build v0.2 around one complete real-company research journey.**

InvestIQ v0.1.1 is a working, locally installable research **toolkit**, not yet a working investment **research product**. Its financial models, citation contracts, five portable skills, hash-linked thesis history, and `investiq demo`/`investiq validate` CLI are useful foundations. However, the shipped integrated workflow uses fictional observations. A normal user cannot yet point InvestIQ at a company's filings, reliably import facts, produce a source-linked dossier, save the result, and repeat it after a new filing.

The next release must close that gap rather than add another AI agent, a general-purpose dashboard, a universal stock ranking, or an early backtesting engine.

**v0.2 product promise:** *A researcher can import real, lawfully accessible company financial evidence, inspect what is known and missing, produce a reproducible company dossier, and store it locally—without writing Python or paying for a market-data subscription.*

Product direction: **Open-source Research OS → Comparative Investment Intelligence → Research Memory & Monitoring → Optional Local UX → Quantitative Research Lab.** An algorithmic fund or ETF is a separate, long-horizon regulated business possibility, not a planned software feature.

## 2. Product positioning

**Mission.** Help anyone investigate public companies with reproducible calculations, transparent source links, explicit assumptions, historical context, and auditable revisions.

**Primary user:** an independent researcher who needs an evidence-backed view of one company and wants to revisit that view after facts change. **Secondary:** an analyst or educator comparing companies and documenting judgment. **Enabling user:** a developer embedding the core, CLI, or skills in a workflow.

**Differentiation to pursue:** research *traceability and decision history* plus industry-aware financial analysis, rather than an unverified predictive score or a prettier market-data feed. The system must help answer: *What did the evidence show? What did we assume? What changed? What do we now conclude—and why?*

**Principles and product constraints**

1. **Human judgment is explicit.** Distinguish reported facts, external estimates, researcher assumptions, calculated results, and AI-generated interpretation. No silent promotion from one class to another.
2. **Reproducibility before automation.** A saved research snapshot must reproduce without a live network call. Preserve accession/source identity, input versions, methodology version, calculation version, retrieval time, and any corrected vintages.
3. **No invented or silent data.** Missing is not zero; incomparable fiscal periods are not silently combined; corporate actions, currencies, share classes, restatements, and reporting dates require explicit handling.
4. **Portable and private by default.** Python core and CLI first; local storage; optional network adapters; no account, tracking, brokerage, hosted LLM, or paid API required.
5. **Evidence-based claims only.** Structural validators cannot fact-check narrative claims; an AI skill's output is draft research pending source/semantic review.
6. **Open-source and legally usable.** MIT covers code, not third-party datasets. Separate source-use, redistribution, fair-access and attribution policy.
7. **Incremental product, not scaffolding.** Every release must add one demonstrable end-to-end user outcome. Avoid placeholder services and premature microservices.

## 3. Current product assessment

| Dimension | Confirmed in v0.1.1 | User gap / limitation | Impact |
| --- | --- | --- | --- |
| Calculations | Positive-EPS P/E, growth/CAGR, reverse valuation, weighted scenarios | No sourced real-company modeling workflow; no FCF or enterprise-value methods yet | High |
| Data provenance | Source, publication/recorded dates, instrument, units, revisions | No normal filing importer, identifier history, metric taxonomy or data-quality diagnostics | **Critical** |
| Research skills | Five portable `SKILL.md` procedures | No automatic input preparation or independently tested semantic factuality | High |
| Decision memory | Hash-linked thesis vintages, JSONL import/export | No local company workspace, search, durable indexed store, human review workflow | High |
| Product UX | Installable CLI and fictional `demo`/`validate` | No `company → source → dossier` workflow for real evidence | **Critical** |
| Research comparison | Building-block contracts | No comparable periods, industry packs, peer matrix or trend view | Medium |
| Quant research | Principles and future intent only | No proven historical vintages, delistings, corporate-action engine or cost model | Blocked |
| Distribution | MIT, public repository, wheel/sdist, CI, release automation | Limited novice onboarding; no user-validated nontechnical workflow | Medium |

**Interpretation:** v0.1.1 is an *engineering foundation*. Product-market value will be demonstrated when a user can create a useful research artifact from real evidence, not merely run a successful test suite.

## 4. Prioritization and rationale

Use qualitative impact, dependency, and verification risk, rather than invented precision in weighted feature scores.

| Candidate | User value | Dependency / delivery risk | Decision |
| --- | --- | --- | --- |
| Real filing/local-data ingestion with full provenance | Transformative | High, but unlocks everything else | **P0 — next** |
| Persistent local company workspace | Very high | Moderate | **P0 — same release** |
| Deterministic, source-linked company dossier | Very high | Moderate after ingestion | **P0 — same release** |
| Clear metric definitions, period alignment, missing-data explanations | Very high | High domain correctness requirement | **P0 — same release** |
| Semantic verification/evaluation of AI draft findings | High | Needs reliable gold/source fixtures | P1 — before AI-assisted reports become default |
| Cross-company comparisons and fundamental trends | High | Requires normalized, comparable data | P1 — v0.3 |
| Thesis change detection and research updates | High | Requires stored, versioned real evidence | P1 — v0.4 |
| Local graphical UX | Medium–high for nondevelopers | Depends on proven workflow | Conditional — v0.5 |
| Portfolio dashboards / automated stock rankings | Medium | Risk of misleading output without comparability | Later |
| Backtesting / systematic strategies | Potentially high | **Blocked by point-in-time and survivorship-safe market datasets** | Conditional — v0.6+ |
| Broker execution, autonomous trading, a managed fund | Outside core open-source research | Financial, regulatory and operational risks | **Explicitly deferred** |

### North-star user outcome

A **completed reproducible company dossier**: a saved research result with attributable figures, methodology/version, explicit assumptions and data gaps, generated from an actual permitted input source and reproducible using its saved snapshot.

Do **not** use stock-price appreciation, simulated strategy returns, number of installed skills, total lines of code, or GitHub stars as the v0.2 quality measure.

## 5. Release roadmap

This is an **order of delivery**, not a fixed-date commitment. Each version is conditional on the preceding release gates.

| Release | Theme | Primary user outcome | Key deliverables | Gate |
| --- | --- | --- | --- | --- |
| **v0.2 — Real-Company Research** | **Now** | Build and save a sourced real-company dossier | Input adapter, optional SEC importer, metric catalog, local store, dossier export, CLI | End-to-end real filing successfully reproduced offline |
| **v0.3 — Fundamental & Peer Intelligence** | Next | Understand trends and compare compatible companies | Period alignment, 2–5 peer comparison, normalized metrics, industry packs, alternative valuation methods | Comparable evidence and correct missing-data behavior |
| **v0.4 — Research Updates & Decision Intelligence** | After v0.3 | Explain exactly what changed in evidence and thesis | Source-update diff, human-approved thesis revisions, research review inbox, change report | Reproducible change log with no hindsight overwrite |
| **v0.5 — Accessible Research Workspace** | Demand-gated | Complete the research journey without CLI expertise | Simple local-first interface, readable reports, export/import, optional AI-draft workflow with evaluations | Independent novice user testing and privacy/security checks |
| **v0.6 — Quant Research Foundations** | Data-quality-gated | Evaluate *testable* systematic hypotheses, not sell an algorithmic fund | Data-quality checks, point-in-time historical universe, benchmarks, cost-aware strategy experimentation | Bias/cost/reproducibility controls demonstrated |
| **v1.0 — Trusted Open Research Platform** | Maturity-gated | Stable public research workflow with community contributors | Supported contracts, migrations, broader source adapters, robust docs and support policy | External adoption, full release gates, compatibility and security review |

**Not implied:** every v0.x release must be created, or a fund/ETF must follow v1.0. Priorities change based on user validation and evidence quality.

## 6. v0.2 Product Requirements — Real-Company Research

### The job to be done

> “I want to investigate a listed company using its published financial statements, see the source of every important figure, explain what is missing, test explicit valuation assumptions when appropriate, and preserve an auditable research snapshot.”

### The first supported journey

1. **Select a security or reporting entity.** Resolve a verified issuer/reporting ID; distinguish issuer from a traded share class. A ticker alone is not a stable historical identifier.
2. **Import evidence.** Accept a documented local CSV/JSON mapping as the always-available path. Add a separately optional **SEC EDGAR submissions/Companyfacts** adapter for US-reporting issuers only after validating source semantics and fair-access behavior.
3. **Normalize and diagnose.** Map a bounded set of financial concepts to canonical metrics, with fiscal period, units, reporting basis, filing/accession ID, `filed_at` or better verified public-availability time, retrieval timestamp, and local recording date. Reject unsupported or ambiguous mappings.
4. **Store an immutable local snapshot.** Preserve raw-source reference/payload metadata and normalized observations; deduplicate idempotently and distinguish restatements. Use local SQLite for indexing plus optional portable JSON/JSONL export. User data must remain outside Git.
5. **Generate a company dossier.** Export readable Markdown and machine-readable JSON, both with metric tables, per-fact source references, availability dates, coverage gaps, explicit analyst assumptions, risk questions and an optional scenario calculation.
6. **Replay offline.** Reproduce the saved dossier with no network, using the same snapshot and method versions. Revision/change comparison is available through the existing thesis ledger, after explicit user approval.

### v0.2 minimum functional scope

**Data entry and identifiers**
- Local CSV/JSON import **first**; document field mappings, validated errors and sample synthetic fixtures. No key or Internet access needed for this path.
- One optional, opt-in SEC source adapter using public EDGAR submissions and structured company facts. Respect the SEC developer/fair-access guidance, identify the application in requests, cache responses, throttle and retry bounded failures; never scrape circumvented or gated sites.
- Require issuer-to-security mapping approval when ambiguous. Model CIK (issuer) separately from `ticker + venue MIC + trading currency` (instrument). Keep alternate names, share-class distinctions and effective date of mappings where known.
- Preserve source access and publishing timestamps separately from fiscal period end. If only a filing *date* is available, do not claim the fact became available at an invented intraday timestamp.

**Metric catalog (v0.2 seed, not a universal chart of accounts)**
- Start with selected US nonfinancial issuer concepts: revenue, operating income, net income, diluted EPS, operating cash flow, capital expenditures, cash, debt, diluted shares, and derived FCF where components are compatible.
- Publish each metric's definition, period kind (stock/flow), units, currency, permitted source tags, adjustments, calculations, limitations and missing/incomparability behavior.
- Do not indiscriminately choose the latest `companyfacts` entry for past periods; separate original and revised filing vintages. Exclude ambiguous XBRL facts rather than picking a plausible but wrong one.
- For no/negative earnings, P/E scenarios must show **not applicable** rather than a misleading valuation. An entry price is optional, user-supplied and time-stamped; never misrepresent it as a live quote.

**Workspace and report**
- An offline local-first workspace that stores issuer identities, source references, observations, snapshot versions, assumptions, thesis revisions and report artifacts.
- Report sections: identity/as-of summary; 3-year financial overview where data supports it; accounting/fiscal basis; provenance and coverage table; trends/ratios that can be safely computed; uncertainty and quality warnings; dated assumptions; thesis questions; scenario sensitivity if valid.
- Export Markdown + JSON (HTML/PDF optional later, not required). No automated “buy/sell,” confidence theater or synthetic star ranking.
- A user command sequence should make tasks discoverable. **Proposed commands only (not shipped):** `investiq research init`, `investiq ingest local`, `investiq ingest sec --online`, `investiq research build`, `investiq research export`.

**Research skills**
- Continue supporting manual, model-agnostic `SKILL.md` files. Let researchers optionally attach structured skill output.
- Do not have an LLM fabricate missing inputs or recalculate authoritative amounts; separate computed ratios from generated prose.
- Do not market structural citation validation as proof of semantic fact-checking.

### v0.2 explicit non-goals

No multi-tenant SaaS, account/auth system, automated personalized investment advice, live prices, auto execution, alerts, portfolio syncing, subscriptions, GPU/agent framework, generic international filing coverage, universal company ranking, benchmark performance or proper point-in-time backtesting.

### v0.2 release acceptance tests

A release is accepted **only if all must-pass checks succeed**:

1. **Real-company demonstration:** with permitted SEC data or a valid user-provided extract, produce at least one complete dossier from real reported filings; reproduce it offline from the saved snapshot. Document the exact input sources and retrieval date. Public Git fixtures must not include material whose redistribution is prohibited.
2. **Coverage:** the demonstration should cover three fiscal years when available; each displayed reported numeric fact must have an issuer, fiscal period, unit/currency, source/filing identity and public-availability qualifier. Unavailable information must be marked missing, never silently imputed.
3. **Negative-case tests:** missing concept, duplicate facts, amended filing, inconsistent fiscal duration, reversed currency, incorrect share class, negative EPS, conflicting revisions, API timeout/429, malformed source, unrecognized ticker and late-publication counterexamples.
4. **Storage:** repeated import is idempotent; original vintages are not overwritten; schema migration and backup/restore tests succeed; nothing in the public repo contains personal holdings or credentials.
5. **Reproducibility:** an independent machine can install the wheel, ingest a documented sample, export a dossier, and reproduce an identical normalized result from the saved snapshot without network.
6. **Usability:** at least three independent trial users, including one without Python development experience, attempt the documented workflow. Target: one successful dossier within 20 minutes using a prepared local source; record issues and failures rather than asserting success prematurely.
7. **Engineering:** lint, unit, integration, packaged CLI and source-schema contract checks are green; dependency/license review is completed; no unresolved critical security/financial correctness findings.
8. **Honesty:** no unsupported claimed investment returns, fabricated source times, unsupported valuation ratio or unchecked AI summary in official examples.

The 20-minute goal and trial-user target are **proposed acceptance thresholds**, not observed results.

### v0.2 outcome-based implementation PRs

| Order | Proposed PR | Outcome / acceptance | Depends on |
| --- | --- | --- | --- |
| **1** | Research contracts & metric dictionary | Issuer/instrument mapping, source-vintage identity, metric definitions, schema version/migration strategy and contract tests | v0.1.1 |
| **2** | Local ingestion with audit diagnostics | User-provided CSV/JSON input produces validated observations, precise errors and reproducible public synthetic fixtures | PR 1 |
| **3** | Local research workspace & snapshot lifecycle | Append-only research records, idempotent imports, versioned schema, backup/export/replay, local-only privacy tests | PR 2 |
| **4** | Optional SEC financial-data adapter | Selectable issuer ingest, deterministic tagging and source links, fair-access safeguards, offline cache and adapter tests | PRs 1–3 |
| **5** | Dossier engine and usable CLI journey | Import → inspect → calculate → export a readable dossier plus JSON, with gaps and source evidence | PRs 2–4 |
| **6** | End-to-end v0.2 acceptance & release | Reproducible real-company example, three-user trials, negative-case suite, wheel install, documentation and release sign-off | PRs 1–5 |

Combine closely related small changes into an outcome PR when safe; **do not** split into one PR per test or helper. Do not merge the next outcome with failing CI, unresolved substantive review findings, or undocumented data semantics.

## 7. v0.3 — Fundamental & Peer Intelligence

**Outcome:** two to five public companies can be compared using genuinely comparable periods and economically relevant metrics.

- Comparable TTM/annual/quarterly presentation with currency and accounting-basis warnings, restatement handling and share-class checks.
- Metric-specific quality, growth and cash-economics trend summaries, including peer-relative growth, operating margins, cash conversion and capital intensity where supported.
- An industry-pack extension interface for distinct economics (for example semiconductors vs industrial services vs electrical infrastructure). Do not force identical scores on unlike businesses.
- Additional valuation methods only after input semantics are tested: FCF yield, EV/EBITDA or related multiples, net debt and earnings-power scenarios. Explain assumptions and omit inapplicable ratios.
- Deterministic comparison reports plus a thesis-challenge section; an optional, experimentally evaluated AI interpretation adapter is **not** the arithmetic engine.
- Publish a versioned methodology note explaining why business quality, valuation attractiveness, 3–6-month catalysts and multiyear optionality are different dimensions. No unexplained master score.

**Gate:** demonstrate comparisons that correctly refuse false equivalence and produce the same results from saved dated sources.

## 8. v0.4 — Research Updates & Decision Intelligence

**Outcome:** a researcher can answer “What changed since the last investment thesis, and why?”

- Delta reports distinguish new filings, restatements, assumption changes, model version changes, and changes caused only by source revisions.
- Human-approved immutable thesis snapshots, commentary, confidence rationale, risk/invalidation checkpoints and evidence diff.
- Local “review inbox” for newly ingested filings and unresolved data gaps. Optional scheduled polling must be an explicit opt-in, with clear source controls; no default background surveillance.
- Reproduce a previous conclusion from its exact prior evidence set, not today's revised figures.
- Export a public, anonymized case study **only** after explicit opt-in and validation that no personal data or restricted extracts are included.

**Gate:** all changed conclusions have traceable drivers; unchanged source data does not create unexplained new rankings.

## 9. v0.5 — Accessible Research Workspace

**Outcome:** non-developers can research a company without learning CLI syntax.

- Validate the v0.2/v0.3 workflows with external users **before** selecting a UI stack.
- If demand is demonstrated, ship a simple local-first interface for importing evidence, reading dossiers, comparing peers and reviewing thesis history. Export plain HTML/Markdown early; a heavy SPA or hosted service is not mandatory.
- Present unknowns and source citations alongside figures, not buried behind expandable fine print.
- If users want AI drafting, provide optional plug-in integrations with explicit model/cost and privacy controls; develop independent evaluation fixtures and human sign-off first.
- Accessibility, installability and ordinary-user error recovery are release criteria.

**Gate:** observed improvement over the CLI in task completion and comprehension; no forced network account or secret upload.

## 10. v0.6+ — Quantitative Research Lab and Investment Products

**Only pursue backtesting after a distinct data-quality gate**: historical universe including dead/delisted securities, corporate actions, time-of-availability and revisions, currency/FX, survivorship safeguards, transaction costs, benchmark alignment, model/parameter freeze and reproducibility.

- Begin with transparent factor and portfolio **research** (quality, improvement, expectations/valuation, risk) and simple published baselines.
- Separate training, validation, out-of-sample, and prospective paper results. Report turnover, drawdowns, sector/region/factor exposures, cost sensitivities and failure cases.
- Do not claim “multibagger prediction” or systematic outperformance based solely on a composite ranking or backtest search.
- A public methodology paper can follow reproducible empirical evaluation. A strategy/index licensing business, managed account, mutual fund or ETF requires independent economic validation, legal review and appropriately regulated partners. **No fund launch is in the committed software roadmap.**

## 11. Architecture evolution

Preserve the direction `source adapters → normalization/evidence → calculations/research domain → local persistence/application workflows → CLI, exporters, optional UI/skills`. Domain logic remains outside the CLI and optional AI integration.

- **Core:** existing deterministic calculation and evidence contracts; extend through documented schemas, not hidden provider-specific logic.
- **Adapters:** opt-in `providers/` or equivalent modules; no mandatory external source or proprietary vendor lock-in.
- **Storage:** local SQLite adapter for atomic, indexed, user-owned research records; JSON/JSONL for portable exports, not a substitute for transactional storage.
- **Reporting:** deterministic dossier generation with citation tables and human-approved interpretation. Make output versions explicit.
- **Interfaces:** progressively CLI → Markdown/HTML export → optional local GUI. Defer cloud SaaS, authentication and microservices until proven need.
- **Testing:** unit/mapping tests, realistic-but-redistributable source fixtures, integration replay tests, evolving schema migrations, release-wheel smoke tests and independently maintained source-quality checks.

**Security/trust boundaries:** treat filing text, third-party PDFs, web content and optional model output as untrusted input. Never execute commands extracted from filings or AI text. Bound downloads and parsing, sanitize report exports, redact secrets, keep private storage out of Git, and require consent before networking.

## 12. Data-source policy and verification

**First public source candidate:** the SEC's `data.sec.gov` APIs for EDGAR submissions and XBRL company facts. SEC documentation describes publicly accessible APIs subject to site security and fair-access rules. This supports a **US-reporting issuer-first** scope, not automatic global coverage. See [SEC Data APIs](https://data.sec.gov/) and [SEC developer documentation](https://www.sec.gov/edgar/sec-api-documentation).

**Identifier mapping candidate:** OpenFIGI v3, optionally, for stronger symbology handling across exchanges; free access is rate-limited without an API key, and mappings should still be checked against the issuer and share class. See [OpenFIGI v3 documentation](https://www.openfigi.com/api/documentation).

Before implementing any external source, verify and document: authorization, acceptable automated request frequency, publication/filing timestamp meaning, API evolution, response error semantics, caching and redistribution permissions. Open-source code does not confer the right to redistribute vendor data. Avoid undocumented finance-site scrapers and purchased-data dumps in public examples.

## 13. Measurement and decision rules

**Product measures (collected only through opt-in user feedback, release tests or local self-tests):**
- **Primary:** percent of trial users who complete a reproducible sourced dossier, and what prevented the rest.
- **Trust:** percentage of reported numeric claims with complete citations and source-time qualifiers (target: 100% for official exported dossiers).
- **Correctness:** unsupported/conflicting facts rejected, restatements handled, and same-snapshot repeated reports consistent (target: zero known high-severity failures).
- **Usability:** time to first dossier with a prepared source (v0.2 acceptance target: under 20 minutes), failure/recovery count, documentation clarity.
- **Community:** successful independent installation, actionable contributions, reproducible bug reports and schema-compatible extensions.

**Do not add default telemetry.** Local-only metrics or volunteered, anonymized issue reports are sufficient for early releases.

**Roadmap governance:** review priorities after each release and after real user observations; record major product/architecture decisions as ADRs. Backlog items require a user problem, acceptance criterion, source-risk note and explicit out-of-scope statement. Do not overengineer future concepts before proving immediate workflow value.

### Stop / pivot signals

- **Data normalization:** repeated inability to reproduce filed numbers with correct context means pause advanced features and harden ingestion.
- **User demand:** if researchers cannot complete a dossier, stop additional quantitative factors and fix workflow/UX.
- **Financial validity:** if source data cannot establish historic information availability, do not ship historical strategy performance.
- **External source terms:** if an adapter cannot comply with access/redistribution rights, disable or redesign it rather than bundling restricted data.
- **Operational scope:** if local-first user outcomes are unproven, do not introduce SaaS infrastructure or paid integrations.

## 14. The next concrete decision

**Approve v0.2 as the next product release and open PR 1: “Research contracts & metric dictionary.”**

That PR should provide the exact issuer/instrument identification strategy, filing accession/publication metadata fields, canonical metric glossary, fiscal/FX rules, schema migration and three realistic validation examples—**before** a broad ingestion connector or interface is added.

Work on the first local input-to-dossier vertical slice should start as soon as those contracts are reviewed, with an opt-in SEC adapter added behind the same interfaces. The single most important deliverable is **one real-company, reproducible, source-backed research dossier that a new contributor can generate and inspect**.

---

*This roadmap is community-facing product planning, not individualized investment advice or a promised implementation schedule. Public technical references were checked on 2026-10-27. Future provider use must be revalidated at implementation time.*
