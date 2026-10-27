# InvestIQ — AI-First Open-Source Investment Research Platform | Roadmap to v1.0

> **Status:** Proposed planning baseline **v3.0 (product-focused revision)** · **Date:** 2026-10-27
> **Implementation:** v0.2.0 remains the declared Python package version. v0.3 PRs 1–6 implement a local research desk and PR 7 verifies a personal-alpha code path; real provider/license, model truth, user validation and public version/tag authorization remain separate unfulfilled gates.
> **Audience:** Individual self-directed investors first, followed by wider independent users and open-source developers. Initial adoption is local-first; functionality is industry-neutral and user-configurable.
> **Companions:** [v0.3 Personal Research Desk PRD](ai-research-experience.md) · [User and OSS Validation](validation-plan.md) · [Engineering Blueprint](../engineering/engineering-blueprint.md) · [Architecture](../architecture/overview.md) · [ADR 0009](../decisions/0009-ai-first-product-pivot.md).

## 1. Executive decision — what we are building

**InvestIQ is an AI-first, open-source, user-controlled investment research system** that makes repeatable investment decisions easier: explore a universe, deeply understand companies, verify market/fundamental evidence, compare economic models, evaluate price and scenarios, challenge assumptions, explicitly record conclusions and revisit them when new facts arrive.

It is **not** a stock-picking chatbot, a clone of ChatGPT, an Excel-to-dashboard conversion or an infrastructure showcase. A distinctive benefit must be demonstrated in less repetitive prompting, more reliable sourced analysis, useful methodology consistency and history-aware research.

**Development sequence:**
1. **Initial usability:** an individual investor runs a local app, researches real supported companies and verifies that the results are useful and reliable. The first usable local UI is required in v0.3, not v0.5.
2. **Deepen the complete investing workflow:** progressively deliver company/peer intelligence, defensible screening, valuation and entry-condition analysis, historical decisions and optional holdings/context. Each release must stay usable, rather than postponing value until v1.0.
3. **Open-source adopters:** make setup, coverage, provider/model configuration, privacy, docs and failure recovery intuitive for external users (alpha by v0.9; external contributions can begin earlier).
4. **v1.0:** stable, reproducible, usable end-to-end research workspace for supported securities, independent of an InvestIQ-hosted SaaS.

**Decision:** Keep the MIT-licensed deterministic Python core and existing v0.2 connected adapters/snapshots. Put AI in the **user-facing orchestration layer**, while retaining provenance/financial arithmetic/licensing in trusted components. Historical snapshots and current quotes remain distinct. Default deployment **local-first with on-demand remotely sourced financial data**, not a static local market database or mandatory hosted cloud service.

## 2. Investment research problem and product principles

**The problem:** Investment research is fragmented across financial-data tools, documents, screeners, spreadsheets, AI assistants and personal notes. Investors must repeatedly collect and verify evidence, reconcile dates and financial definitions, decide whether companies are genuinely comparable, test uncertain assumptions, explain rankings and track which conclusions changed. A generic LLM can answer individual questions but may not provide a consistent, auditable, user-controlled research-to-decision workflow.

**InvestIQ's proposed solution:** Automate the research workflow through **AI-guided discovery, research, comparison, valuation, critical challenge and monitoring**, backed by qualified source data, deterministic calculations, configurable methodologies and explicit investor control. The intended improvement in accuracy, effort and sustained usefulness must be validated rather than assumed.

**Product principles:**
- **Sector- and thesis-agnostic:** Work with any supported company, industry, investment theme, portfolio or investor methodology. Examples and internal research histories never define product functionality or default rankings. Equity analysis is the **initial supported asset class**, not a permanent architectural restriction.
- **AI executes the workflow, not just chat:** Natural-language questions and purposeful actions should trigger appropriate permitted retrieval, computation, synthesis, comparison and follow-up without repeated technical prompts or manual spreadsheet assembly.
- **Evidence before opinion:** Identify issuers/listings correctly; disclose source, market/fiscal date, currency, rights and missing data. Model prose is not a source of financial facts, and LLM mathematics is not authoritative.
- **Explainable, adaptable models:** Financial quality, business strength, valuation, risk, momentum/catalysts and uncertainty can be evaluated separately; sector-appropriate factors, investor-defined weights and horizons should be versioned and inspectable.
- **Distinguish research from decisions:** An investment scenario is not a return forecast; explain base/bear/bull assumptions and conditions that could invalidate a thesis. Never automatically place trades or rewrite a saved conclusion.
- **Current evidence, immutable decisions:** Refresh current inputs from authorized providers; preserve prior approved research only to the extent lawful and never treat a static local file as today's market data.
- **Local-first open source:** Let an individual use the software before building shared infrastructure. Preserve privacy and portability. Third-party model/data credentials or subscriptions, where needed, are distinct from InvestIQ's open-source license.
- **Progressively useful releases:** Deliver a coherent, small supported journey early and expand coverage, sophistication and external usability through verified milestones—not a large unfinished set of modules.

