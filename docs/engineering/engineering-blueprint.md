# InvestIQ Engineering Blueprint

> **Status:** Engineering standard, version 1.0 · **Date:** 2026-10-27  
> **Applies to:** future production changes and incremental maintenance of existing v0.1.1 code.  
> **Architecture:** [Connected research](../architecture/overview.md), [ADR 0003](../decisions/0003-connected-data-and-research-history.md), [Product roadmap](../product/product-roadmap.md).  
> **Intent:** financial correctness, transparency, maintainability, security, thoughtful UX, and AI readiness **without unnecessary infrastructure**.

## 1. Engineering decision and enforcement

InvestIQ follows a **small modular Python monolith with ports and adapters at actual external boundaries**. We invest in good engineering practices **now**, while introducing new infrastructure only after an actual connected-research workflow needs it.

- **MUST** means an applicable release-blocking rule, unless a reviewer approves an explicitly documented exception and bounded remediation.
- **SHOULD** means the default, with alternatives explained in the PR.
- **CONDITIONAL** means the standard becomes mandatory only when the corresponding feature exists (for instance, browser tests when there is a frontend).
- **Existing CI gate** means a check currently executed. **Planned gate** means a proposal; this document alone does not switch it on.

### Verified v0.1.1 baseline

The existing Python package provides evidence, valuation, research, thesis, synthetic workflow and CLI modules. Ruff lint, pytest, wheel/sdist build and installed CLI smoke checks are in GitHub Actions. Five model-neutral research skills have instructions and structural evidence contracts. This is a useful starting point.

Not currently implemented: market-price providers, provider contract tests, live/freshness service, hosted API, cloud or persistent application store, web frontend, AI factuality evaluation runner, and a configured static type-checking or automated security-scanning gate. **Do not claim they already exist.** Their absence is not a v0.1.1 regression.

## 2. Architecture and boundaries

The target dependencies are:

    CLI / future Web UI / future API / optional AI tools
                        |
                Application use cases
                   /           \
                  v             v
          Pure domain core   Abstract ports
          evidence, quotes   quotes, filings
          valuation, thesis  cache, storage
                                   ^
                                   |
                             External adapters
                       HTTP providers / persistence

The financial **domain** never imports vendor SDKs, HTTP clients, database models, cloud libraries, UI frameworks or model providers. Application use cases orchestrate core domain and injected ports. Providers normalize external data to our contracts; interfaces render or transmit data without reimplementing financial formulas.

**Create boundaries only when they do work.** Keep cohesive calculation functions in their existing modules. Extract application use cases when fetching, normalization, scenario calculation and/or saving must be coordinated. Define a port for replaceable external I/O, testability or entitlement enforcement. Do not mechanically introduce an API → service → repository → model chain or create directories containing only placeholders.

**Target naming:** descriptive snake_case modules/functions/variables, PascalCase domain types, explicit business terms and consistently named input/output contracts. No permanent file names like phase_2_final, old_auth_mapping or general-purpose dumping-ground utils. Avoid renaming stable existing symbols solely for cosmetic consistency; public compatibility matters.

### Distinct research concepts

- **CurrentResearchView (planned):** source-entitled market data with source timestamp, retrieval time, market session, actual real-time/delayed/EOD/unknown status and deterministic calculations. It may change on refresh.
- **ResearchSnapshot (planned):** deliberate, immutable user-approved research record with method version, assumptions, selected licensed/replayable input manifest, source references and linked thesis history. It never changes merely because another market tick arrives.
- **ResearchAssumption (exists):** investigator hypothesis, separate from sourced observation or provider consensus.
- **FinancialObservation (exists):** source-backed, date/units-aware evidence, not a statement that the provider was necessarily correct.
- **ValuationScenario (exists):** conditional arithmetic, not an estimated probability distribution or personalized instruction to trade.

**Current data** comes from a suitably entitled provider and carries freshness. **Saved decisions** come from versioned, lawful retained evidence and must not silently call today's feed during historical replay. Source rights may limit exact replay; those limits are explicitly disclosed.

## 3. Financial and data correctness — highest priority

Correct Python code can produce financially misleading conclusions. All material changes to evidence, market data, valuation or thesis must address:

