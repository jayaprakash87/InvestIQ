# InvestIQ v0.3 — Personal AI Research Desk PRD

> **Status:** Proposed personal-alpha release, **not implemented** · **Date:** 2026-10-27
> **Canonical product path:** [Roadmap through v1.0](product-roadmap.md) · **Prior research:** [Research Foundations](research-foundations.md) · **Testing:** [Validation Plan](validation-plan.md).

## 1. Why v0.3 and what it is *not*

The project owner has repeatedly researched AI infrastructure, semiconductors, optics, power/thermal and other equities using LLM conversations and large manually revised spreadsheets. The first InvestIQ product must **reduce the friction of that research** without hiding fundamental source/valuation errors.

**v0.3 = the first actually useful personal workspace**, not the complete product and not a mass-market SaaS. Deliver **one complete supported company research loop** and an easy local UI. Advanced multi-company screening, 194-company coverage, deep margin trends, full fundamental scoring, entry price models, monitoring and portfolio analytics have explicit later milestones (v0.4–v0.8). Do not imply those are implemented in v0.3.

**Product hypothesis:** a researched answer with trustworthy cited financial inputs, automatically orchestrated analysis and a real bear case requires fewer prompts and corrections than a generic LLM.

## 2. Persona and specific initial job

**Primary tester:** the project's creator, a self-directed investor who asks nuanced business-moat/valuation questions, checks current price/FCF/margins/debt, compares AI-infrastructure subsectors, questions rankings, revisits investment decisions and currently uses spreadsheet scenarios.

**Initial task:** "Analyze **Broadcom** as an AI infrastructure investment over a selected multi-year horizon. Explain the business and key risks, show correctly qualified sourced financial figures and current permitted price, evaluate applicable simple valuation assumptions, produce a *specific* bear case and let me explicitly save the research decision."

Broadcom is an **illustrative supported-candidate** subject, not a pre-certified issuer/feed. Verify CIK/venue/data-plan entitlements independently; if not suitable, use another well-supported SEC 10-K US-GAAP issuer. Do not promise TSMC, Schneider Electric, IFRS or 194-value-chain-name support in v0.3.

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
| Narrow verified company lookup and identity resolver for an approved small set | Every issuer, IFRS/20-F global coverage, exchange streaming |
| One bounded tool-using AI coordinator, versioned prompts/tool records | Agent swarm, autonomous trade decisions, complex persistent vector memory |
| Sourced annual financial context plus eligible quote/valuation; clear missing metrics | Full quarterly/TTM FCF/ROIC history and comprehensive stock-scoring |
| Testable sector/business explanation and specific bear-case challenge | Automatic research universe ranking and dynamic screening |
| Hypothetical simple scenario controls where supported by current core | Unverified price forecasts, advanced DCF terminal models, entry-decision engines |
| Explicit user-approved lawful thesis snapshot/replay/export | Portfolio holdings, notifications, background update agents |
| Synthetic no-key demo; guided permitted provider/model setup | Required InvestIQ cloud account, hidden central API token costs |

## 5. Output contract and source reliability

Every answer must distinguish **reported fact; third-party estimate; deterministic calculation; AI interpretation; user assumption; unavailable evidence**. Material financial numbers need reference to exact provider/issuer, metric definition, fiscal time, unit/currency, original price/event timestamp and provider-declared real-time/delayed/EOD/unknown state. No silent fallback or today-labelled stale price. A hypothetical scenario is *not* a model's predicted return.

Research analysis includes:
- What products and economics drive the business; which AI layer it occupies; where its moat and competitors/partners lie, with attributed claims where possible.
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
- Creator compares several actual supported research sessions against current ChatGPT+spreadsheet workflow, records errors/friction/usefulness and decides whether v0.4 is warranted.

**Not a release gate:** global fund-data completeness, broker integration, historical backtesting, full multi-factor stock ranking, portfolio management, unattended scheduled monitoring, installation by unknown external users, or unmeasured claims of superior returns.

## 7. Implementation slices

| Slice | User milestone | Engineering proof |
| --- | --- | --- |
| **A — local task shell + provider onboarding** | Launch simple research interface; select supported issuer; clearly synthetic offline demo or guided lawful BYOK | OS smoke, credential privacy, issuer mapping, entitlement/errors, startup |
| **B — AI-integrated research** | One natural-language user question → complete referenced evidence/finance + bear-case research | Typed tools, finite orchestrator, deterministic arithmetic, semantic evidence tests, prompt injection, budget/cancel |
| **C — interactive scenario + deliberate history** | Follow up, drill down, modify supported assumptions, explicitly save/export/replay | UX tests, financial method/units, immutable snapshots, lawful retention and deletion |
| **D — personal acceptance** | Creator repeatedly completes the supported real research task and compares it with old workflow | Documented live-provider terms/coverage, performance/cost, usability gaps, unresolved risk register |

Follow GitHub Actions draft-to-ready policy, cohort PRs around outcomes and merge only reviewed green changes. A mock UX may validate early, but the v0.3 release cannot claim "connected" without an approved real source test.

## 8. From v0.3 to v1.0

v0.3 provides the local UI, AI research loop and first explicit private decision, **not the full future roadmap**. The required following increments are [v0.4 economic/peer analysis → v0.5 sector universes & explainable scoring → v0.6 valuation entry conditions → v0.7 thesis updates/monitoring → v0.8 optional portfolio context → v0.9 external OSS usability → v1.0 stable workflows](product-roadmap.md#6-roadmap-to-v10--progressive-independently-usable-releases).

## 9. Decision

The next PR should enable one new investor-visible task, not add new abstraction layers for anticipated modules. v0.3 ships only after **actual personal usefulness**, correct licensing, honest data gaps and source/model evaluations are demonstrated. No source data, historic workbook prices, personal holdings or API keys should be added to the repository.