## 3. Intended users and deployment

| Stage | Primary user | Setup / access | Experience expectation |
| --- | --- | --- | --- |
| **v0.3–v0.6 personal alpha** | Initial self-directed investor | Local app; own authorized market-data/model credentials where required; synthetic offline mode | No CLI/CIK/manual JSON during normal research; clear provider/coverage setup, save/private local records |
| **v0.7–v0.8 repeat-use alpha** | Initial investor plus limited reviewers | Same local/self-hostable product; private data optional | Timely update/re-underwriting and portfolio/context only if explicitly enabled |
| **v0.9 external OSS beta** | Independent nontechnical investors and developers | Documented one-command/packaged install; guided setup; portable private data; reproducible samples | First real supported research task without knowing Python or assembling multiple prompts |
| **v1.0 stable OSS** | Any user within supported markets/asset classes and accepted provider requirements | Local-first, open code and documented plug-in adapters; optional self-host; cloud not required | Complete repeatable, trustworthy research lifecycle and versioned migration/compatibility |

**Portable user configuration:** No user's tickers, holdings, buy prices, preferences, theses or credentials become public fixtures, rankings or hardcoded defaults. Demonstration data are redistributable and clearly synthetic. Each installation supports its own research universe, assumptions, preferences and methods.

**Open source from now, consumer-ready later:** The repository is already public/MIT; v0.9 is **usability/beta readiness**, not the first time code is open.

## 4. Experience — user actions, not modules

A supported investor should open InvestIQ and see:
- **Ask or Research:** "Analyze this company for a multi-year horizon" — the system resolves a supported security, retrieves lawful current sources, builds financial/business/valuation evidence, shows a specific bear case and allows follow-ups.
- **Compare:** "Compare these companies and explain which are genuine peers" — identify differences in business model, economics, financial definitions and investment trade-offs.
- **Explore:** "Which companies in this industry or investment theme deserve further research?" — define the company universe, data coverage and explainable score/rank breakdown **as of** a dated data snapshot.
- **Underwrite:** "What assumptions and entry price could support my chosen hypothetical return hurdle and investment horizon?" — scenarios, reverse valuation, sensitivity and named failure conditions.
- **Revisit:** "What changed since I last assessed it?" — distinguish price, fundamentals, published guidance/estimates, corporate events, assumptions and scoring-method changes under lawful observation retention.
- **Portfolio context (opt-in):** "Are my selected investments exposed to overlapping risks? What happens in a downside scenario?" — do not merge watchlists and owned positions.

**No daily user needs to chain six SKILL.md prompts, assemble manual CIK/MIC records, run a CLI or recalculate spreadsheet formulas.** A simple natural-language task interface plus purpose-built tables/charts/controls delivers more than pure chat. The five existing skills become guided research procedures invoked by orchestrator tools; skills alone are not executing agents.

**UI minimum:** question/search, company overview, structured source/evidence panel, timeframe selector, actual-versus-assumption clarity, scenarios where supported, specific risk/counter-case and deliberate history save. As capabilities ship, expose discover, compare, watchlists, rankings, thresholds and portfolio views. Never show clickable features that do nothing.

## 5. Implementation baseline and data reality

**Already implemented (v0.2 source):** portable Python valuation/evidence/thesis contracts; five model-neutral research *instruction* skills; synthetic offline CLI; SEC annual US-GAAP facts and Twelve Data BYOK minute-candle CLOSE; venue-qualified issuer contracts; conservative quote freshness and default-denied reuse rights; dated current analysis; explicit rights-aware private snapshots/replay and CLI acceptance tests.

**Not implemented or not verified:** model execution, research coordinator, company search, graphical interface, multi-company trend/peer workflows, comprehensive FCF/ROIC/quarterly data, wide-universe research, scorecards, alerts, holdings, open-source consumer installers, secure hosted SaaS, verified provider real-time data rights, independent provider smoke and real-user evaluation.