| Area | Required invariant |
| --- | --- |
| Security identity | Issuer/reporting entity distinct from ticker, venue/MIC, share class and currency; historical symbol mapping where known |
| Precision | Source monetary observations use exact finite Decimal and declared units; no silent float-to-reported-money conversion |
| Fiscal data | Fiscal period and stock-vs-flow, reported vs derived, statement coverage, adjustments, filing identity and revision lineage |
| Dates | Economic/event time, public availability, retrieved/received time and recorded time are independent; no invented intraday publication time |
| Price | Quote kind, event timestamp, exchange session, currency, adjusted basis, provider and actual entitlement/delay or unknown |
| Comparability | Reject or flag inconsistent currencies, split basis, period duration, share class, issuer identity and units |
| Missing data | Missing is NOT zero; fail or label unknown rather than fabricating estimates |
| Historical replay | Correct point-in-time source vintages; never substitute revised today's fundamentals into an old thesis |
| Scenarios | Inapplicable P/E for nonpositive/meaningless EPS, units and limitations disclosed; no unconditional return promises |
| Licenses | Vendor permission to access, cache, retain and redistribute is separate from the public software license |

Each consequential financial code change **MUST** include at least one correctly worked positive example and negative or boundary cases that catch incorrect-but-plausible outputs.

Financial validation and prose validation are separate: a structurally valid citation cannot prove a model's narrative is faithful to its source.

## 4. Python/backend coding and organization standards

### Apply immediately to changed/new code

1. Public APIs receive explicit input/return type annotations. Internal interfaces use types where they prevent invalid states; avoid unchecked Any beyond serialization boundaries.
2. Favor frozen typed value objects and enums for domain concepts with stable invariants. Use Protocol interfaces where there is a meaningful replacement boundary, not everywhere.
3. Use Decimal and source currency/unit semantics for authoritative monetary evidence. Existing float scenario math remains acceptable when explicitly approximate and carefully tested.
4. Require timezone-aware instants. Store market session/calendar semantics separately from UTC conversion. Do not infer quote timeliness from the time a response was received.
5. Keep domain logic deterministic, with no network, filesystem, vendor credential lookup or model invocation at import time. Inject I/O and clocks when necessary.
6. Validate on entry to the domain. Categorize errors such as unsupported input, missing source, ambiguous identity, invalid unit, stale data, no entitlement and transient provider outage.
7. Fail closed on data rights, identity ambiguity, or unsupported source fallback. Never turn timeout/429 or denied feed into a plausible synthetic price.
8. All external calls have bounded timeouts/retries, rate-limit handling, cancellation strategy and safe logging; do not infinitely retry permanent access-denied errors.
9. Use versioned JSON/wire schemas with exact decimals, offsets, migration rules and round-trip tests. Document breaking public changes instead of silently changing persisted structures.
10. Introduce dependencies only after evaluating license, security, maintenance, install weight, usage and cross-platform impact.

### Conditional backend/API rules

If a real HTTP API becomes necessary: keep request handlers thin and use existing application/domain logic. Design typed request, success, partial and error contracts, status/error taxonomy, idempotency for saves, bounded pagination, reasonable deadlines and correlation IDs without leaking secrets.

If multiple users share a service, validate authentication, authorization, tenant isolation, provider license isolation, secure secret storage, request throttling and data deletion/retention **before** serving the public. Do not add a fake RBAC scaffold to a single-user Python library.

**Illustrative layout, not a task to add empty folders:**

    src/investiq_core/
      evidence.py, valuation.py, research.py, thesis.py    [existing]
      market.py, instruments.py                            [when needed]
      application/                                          [use cases, when needed]
      adapters/                                             [real provider/cache/storage IO]
      cli.py                                                [existing thin interface]
    skills/                                                 [existing model-neutral skills]
    tests/                                                  [unit, contract, integration]
    docs/engineering/                                       [this blueprint]

## 5. Testing standards and quality gates

**Strong domain tests outrank a high vanity coverage number.** Each high-risk capability should be covered across several levels.

