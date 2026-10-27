# InvestIQ v0.3 — Personal AI Research Desk PRD

> **Status:** Proposed personal-alpha release, **not implemented** · **Date:** 2026-10-27
> **Canonical product path:** [Roadmap through v1.0](product-roadmap.md) · **Testing:** [Validation Plan](validation-plan.md).

## 1. Why v0.3 and what it is *not*

The first product release after the analytical core must let an individual investor **complete a meaningful, source-backed company research task through a simple local interface**, without repeatedly constructing prompts, editing data files or learning the underlying Python toolkit.

**v0.3 is an initial usable vertical slice**, not the whole research platform or a mass-market SaaS. Deliver one complete supported company research loop with clear source coverage, uncertainty and lawful save/replay. Later milestones add deeper financial/peer research, configurable scoring, scenario underwriting, updates, optional portfolio research and external open-source usability.

**Product hypothesis:** AI-coordinated financial research with verified evidence, repeatable computation, specific risk challenges and an accessible interface can reduce effort and errors relative to using a general-purpose LLM alone.

## 2. Persona and initial job

**Primary user:** An independent equity investor researching a listed company, checking sources and financial quality, testing valuation assumptions, evaluating the strongest contrary argument and deciding what merits further investigation.

**Representative acceptance task:** "Research a supported listed company for my selected investment horizon. Describe its business and financial condition with cited evidence; explain valuation assumptions, key risks and thesis-breaking conditions; let me inspect sources and deliberately save a dated research note."

**Coverage constraint:** Choose one company compatible with independently verified existing provider support and rights. The company, sector, theme and user portfolio are **test inputs only**, never hardcoded product requirements. Broader accounting standards and additional exchanges are separate, explicit data-coverage extensions.

## 3. First-run user journey — no developer workflow during everyday use

1. **Start InvestIQ locally:** documented OS-specific install/run action opens browser-based app; no Python coding or CLI required for normal user flow after setup. A packaged native installer is **not** required until v0.9.
2. **Choose demo or connect:** "Try synthetic example" (works without key/account, clearly fictional), or **guided one-time setup** for authorized source/model service. If provider/model key is necessary, disclose who charges for it, store safely under user control and let user inspect/revoke configuration. Do not promise free live licensed data or a ChatGPT subscription's inclusion of API credits.
3. **Search/select supported company:** plain company name/ticker with verified issuer/security/venue mapping and ambiguity prompt; CIK/MIC/currency/time semantics must be resolved behind the scenes or through understandable choice, not unexplained technical fields.
4. **Ask:** prefilled research template or natural-language question; horizon is visible and editable; explicitly show what the connected provider can actually substantiate.
5. **Research:** one bounded model-neutral tool coordinator calls existing dated/entitled data functions and deterministic valuation functions. Show progress, cancellation, errors and partial outputs.
6. **Read:** concise conclusion **without buy/sell order**, source-backed business/financial summary, eligible valuation/sensitivity, strongest falsification condition and missing/unsupported evidence. Expand panels for original sources and units, fiscal/market periods.
7. **Follow up:** ask why a number changed; adjust explicitly hypothetical assumptions; use deterministic calculations. If a requested metric lacks support, report gap rather than model-fabricated data.
8. **Save deliberately:** present exact eligible research inputs and what source licenses prohibit storing; user can approve a versioned private thesis, inspect its version, export/open/replay eligible historical inputs and discard it. No automatic portfolio position or user profile recording.

## 4. Minimum feature boundaries

| Must ship v0.3 | Explicitly deferred |
| --- | --- |
| Local single-user UI with question/search, research view, source drawer and consent/error controls | Multiuser hosted SaaS, global live markets, broker auth |
| Narrow verified company lookup and identity resolver for an approved small set; **lawfully retrievable issuer narrative evidence** (e.g., identifiable business/risk passages from annual filings) when making business/moat claims | Every issuer, IFRS/20-F global coverage, exchange streaming |
| One bounded tool-using AI coordinator, versioned prompts/tool records | Agent swarm, autonomous trade decisions, complex persistent vector memory |
| Sourced annual financial context plus eligible quote/valuation; clear missing metrics | Full quarterly/TTM FCF/ROIC history and comprehensive stock-scoring |
| Testable sector/business explanation and specific bear-case challenge | Automatic research universe ranking and dynamic screening |
| Hypothetical simple scenario controls where supported by current core | Unverified price forecasts, advanced DCF terminal models, entry-decision engines |
| Explicit user-approved lawful thesis snapshot/replay/export | Portfolio holdings, notifications, background update agents |
| Synthetic no-key demo; guided permitted provider/model setup | Required InvestIQ cloud account, hidden central API token costs |