**Coverage discipline:** The existing v0.2 implementation supports a narrow SEC annual US-GAAP path, **not** every equity issuer, accounting standard, exchange or asset class. Broaden the supported universe through explicitly tested adapters, fiscal/FX/share-basis normalization, corporate-action semantics and provider rights. The general-purpose product vision must not be confused with universal data coverage at v1.0; unsupported is an honest result.

**Market-data policy:** On-demand permitted feeds for current research. Consumer app may use BYOK when source contracts require it, but a **setup wizard** rather than manual environment variables is required for everyday use. Offline synthetic sample requires **no account or key** and is always visibly fictional. LLM adapters may require their own endpoint/key or supported local model; verify actual quality/cost before claiming turnkey free AI. A public hosted service requires separate licensing/security/business justification.

## 6. Roadmap to v1.0 — progressive, independently usable releases

Releases are **outcome milestones, not delivery dates or promises**. Every release inherits source rights, truthful data and security gates. A workflow that fails its earlier release gate blocks dependent scope.

| Version | Theme | Usable capability by that release | Exit gate |
| --- | --- | --- | --- |
| **v0.1.1 — released** | Research primitives | Run fictional evidence/thesis/reverse valuation CLI | Historical release |
| **v0.2.0 — source release candidate** | Connected analytical core | Optional manual BYOK single-company SEC/quote research and private lawful snapshot/replay | Live provider/account rights smoke + explicit public tag/release authorization outstanding |
| **v0.3 — Personal Research Desk (NEXT)** | **AI + local UX first** | Install/run local task UI, set up permitted data/model provider once, search a small supported company set, ask for a **complete source-linked company research answer**, inspect bear case, adjust eligible simple scenarios and save an allowed thesis | Initial user completes actual supported research without CLI/CIK/JSON; coherent UI/model/source/consent failure states and AI semantic/security tests |
| **v0.4 — Company & Peer Intelligence** | Business and fundamentals | Inspect company economics, financial trend/quality, margins/cash/leverage **where sourced**, material risks, and compare supported true peers or show economic mismatch | Supported peer/period/units/FX, no invented history; comparison passes representative daily research tasks |
| **v0.5 — Universe, Screens & Explainable Scores** | Discovery and research prioritization | Maintain sector/theme value-chain lists; evaluate named companies using configurable quality/valuation/growth/moat/risk/confidence factors, compare short vs long horizons and see missing data/rank sensitivity | Coverage-aware rankings, documented weights/method versions, no price-dependent score on stale/unverified price |
| **v0.6 — Underwriting & Entry Conditions** | Valuation-to-decision | Bear/base/bull, reverse valuation, implied growth, entry-threshold analysis for a **hypothetical** return hurdle, risk/assumption sensitivity and explicit thesis decision record | Correct valuation basis/horizon, no free-form LLM arithmetic, changed price never silently changes past decisions |
| **v0.7 — Research Continuity & Monitoring** | Why did my thesis change? | Approved watchlists, lawful scheduled/on-demand refresh, saved conditions, material price/fundamental/news/estimate changes if covered; see price-driven vs thesis-driven vs methodology-driven deltas | Point-in-time checks, opt-in schedules, licensed retention, meaningful alerts, no automatic thesis revision, observed repeat usefulness |
| **v0.8 — Portfolio Context & Research Workspaces** | Decision portfolio | Optional private holdings and watchlist separation, thematic concentration, risk/overlap and conditional allocation/scenario analysis, multi-currency where correctly supported; import/export personally sourced research | No defaults containing personal holdings, privacy isolation, accurate position currency/source, no brokerage orders |
| **v0.9 — External Open-Source Beta** | Others can use it | Supported OS installation, guided first-run demo/BYOK setup, discoverable UI, example research, docs, supported scope and privacy controls, error recovery and contributor extension contracts | Independent external install and task tests; stable migrations, release artifacts, security/privacy/license checks; documented failure limits |
| **v1.0 — Stable Open Research Workspace** | Dependable OSS product | A user can install, configure, explore/research/compare/underwrite/track supported equities, inspect evidence, export/replay permitted decisions, use own models/data adapters/configuration and reset/delete local profile | Defined product+engineering exit checklist in §9; evidence of repeat usage and independent external adoption |

