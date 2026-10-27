# InvestIQ Engineering Blueprint

> **Status:** Engineering standard, version 2.0 — AI-first strategy alignment · **Date:** 2026-10-27  
> **Applies to:** current v0.2 source release candidate maintenance and future v0.3+ product development.  
> **Architecture:** [Connected research](../architecture/overview.md), [ADR 0003](../decisions/0003-connected-data-and-research-history.md), [Proposed AI-first roadmap v3.0](../product/product-roadmap.md), [ADR 0009](../decisions/0009-ai-first-product-pivot.md), and [v0.3 PRD](../product/ai-research-experience.md).  
> **Intent:** an **accessible, AI-coordinated investment research workflow** while preserving deterministic financial integrity, licensed data, privacy, maintainability and demonstrable user value **without speculative infrastructure**.

The [v0.1.1 engineering alignment audit](baseline-audit-v0.1.1.md) records the codebase's verified starting point, identified financial-correctness hardening and pre-v0.2 entry criteria.

## 1. Engineering decision and enforcement

InvestIQ retains a **small modular financial core and ports/adapters only at actual trust/I-O boundaries**. The next engineering outcome is a **supported, nontechnical investment question → sourced answer → strongest challenge → explicit decision** journey. Measure task completion and source quality before expanding backend breadth. Preserve backward-compatible v0.2 CLI behavior.

- **MUST** means an applicable release-blocking rule, unless a reviewer approves an explicitly documented exception and bounded remediation.
- **SHOULD** means the default, with alternatives explained in the PR.
- **CONDITIONAL** means the standard becomes mandatory only when the corresponding feature exists (for instance, browser tests when there is a frontend).
- **Existing CI gate** means a check currently executed. **Planned gate** means a proposal; this document alone does not switch it on.

### Current implementation and historical audit

The [v0.1.1 alignment audit](baseline-audit-v0.1.1.md) is a historical baseline. **Current v0.2.0 source release candidate** contains provider-neutral market/issuer contracts; opt-in SEC annual Companyfacts and Twelve Data BYOK quote access; conservative connected analysis; freshness and rights handling; explicit private, rights-aware snapshot/replay; and synthetic end-to-end CLI acceptance. Existing CI includes Ruff, pytest, package build and installed CLI smoke. Automated fixtures are **not proof** of live market/provider entitlement or public release authorization.

**Not implemented:** AI/LLM orchestrator, runnable agent, integrated user chat/browser UI, supported company search, investor preferences/watchlists, monitoring, model factuality evaluation runner, hosted secure multiuser service, verified universal real-time feeds, or measured user retention. The five model-neutral SKILL.md files are portable instructions only.

**v0.3 target:** a bounded tool-using AI research experience that visibly sources claims, delegates arithmetic to deterministic core functions, provides a testable bear case, supports scenario follow-ups and gives a nontechnical investor a usable interface. A standalone web UI and assistant-native integration are competing distribution hypotheses; assess rights, costs, security and user preference before adopting either permanently.

## 2. Architecture and boundaries

**Proposed v0.3 runtime (not shipped):**

1. **Question/task UI:** supported company lookup, investment question, explicit ambiguous security/venue choice and consent.
2. **Research orchestration:** one bounded model-independent coordinator with typed, allowlisted source/identity/analysis tools, time/step/token budgets, cancellation and meaningful partial failures.
3. **Trusted financial core:** existing provider-normalized, entitlement-aware evidence and deterministic valuation/thesis functions. Domain logic never imports model/UI/cloud/provider SDKs or performs network calls at import.
4. **Evidence-linked answer:** claims separated as sourced fact, consensus estimate, calculated result, AI inference, investor assumption or explicit gap; financial citation ID **and semantic fidelity** evaluated.
5. **User-controlled decision:** optional, affirmatively approved private research snapshot using only lawful retained inputs, never implicit save per question or quote refresh.
6. **Future continuity (v0.4 planned):** opt-in investor context, watchlists and time-correct material-change checks, not background collection by default.

**Boundaries:** presentation invokes typed application use cases, not financial formulas in browser code. AI calls only narrow tool ports; source adapters enforce legal scope and freshness. Prohibit invented current quotes, unauthorized retention/egress, cross-user leaks, arbitrary model shell/network calls and trading execution. No generic API → service → repository → model scaffold, multi-agent platform, vector store, queue or microservices without validated demand.

**Research concepts:** v0.2 supplies a constrained *transient current view* and explicit immutable *saved decision*. Its historical quotes may be excluded when provider rights are unknown. v0.3 adds *AI research runs* with source/tool traces and ephemeral context by default. v0.4 may add *investor context* only with explicit retention and correction/deletion controls.