| Level | Purpose / required scenarios | When |
| --- | --- | --- |
| Domain unit tests | Numeric edge cases, currency, units, period comparisons, hashes, serialization, public/recorded time, immutability | **Now** |
| Provider contract tests | Uniform quote/fundamental mapping, 401/403/429, timeout, stale fallback, wrong instrument/currency, revisions | With first provider |
| Application integration tests | Fetch → normalize → compute → refresh; old saved thesis unchanged; offline replay with network disabled | With v0.2 use cases |
| Installation/release smoke | Wheel/sdist, CLI, source-link output, migration and replay | Every applicable release |
| Browser/components/accessibility | User journey, keyboard/screen-reader, responsive and error-state tests | When frontend exists |
| Model evaluation | Factuality, numeric fidelity, citations, prompt injection, missing/conflicting evidence | When AI output is shipped |

Tests must be deterministic in normal CI: synthetic or suitably licensed frozen fixtures, fake clocks, fake/recorded provider responses, no dependency on an exchange being open or a market quote having a particular live value. Do not put real provider secrets in standard GitHub Actions.

### Test design

For critical domain changes include positive cases and negative **plausibility failures**: quarter mistaken for TTM, restated result inserted into an older as-of view, split-adjusted price mixed with unadjusted EPS, late-known filing, false quote freshness, cash-flow gap treated as zero, cross-company identity mismatch and forbidden provider fallback.

Document the source of expected numerical results, not just that results have the right type. Add invariant/property tests for deep arithmetic where useful.

Coverage reports SHOULD be added early in v0.2 to expose risk gaps per module. Do not set blanket 100% coverage. Apply more rigorous branch review for valuation, historical availability, rights and data integrity.

### Current CI vs planned CI

**Current enforced:** Ruff lint, pytest, distribution build and installed-wheel CLI smoke.

**Planned early v0.2:** formatter gate (after a one-time coherent formatting baseline), one static type checker (mypy **or** pyright, not both without a need), coverage visibility and provider contract tests. Add dependency/secret/license scans with external packages, keys or hosted surfaces. Tests must be added to actual CI before being described as gates.

Do not suddenly fail an entire old codebase on a strict new checker without an approved baseline/migration plan. Prioritize changed code and high-risk types; no blanket ignores. Resolve review findings before merge instead of suppressing them to pass CI.

## 6. Git workflow, documentation and release discipline

**PR scope = one demonstrable outcome**, including tests, fixtures and docs; not one PR for each helper. Prefer cohesive pushes over triggering expensive CI for every trivial intermediate commit. Existing concurrency cancellation should be retained. Measure the actual CI bottleneck before parallelizing tests or adding a large matrix.

Every production PR needs:
- user or developer outcome and acceptance criteria;
- changed contracts and architectural impact;
- meaningful test evidence including material failure paths;
- financial semantics, timestamps, source, license and security impact;
- documentation, migration and release compatibility changes;
- green applicable checks and resolved substantive review findings.

Use ADRs for durable, hard-to-reverse choices (provider contract, snapshot retention, public API semantics, UI/backend framework, auth, cloud shared cache). A minor refactor does not require an ADR.

Release artifacts must be built and smoke-tested from the reviewed source; do not rewrite tags after release. Version the Python distribution and persisted research wire schemas independently. Describe deprecations, migrations and rollback/restore when a stored format or public API changes.

The public repository MUST NOT contain real private positions, provider API keys, personal secrets, paid vendor datasets or third-party research outside permission.

## 7. Security and external-data threat model

Threats include leaked provider credentials, malicious financial document text, unsupported vendor data redistribution, source URL abuse, symbol confusion, wrong entitlement in a shared cache, corrupted input manifests, untrusted AI instructions and private research data leakage.

**Applicable controls:**
- Credentials in private environment/config/secret service, never Git or public logs. Redact errors and sensitive headers; use secret scanning and dependency review as integration surface grows.
- Network adapters enforce source terms, fair-access/rate limits, request deadlines, redirect restrictions and bounded payload parsing. If hosted fetch accepts user URLs, explicitly defend against SSRF.
- Treat filings, XBRL, quotes, news, web search and model text as untrusted input. Never execute commands embedded in retrieved material.
- Enforce provider/plan entitlement scope on caches. A premium cached quote may not flow to a caller without reuse rights.
- Preserve backups/migration and private storage boundaries for saved theses. Hosted user data requires retention/deletion policy, encryption where appropriate and audited access.
- Distinguish no-data vs unauthorized vs out-of-date in errors; don't silently coerce to stale “live” content.
- Report vulnerabilities privately per [SECURITY.md](../../SECURITY.md).