### Work sequencing and dependencies

- **v0.3 is intentionally narrow:** one useful, real-company end-to-end personal flow, including **traceable issuer narrative evidence** as needed for business/risk claims; not broad market coverage or a comprehensive stock screener.
- **v0.4 requires validated source breadth:** trend/peer only with compatible periods, fiscal filings and sources; narrow alternatives when providers cannot support it.
- **v0.5 requires score methodology integrity:** no rankings merely because a formula can be calculated. Include confidence, missingness, scenario/sector/horizon distinctions.
- **v0.6 requires price/valuation rights and completeness:** reverse underwriting is allowed only with compatible current/ref-price and financial assumptions.
- **v0.7 requires durable dated source history to the extent lawful:** can monitor source changes without storing restricted quote bodies; do not falsely claim exact hindsight reconstruction.
- **v0.8 is opt-in and private:** holdings require stronger secret/storage/user-correction controls.
- **v0.9/v1.0 require real external usability:** publication on GitHub alone is insufficient.

Scope changes can shift features between minor releases, but **must preserve the full v1.0 capability map and release dependencies**, and record why a feature moves. Do not shortcut gates by renaming.

## 7. Detailed roadmap capabilities and method evolution

### A. AI and interaction (starts v0.3, improves every release)
- Single bounded, replaceable model coordinator with narrow **issuer filing/document passage retrieval** (for business model, concentration and risks), numerical evidence/quote retrieval, calculation, source inspection, challenge and explicit-save tools; agent run costs, failures, citations and model version visible where useful.
- Context-aware follow-ups within approved tasks; never need to restate every factor/stock/timestamp. Do not persist conversations or investor preferences without opt-in.
- Report-first UI plus purposeful comparison tables, scoring breakdowns, charts and sliders. AI **orchestrates**; the product isn't an unstructured prompt box.
- Source-to-claim semantic checks, confidence calibrated to evidence coverage (not fabricated numerical probability), prompt-injection defenses and bounded retries.
- Portfolio/notifications later only with deliberate opt-in and controlled retention.

### B. Connected financial and fundamental data (expanded when required)
- Issuer/listing mapping, supported geographic/fiscal regimes, price kind/session/time, currency and FX/adjustments; no "today" quote without a credible event time.
- Annual → quarterly/TTM where available, restatements, financial definitions, capex/FCF, ROIC/debt/share count; vendor coverage matrix by sector and instrument.
- Provider-permission-aware caching and data costs, offline sample, private lawful snapshots; do not run a server/data warehouse just to maintain static current prices.

### C. Research methodology and scoring (v0.4–v0.6)
- Extensible **industry-aware** research templates and valuation methods based on economic characteristics, business model, financial disclosure and data quality—without privileging named sectors or hardcoding a thematic universe.
- Research scores: business quality, financial trend, sustainable economics, valuation/return potential, risk resilience, catalyst/horizon and evidence coverage **separately**, plus optional explicit-weight composite.
- Every score stores source vintage, assumptions, weight/model version and peer group; calculate rank shifts due to price, fundamental and scoring-method changes distinctly.
- No default factor weights or historical investor preferences are universally objective; support auditable, editable methodologies, explicit uncertainty and validation with lawful point-in-time data when needed.

### D. User-controlled state and continuity (v0.3+)
- Historical decisions saved explicitly; position/watchlist membership, saved scenarios, choices and consent stored locally by default under user-owned data paths.
- Refresh current views without mutating decisions. Save lawful data/refs; if retention prohibited, replay only eligible inputs and visibly disclose the gap.
- Future sync/cloud deployment and automatic monitoring optional, conditioned on hosting authorization, multi-user isolation and sustainable costs.

### E. Open-source operating model (v0.3 → v1.0)
- MIT core and app; no dependency on centrally hosted InvestIQ infrastructure. Provider/model adapters open/documented; data provider contracts and model costs **separate** from MIT grant.
- Config portability, cross-platform developer/consumer install, accessible UX, security-by-default for user secrets, sample fixtures, contributor docs, CLI compatibility and migration/backup/export.
- If a new external user has no paid feeds, the app still demonstrates an **honestly labeled synthetic** workflow and clearly explains how to configure permitted connected research.

## 8. v0.3 step-by-step delivery slices (outcome PRs, not premature implementation approval)