**Framework and distribution:** use thin prototypes to compare a lightweight standalone UI and an assistant-native tool/skill interface. Choose browser framework, identity service and hosted boundaries through an ADR **after** confirming usability, financial-data display terms, provider cost and security needs.

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
| AI model/tool evaluation | Semantic source-to-claim support, arithmetic delegation, chronology/currency, tool permission, prompt injection, missing data, cost/latency | **Mandatory v0.3 AI release gate** once implemented; not enforced in v0.2 CI |

Tests must be deterministic in normal CI: synthetic or suitably licensed frozen fixtures, fake clocks, fake/recorded provider responses, no dependency on an exchange being open or a market quote having a particular live value. Do not put real provider secrets in standard GitHub Actions.

### Test design

For critical domain changes include positive cases and negative **plausibility failures**: quarter mistaken for TTM, restated result inserted into an older as-of view, split-adjusted price mixed with unadjusted EPS, late-known filing, false quote freshness, cash-flow gap treated as zero, cross-company identity mismatch and forbidden provider fallback.

Document the source of expected numerical results, not just that results have the right type. Add invariant/property tests for deep arithmetic where useful.

Coverage reports SHOULD be added early in v0.2 to expose risk gaps per module. Do not set blanket 100% coverage. Apply more rigorous branch review for valuation, historical availability, rights and data integrity.

### Current CI vs planned CI

**Current enforced:** Ruff lint, pytest, distribution build and installed-wheel CLI smoke.

**Progressive quality adoption:** formatter, one static type checker (mypy **or** pyright), coverage visibility and provider contract checks as appropriate. For v0.3, establish model/tool evaluation and browser/task-acceptance checks **before** describing them as CI release gates. Add dependency/secret/license scans with external packages, keys or hosted surfaces. Tests must be added to actual CI before being described as gates.

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

## 8. AI-first orchestration and release evaluations

AI execution is a **planned product capability**, not merely readiness. Reuse the five portable skills as procedures but do not claim that a research agent exists until an orchestrator is implemented and evaluated.

| Area | Mandatory implementation standard for v0.3 |
| --- | --- |
| Question-to-tools | Typed ResearchTask, resolved issuer/venue, bounded allowlisted calls, explicit partial/errors, cost/step/time limits and cancellation |
| Financial grounding | Sources and deterministic domain math remain authoritative; reject unsupported calculations, currency/share-class joins, timestamps and data-rights violations |
| Answer contract | Separate observed fact, provider estimate, calculation, AI interpretation, user assumption and missing evidence; cite material claims and expose a falsifiable bear case |
| Evidence verification | Source existence and claim-to-source semantic support **both** tested; fabricated references or plausible but unsourced numbers are failures |
| Model independence | Model-specific API adapters outside core, prompt/model/tool/schema versions and repeatable regression fixtures |
| Tool privilege | No arbitrary fetching, shell execution, file writes, trade placement, silent snapshot saves or provider-entitlement changes from model output |
| Privacy | Minimized prompt context, consent for external processing and private persistence, redact transcripts/logs, isolate hosted users, explicit export/deletion |
| Security | Treat SEC/filings/news/web/model text as untrusted; malicious document instructions may never override tool policy |
| Failure UX | Clear uncertainty, partial result, timeouts, stale/restricted sources, provider/model failures and instructions to retry/resolve rather than fabricated completion |

**Evaluation harness required before v0.3 product release:** versioned synthetic/legally frozen golden cases and expert review for missing EPS, fiscal revision, FX/share-basis mismatch, stale/EOD mislabeled live, ambiguous ticker, post-cutoff filing, incompatible peer comparison, fake citations, contradictory bull/bear evidence, malicious financial document, retention-denied quote, token-cost loops and user-data leakage.

Enforce tool schema and numerical-domain regression in automated tests; evaluate source/claim *semantic* faithfulness and grounded qualitative findings with expert-labelled cases plus manual review. Record observed validity, material error rates, coverage, latency/model and provider costs. Establish thresholds from a baseline, never invent success results or declare "AI verified" from structural checks. Block launch on critical financial misinformation, license breach, unauthorized data persistence or prompt-injection escape.

Do not implement complex autonomous multi-agent architecture, RAG database, vector memory or unbounded background jobs simply because the roadmap is AI-first.

## 9. User experience and frontend acceptance (v0.3)

**A usable interface is now a v0.3 deliverable.** A CLI and JSON export do not satisfy a nontechnical investor. A small standalone UI or assistant-native integration may satisfy this, based on [comparative validation](../product/validation-plan.md).