## 5. Output contract and source reliability

Every answer must distinguish **reported fact; third-party estimate; deterministic calculation; AI interpretation; user assumption; unavailable evidence**. Material financial numbers need reference to exact provider/issuer, metric definition, fiscal time, unit/currency, original price/event timestamp and provider-declared real-time/delayed/EOD/unknown state. No silent fallback or today-labelled stale price. A hypothetical scenario is *not* a model's predicted return.

Research analysis includes:
- What products and economics drive the business; its industry and value-chain position; where its moat and competitors/partners lie. **Claims about products, customers, concentration, competitive positioning and risk must be supported by retrieved filings/qualified evidence or explicitly labeled as unverified interpretation.** The existing v0.2 numeric Companyfacts API alone is insufficient; a bounded issuer-document text source or other permitted evidence source is a required v0.3 addition.
- Latest supported financial observations and source limitations (no unsupported FCF/debt or growth data invented).
- Suitable, currently supported valuation and changes implied by explicit user hypotheses.
- Strongest bear case, **observable conditions that would weaken/strengthen the thesis**, and missing evidence that blocks conviction.
- Clear research timestamp, model/tool/method version and provenance/source details.
- No guaranteed-alpha rating, prescriptive personal trade action or fake confidence percentage.

**Safety:** untrusted filings/web text cannot override tools; model cannot fetch unauthorized URL, persist unknown-rights quote, change entitlements, read unrelated private files or run trades. Bounded time/steps/tokens/provider usage; sanitized errors and user-visible partial results.

## 6. v0.3 acceptance — by the person who needs it

**Required user outcomes**
- Complete one real, legally supported company case **from local UI without CIK, JSON, manual prompt orchestration or shell after setup**.
- Start a clearly synthetic research example with zero credentials and no false market-data representation.
- Configure authorized market/LLM provider once through guided UI when needed. Model/provider terms and expenses disclosed, with explicit consent to external processing of private text.
- Receive integrated source-linked researched answer and meaningful counter-case; drill into at least material numeric claim sources and unsupported inputs.
- Change a qualifying valuation assumption and observe deterministic recalculation with traceable input changes.
- Deliberately save/reopen eligible private thesis, with price/valuation omissions disclosed when rights forbid snapshot retention.
- Complete negative paths: ambiguous listing, no eligible quote or EPS, currency mismatch, denied entitlement, stale data, provider failure, model hallucination, prompt injection, interrupted run and private save failure.
- Run reproducible source/financial semantic evaluations and app integration/accessibility checks; independent real-provider smoke and provider-license review must be documented rather than assumed.
- Initial user compares several supported research sessions against a general-purpose LLM and existing research workflow, records errors/friction/usefulness and decides whether v0.4 is warranted.

**Not a release gate:** global fund-data completeness, broker integration, historical backtesting, full multi-factor stock ranking, portfolio management, unattended scheduled monitoring, installation by unknown external users, or unmeasured claims of superior returns.

### PR 6 opt-in private decision boundary

The local Research Desk uses the **existing** v0.2 `ThesisSnapshot`, `ResearchSnapshot`, `LocalSnapshotStore` and offline replay rather than a second research database. The investor opts in using a private startup directory and **explicitly authors and approves** each immutable revision. Stored data comprise thesis text/stage/revision rationale, risks/falsification triggers, issuer identity and optionally hypothetical growth, terminal P/E, weights and horizon. Restricted or uncertain-rights quotes, manually entered EPS/entry price, price-derived outputs, complete filings, API keys and AI interpretations are **not** retained. Offline replay therefore provides identity/history integrity but not numeric price valuations; no misleading replay claim is permitted. Local digests are tamper-evident only under an honest file owner, not externally trusted signatures, and the user must secure the folder. Release acceptance still needs independently authorized source coverage and demonstrated investor usefulness.