**Proportionality:** do not build auth/tenant infrastructure for a small CLI. Full authorization and hosted security controls become mandatory at the real shared-user boundary.

## 8. AI readiness and evaluations

InvestIQ already has five portable research skills and a shared ResearchReport structure. AI should **interpret attributed evidence**, not fabricate market facts or perform the authoritative arithmetic.

| Capability | Standard |
| --- | --- |
| Data in | Versioned observations with venue, source, units, time cutoff, entitlement and assumptions |
| Research out | Typed finding kind: reported fact, estimate, assumption, inference or explicit gap; traceable citation IDs |
| Arithmetic | Deterministic InvestIQ domain functions; models explain scenarios but do not supply unchecked returns |
| Trust | Source-ID existence is only structural validation; independently evaluate semantic source faithfulness |
| Model independence | Skills and domain logic cannot depend on one LLM provider; optional adapters own the model calls |
| Tool privileges | Narrow fetch, analyze, export and deliberate save tools; no hidden trade execution or entitlement changes |
| Privacy/cost | Explicit provider consent, redacted transcripts, model/token budget and no unsolicited private research upload |
| Prompt injection | Financial text is data, never instructions to change policy, execute shell, steal secrets or write thesis history |

### Evaluation protocol, not a live gate yet

Build legally reproducible golden cases: missing EPS, unsupported CAGR, contradictory restatements, dates known only after a historical cutoff, wrong currency or share class, stale EOD quote labeled live, ungrounded market share claim, malicious filing instructing the agent to bypass controls, and user/tenant entitlement mismatch.

Measure **schema validity, numeric fidelity, source/citation validity, semantic evidence faithfulness, missing-data behavior, prompt-injection resistance and model cost/latency**. Track prompt/skill/model version and frozen inputs. Use expert review for semantic conclusions. No absolute “AI verified” badge from source-ID checks alone.

These become release gates **only when a specific AI-powered feature is introduced and its evaluation runner is implemented**. Never delay deterministic research features for a nonexistent AI agent suite. Do not build an autonomous multi-agent framework, vector search, RAG database or model gateway without tested user demand.

## 9. Frontend, product design and UI/UX

v0.1.1 has no web frontend. **Design the experience now; pick the stack after validating the workflow.** Do not scaffold a Next.js app or adopt a large design system in the Blueprint PR.

Core journey:

    Find supported company → Inspect source/freshness → Analyze
                    → Challenge assumptions → Explicitly save/replay thesis

**Frontend and report UX rules, applicable when exposed:**
- Quote, currency, venue, price kind, provider, last market event, session and real-time/delayed/EOD/unknown status must be visible near the price. Closed-market and stale data must not masquerade as “live now”.
- Every important figure has source, reporting period and calculation/assumption provenance. Unknown, stale and unavailable must not look like zero.
- Clearly distinguish **Current View** from **Saved Thesis as of [time]**. Refresh current calculations but never silently edit saved research.
- Show what a bear/base/bull scenario assumes, how changing inputs affects calculated outcomes and what the model omits. No fake predictive certainty or buy/sell pressure.
- Design success and error states: no coverage, ambiguous ticker, unsupported venue, delayed quote, closed market, missing financials, rate-limit response, permission denied, offline replay failure and provider outage.
- Accessible semantic controls, keyboard operation, readable contrast, non-color status communication, responsive tables, understandable terminology and measured financial precision.
- User privacy is visible: report export, external API/AI call and save actions are deliberate and clearly described.

For a future frontend, require shared design tokens, components that present typed view models, API contract tests, accessibility checks and task-based usability testing. Framework selection (React, Next.js, otherwise) gets an ADR after user research and hosting requirements are clearer. Markdown/HTML report export may satisfy early users better than a server-rendered SPA.

## 10. Reliability, observability, optimization and cost

**Measure before optimizing.** Accuracy and licensing outrank shaving milliseconds off a wrong answer.