**Hero task:** Ask a supported investment question → select exact instrument when ambiguous → watch bounded research status → read concise source-grounded business/financial/valuation analysis → inspect strongest bear case and data gaps → drill down to evidence → edit permitted scenario assumptions → explicitly approve any save/export.

**Critical UX requirements:**
- No mandatory CIK/MIC, shell commands, developer API key or JSON schema for the supported consumer experience; if lawfully accessible provider data cannot support this, do not release/market it as consumer-ready.
- Show quote currency, venue, price kind, provider, market timestamp, real-time/delayed/EOD/unknown and stale status. Financial values carry fiscal period, source and method.
- Separate observation, third-party estimate, calculation, model inference and user assumption. Render unavailable as missing, **never as zero**. Forecast/scenario results are conditional, not advertised alpha.
- Inline source inspection with claim-level context; prominent specific counter-thesis and unsupported-data questions; comprehensible summary before financial detail.
- Loading, cancellation, partial output, unsupported company, ticker ambiguity, closed market, rate-limit, model failure, citation failure, declined provider rights and unsafe input recovery.
- Responsive/accessible semantic UI with keyboard and screen-reader operation, non-color status indicators, understandable language and accuracy-preserving number formatting.
- Explicit privacy consent for model/provider calls and personal storage; users can inspect and withdraw stored research according to declared retention rules.
- Browser components, end-to-end usability task tests and accessibility checks must be implemented **if standalone UI is selected**, before release. Assistant-hosted channels must meet comparable evidence, permission and usability standards.

**v0.4 (not v0.3) return-session outcome:** stored opt-in thesis → supported changed evidence → precise source/assumption deltas → user-approved thesis revision. No silent rewriting from refresh.

Do not prebuild a complex frontend framework/design system before validating the task. Select framework and hosted auth boundaries by ADR when the operating model is known.

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
| AI execution (v0.3) | Source-claim semantic checks, tool privileges, prompt injection, versioned evaluations and bounded latency/cost |
| Release/operations | Artifacts, versions, CI, migrations, cost and rollback where applicable |

**Must-pass checklist for each applicable PR:**
- [ ] Outcome and user value stated; no unrelated scaffolding
- [ ] Financial/domain semantics and public contracts explicit
- [ ] Correct dependency direction and vendor isolation
- [ ] Deterministic tests plus material negative edge cases, or justified docs-only change
- [ ] Existing Ruff, pytest, build, installed-wheel smoke checks pass
- [ ] New feature-specific gates pass **when implemented**; v0.3 AI/UI requires semantic/financial/tool/UX evaluations
- [ ] Real-investor usability and differentiation against LLM/incumbent alternatives are assessed before broad feature expansion
- [ ] Source timestamps, freshness and entitlements truthful where relevant
- [ ] No secrets, private holdings or nonredistributable provider data
- [ ] Documentation, migration and release risks updated
- [ ] No unresolved material review findings; exceptions recorded and approved

## 12. Engineering release sequencing — user outcomes before scaffolding

| Stage | Outcome / gates | Do not do |
| --- | --- | --- |
| **v0.2 source baseline** | Preserve connected CLI, source rights and replay; independently verify live provider entitlement before publication claims | Claim shipped LLM agent or consumer GUI |
| **v0.3 thin vertical slice** | One usable, supported research-question experience with appropriate provider rights, onboarding and explicit uncertainty | Build large SaaS/auth/cache system before consumer flow |
| **v0.3 AI research** | Bounded model tools, evidence-linked research/challenge, deterministic valuation and failure control | Free-form LLM numeric facts, uncontrolled agent stack |
| **v0.3 acceptance** | Evaluated model semantics and tool safety, browser/assistant UX, manual licensed-provider review, measured benchmark with real investors | Declare PMF from a demo or synthetic CI |
| **v0.4 conditional** | Opt-in memory, structured thesis deltas and lawfully scheduled monitoring | Implicit context capture and always-on worker by default |
| **v0.5+ conditional** | Proven discovery/portfolio/quant value and economic/legal safety | Expand broad analytics with no return-use validation |

Use outcome-based PRs and [draft-to-ready CI policy](ci-efficiency.md). Keep v0.2 documentation as truthful implementation history, not the current next-action list.

**Stop-and-correct signals:** false live/delay labels, licensed-data leakage, fabricated facts, replay that silently uses current prices, cross-instrument valuation error, entitlement bleed, private secrets committed, or serious unaddressed financial/security review findings.

**Engineering decision:** Preserve the v0.2 source foundation. Subject to product approval, implement the **v0.3 AI Research Experience** as a bounded, testable user-facing vertical slice with strong data-rights, factuality, security and usability gates.