### PR 5 interactive evidence and scenario boundary

The first follow-up UI provides **independent, single-turn** questions with fresh external-processing consent. It can prefill a suggested follow-up from the preceding response but **does not forward earlier questions, claims, sources or generated answers** as conversation context; the user sees that distinction and can review the new question. The question list is temporary browser memory only, not a recorded thesis or a private user profile.

The first editable valuation surface uses **only manually entered hypothetical positive EPS and price in assumed USD/share**, three subjective bear/base/bull growth/multiple/weight cases, and InvestIQ's existing deterministic Python valuation core. The UI does not pretend to reconcile SEC company-wide EPS and an unknown-adjustment quote. Invalid weights, unsupported bounds and missing values must fail closed; weighted terminal outcomes and price-only annualized results must be source-method traceable. No external providers, model calls or persistence are part of this calculation. Verified valuation eligibility and approved saved research remain work for PR 6/7 and later milestones.

### PR 4 model-assisted interpretation boundary

The first model execution is an explicit, consent-gated **single-call** interpretation over public SEC 10-K excerpts and a narrow annual US-GAAP fact subset; it uses a provider-neutral model port and one fixed OpenAI Responses adapter. No free-running agents, tools, arbitrary URL fetches, external licensed quotes, persisted prompt/answer history or investment recommendations. A strict structured-response schema and deterministic citation allowlist reject unknown sources. The interface must conspicuously distinguish **source presence** from **factual entailment**—the model's unsupported interpretation remains fallible even with an allowed citation. Full source-grounding evaluation, business knowledge extraction and model/provider portability are subject to later quality gates.

### PR 3 evidence qualification checkpoint

The initial research evidence engine provides a **limited, deterministic** SEC 10-K primary-document excerpt inspection, with document URL, accession, filing date, normalized extraction offset, snippet hash and visible limitations. It is a source-retrieval step, **not** a completed factual business-analysis/section understanding capability. Document parsing may not cover all SEC layouts or issuer regimes; insufficient coverage must be displayed as a gap. AI source-to-claim grounding, robust narrative retrieval across filing styles and tested business analysis belong in the later research-orchestration/acceptance milestones. Document bodies and user-specific financial data are not to be archived or forwarded to an LLM without independent consent/terms review.

## 7. Implementation slices

| Slice | User milestone | Engineering proof |
| --- | --- | --- |
| **A — local task shell + provider onboarding** | Launch simple research interface; select supported issuer; clearly synthetic offline demo or guided lawful BYOK | OS smoke, credential privacy, issuer mapping, entitlement/errors, startup |
| **B — AI-integrated research** | One natural-language user question → attributable filing/document *and* numeric evidence, business analysis and a specific bear case | Narrow cited issuer text retrieval, typed tools, finite orchestrator, deterministic arithmetic, semantic evidence tests, prompt injection, budget/cancel |
| **C — interactive scenario + deliberate history** | Follow up, drill down, modify supported assumptions, explicitly save/export/replay | UX tests, financial method/units, immutable snapshots, lawful retention and deletion |
| **D — personal acceptance** | Initial user repeatedly completes the supported real research task and compares it with existing tools | Documented live-provider terms/coverage, performance/cost, usability gaps, unresolved risk register |

Follow GitHub Actions draft-to-ready policy, cohort PRs around outcomes and merge only reviewed green changes. A mock UX may validate early, but the v0.3 release cannot claim "connected" without an approved real source test.

## 8. From v0.3 to v1.0

v0.3 provides the local UI, AI research loop and first explicit private decision, **not the full future roadmap**. The required following increments are [v0.4 economic/peer analysis → v0.5 sector universes & explainable scoring → v0.6 valuation entry conditions → v0.7 thesis updates/monitoring → v0.8 optional portfolio context → v0.9 external OSS usability → v1.0 stable workflows](product-roadmap.md#6-roadmap-to-v10--progressive-independently-usable-releases).

## 9. Decision

The next PR should enable one new investor-visible task, not add new abstraction layers for anticipated modules. v0.3 ships only after **actual personal usefulness**, correct licensing, honest data gaps and source/model evaluations are demonstrated. No source data, historic workbook prices, personal holdings or API keys should be added to the repository.