Plan limited measurements for connected v0.2: source request duration/errors, 429 retries, cache age/hit ratio, provider freshness, normalization time, valuation time and snapshot replay success. Do not add default user analytics or log confidential holdings. Prefer opt-in instrumentation or local diagnostics for public OSS.

Quote TTL and validity must be provider-, plan-, market-session- and entitlement-aware; a cache is an optimization, **not** a market data source of truth. Cache keys reflect source/provider, instrument, data/adjustment kind, session/currency and entitlements. Shared cloud cache only after demonstrated scale, measured cost and legal authorization.

For a hosted API later, define realistic budgets/SLOs from observed representative provider behavior. Circuit breaking, backpressure, stampede mitigation, bounded request size, monitored cost and secure access become mandatory with actual hosted traffic. Do not declare universal sub-second live-feed SLAs for third-party sources.

CI optimization is also evidence-driven. Preserve cancellation of superseded runs, avoid expensive duplicate jobs, and parallelize only when it reduces observed critical-path time without losing coverage.

## 11. Review ownership and practical release gate

Use reviewer *hats* rather than creating an enterprise review board.

| Review perspective | Focus |
| --- | --- |
| Financial/domain | Formula correctness, units, periods, FX, source timing and plausible wrong values |
| Architecture | Dependencies, ports only where useful, compatibility and lack of speculative scaffolding |
| Data/provider | Provenance, share class, session, license, entitlement, stale cache, revision handling |
| Security/privacy | Secrets, malicious external input, authorized reuse and private snapshots |
| Test/quality | Negative paths, deterministic fixtures, replay, meaningful assertions and gates |
| Product/UX | User journey, source/freshness visibility, missing-data messaging and accessibility |
| AI readiness | Grounding, prompt injection, tool scopes, versioned model evaluations when applicable |
| Release/operations | Artifacts, versions, CI, migrations, cost and rollback where applicable |

**Must-pass checklist for each applicable PR:**
- [ ] Outcome and user value stated; no unrelated scaffolding
- [ ] Financial/domain semantics and public contracts explicit
- [ ] Correct dependency direction and vendor isolation
- [ ] Deterministic tests plus material negative edge cases, or justified docs-only change
- [ ] Existing Ruff, pytest, build, installed-wheel smoke checks pass
- [ ] New capability-specific checks pass **when they actually exist**
- [ ] Source timestamps, freshness and entitlements truthful where relevant
- [ ] No secrets, private holdings or nonredistributable provider data
- [ ] Documentation, migration and release risks updated
- [ ] No unresolved material review findings; exceptions recorded and approved

## 12. Adoption roadmap — standards without premature infrastructure

| Stage | Action | Non-goals |
| --- | --- | --- |
| **Now — Blueprint PR** | This document, contributor and PR-template alignment; preserve existing CI and code | No empty framework folders, frontend, database, agent stack or global refactor |
| **v0.2 PR 1** | Typed market/issuer/freshness/entitlement contracts, versioned errors, negative tests; decide one type checker | No mandatory cloud or live feed in pure domain |
| **v0.2 PR 2–3** | Provider contract fixtures, networking safeguards, bounded cache, BYOK, source licensing; introduce type/format/security checks progressively | No multi-tenant auth or streaming stack without need |
| **v0.2 PR 4–5** | Connected use cases, truthfully time-labeled valuations and explicit save/replay adapter; integration/replay tests | No implicit thesis writes per quote |
| **v0.2 acceptance** | At least one lawfully connected issuer/price source, failure-mode testing, artifact install, user walkthrough and complete source documentation | No universal real-time/global data claim |
| **When UX/hosted demand appears** | Validate design, choose stack/ADR, browser/API/security/load checks based on actual surface | No premature SaaS infrastructure |

**Stop-and-correct signals:** false live/delay labels, licensed-data leakage, fabricated facts, replay that silently uses current prices, cross-instrument valuation error, entitlement bleed, private secrets committed, or serious unaddressed financial/security review findings.

**Engineering decision:** Implement **v0.2 PR 1 — Provider-neutral market-data contracts and source/entitlement semantics** after adopting this blueprint. Engineering rigor is a constraint on how to build the next working capability, not a reason to postpone it indefinitely.