| Step | User-visible result | Required proof |
| --- | --- | --- |
| **PR A — first-run research shell** | Simple local research entry, supported company lookup/selection and guided provider/model configuration **or transparent synthetic demo** | On Windows/Linux supported target, local startup, no CLI during normal use, credential and data-rights safeguards; interactive smoke |
| **PR B — one complete AI research task** | Bounded coordinator combines existing dated SEC/quote tools with trusted valuation, cited business/financial summary, strongest bear case and useful gaps | Model/tool contracts, semantic/source checks, numerical delegation, partial failures, prompt-injection and cost controls |
| **PR C — interactive answer and lawful decision** | Drill into sources, compare conditional scenarios, answer grounded follow-ups, explicitly create/replay/export private versioned permitted thesis | Scenario correctness, allowed history fields, no stale data or silent writes, local privacy/deletion behavior |
| **PR D — personal release acceptance** | Repeatable research for an intentionally supported small stock set; offline demo and connected happy/negative paths | Initial investor uses the daily workflow without developer instructions; measure quality, latency/cost and compare against direct LLM research |

The first PR may use mocks clearly labeled as such, but **v0.3 release requires a real, independently verified supported case** under actual provider terms. Do not add a generic browser stack or SaaS accounts before the first research journey works.

## 9. v1.0 acceptance — what "ready to be used" means

**Functional acceptance**
1. Independently install and configure on documented supported OS; run synthetic sample with no credentials, and configure lawful connected provider/model access through a comprehensible UI.
2. Run a supported company deep dive, explicit peer comparison, explainable screening/ranking, valuation/entry sensitivity and source-linked counter-thesis. No mandatory Python skills or multi-prompt recipes.
3. Save, reopen, diff and export a user-authorized thesis; see meaningful legal/data-coverage limitations and research-update events. No silent historical revision.
4. Opt into a watchlist and, if desired, private holdings/portfolio research. Never require broker connection or trading permissions.
5. Edit methodology weights, horizon, assumptions, source choices and sector definitions without changing other users' defaults. Clear method/model/source versions.

**Engineering and trust acceptance**
6. Verified issuer/venue/price/currency/time/fiscal data with zero known critical permission violations or fabricated official figures; supported-region and missing-data failures are understandable.
7. Financial unit/economic/temporal, source-to-claim semantic, prompt-injection, model regression, privacy, storage migration/replay, installer/browser accessibility and provider contractual test suites pass as applicable.
8. Versioned public APIs/data schemas, backward-compatible CLI, repeatable releases, clean source/synthetic fixtures, documented source/model/provider cost and licensing obligations, secure secrets, backup/export/delete and security disclosure process.
9. At least one structured independent external usability/adoption trial plus measured repeat-use evidence; record actual sample size and observed results before declaring the milestone complete. **Numeric thresholds should be set after a baseline**, not invented.
10. No untested promise of guaranteed investment return, all market coverage, automatic trading, licensed real-time public redistribution or institutional portfolio compliance.

**Operational readiness:** The complete product still works as an open-source local/self-hosted package with on-demand data, not a paid hosted account. Unsupported providers/regimes remain explicitly out of scope; a consistent subset is acceptable for v1.0.

## 10. Measures, validation, governance and stop rules

**Personal north-star before external beta:** number of completed, **actually useful** supported research/underwriting sessions per week, with accepted evidence and no manual data assembly. Also track first useful answer time, corrections, missing source/financial data, score/valuation confidence, research re-use and authorized data/LLM cost.

**External north-star for v0.9–1.0:** portion of new independent users who install, configure, finish one source-linked task and voluntarily return for another decision/research update.

**Compare with alternatives:** same task across current InvestIQ, a general-purpose LLM and a mature research service; do not presume superior model output without measured source fidelity, effort, retention and preference. See [validation plan](validation-plan.md).

**Stop/narrow/pivot if:** no sustained personal use; user repeatedly prefers manual LLM prompting; unreliable or unlicensable sources; significant wrong/risky outputs; cost disproportionate to value; external users cannot install/use; or no meaningful return-value after several iterations. An assistant-native integration remains a distribution option **alongside**, not a substitute for delivering a usable personal research workspace.

**Review policy:** roadmap changes require PR and a product-decision record. Product defines problems/release gates; [engineering](../engineering/engineering-blueprint.md) defines implementation. Complete v0.2 PR/ADR/release facts remain historical. This planning proposal does not authorize public tag, hosted infrastructure, private-data upload or merge.
