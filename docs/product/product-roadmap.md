# InvestIQ — Product Strategy and Roadmap v3.0

> **Status:** Proposed AI-first planning baseline for review · **Date:** 2026-10-27
> **Supersedes:** [Product Roadmap v2.0](../decisions/0009-ai-first-product-pivot.md) for **future priorities**; it does not retroactively change the v0.2 implementation or signed release decisions.
> **Implementation baseline:** v0.2.0 **source release candidate**, not a fully validated public/hosted product. The connected CLI and synthetic acceptance exist; independent live-provider entitlement smoke, public tag and user validation remain pending.
> **Companion documents:** [AI Research Experience PRD](ai-research-experience.md) · [Product Validation Plan](validation-plan.md) · [Engineering Blueprint](../engineering/engineering-blueprint.md) · [Architecture](../architecture/overview.md).

## 1. Product decision

**Build and validate an AI-first investment decision workflow, not a feature collection or a financial-data terminal.**

InvestIQ's proposed customer-facing promise is: **"Your AI investment decision partner: discover a question, research it with evidence, challenge the thesis, preserve the decision, and see what materially changed."**

The **differentiation hypothesis**, not an established moat, is that investors value a *continuous, structured, source-linked decision process* more than individual AI-generated reports. General-purpose LLMs and incumbent research platforms already offer research, screening, AI chat, alerts and watchlists. The product must show measured superiority in **effort saved, analytical reliability, continuity and return usage**. If it cannot, we should choose a lightweight assistant/skill/MCP integration instead of building a separate application.

**Immediate product priority:** v0.3 *AI Research Experience* — an accessible conversation/task-based interface and a complete, bounded, tool-assisted workflow for a small supported company universe. **A graphical/interactive interface is a first-class release requirement, not a v0.5 afterthought.**

No more platform-first features solely to make the technical architecture comprehensive. Advance scope only when it enables a demonstrable investment-research outcome or an essential safety, data-rights or reliability gate.

## 2. Who and what job

- **Primary segment for validation:** serious, self-directed **equity investors** who revisit investment theses across weeks or months. Research fluency varies; coding and API knowledge must not be prerequisites.
- **Secondary segment:** independent researchers, educators and small investment-analysis teams (only after the primary flow is proven).
- **Developer audience:** keep the existing MIT-licensed Python library, CLI and model-agnostic skills reusable; they are a distribution/technical path, **not** proof that a consumer app should exist.
- **Explicit non-users for the first release:** high-frequency traders, broker order executors, regulated discretionary managers, quant institutions requiring licensed historical universes, and investors expecting guaranteed stock picks.

**Jobs to be done:**
1. *Investigate:* "Is this company worth researching at the current valuation?"
2. *Compare:* "Which of these companies fits my stated horizon and constraints, and why?"
3. *Challenge:* "What would falsify my thesis, and what critical information is missing?"
4. *Remember/revisit:* "What has changed since the decision I actually made?"
5. *Discover (later):* "Which evidence-supported opportunities deserve my limited attention?"

The workflow delivers **research decision support**, not personalized trade instructions or investment-adviser claims. Do not display confidence, forecasts or rankings as objective probabilities of outperformance without appropriate validation.

## 3. Why users might choose InvestIQ

| Current alternative | Good enough already | InvestIQ must *prove* incremental value |
| --- | --- | --- |
| General-purpose LLM | Fast synthesis, follow-up questioning and varied reasoning | Lower manual prompting, reliable source-to-calculation grounding, saved structured decisions and date-aware reassessment |
| Financial data/screening application | Professional financials, comparisons, watchlists and alerts | Better end-to-end analytical workflow, meaningful thesis-change interpretation and tailored evidence challenges |
| Spreadsheet / manual notebook | Flexibility and transparent assumptions | Easier updates, less clerical reconciliation, durable comparison of prior assumptions and current facts |
| Existing AI-native research tools | AI summaries, screeners, agent features and alerts | **Demonstrated** task completion, quality, explainability, continuity, usability and economics; mere feature parity is insufficient |

**Stop rule:** If independent testers do not prefer or return to the workflow, or the recurring information value is available at lower effort in an existing tool, do **not** continue investing in standalone SaaS infrastructure. Reassess a portable AI integration, narrower niche or stopping the product.

## 4. What exists today and what does not

| Capability | Actual v0.2.0 source state | Future expectation |
| --- | --- | --- |
| Math, evidence, versioning | Deterministic valuation primitives, sourced numeric contracts, thesis history and offline synthetic workflow | Reuse as the trusted financial core |
| Connected research | Opt-in BYOK SEC annual Companyfacts and Twelve Data minute-candle CLOSE with explicit mapping and unknown declared plan timeliness | Broader qualified identity resolution and research data only where rights/coverage support it |
| Data use/retention | Fail-closed entitlement metadata, optional rights-aware cache, private snapshots; quotes with unknown retention rights **excluded** from history | Retain/reconstruct only permitted values; show gaps and method versions |
| AI | Five **instruction-only**, model-neutral research skills and structural ResearchReport validation | **Not implemented:** LLM execution/orchestrator, semantic grounding evaluation, investor memory or autonomous analysis |
| Interface | Python CLI, JSON and Markdown export | **Not implemented:** consumer chat/task UI, company search, result cards, interactive scenarios or browser application |
| Continuity | Manually saved research history | **Not implemented:** permissioned watchlists, material-change monitoring, notifications or recurring agent |
| Live claims | Automated tests use synthetic responses, **not** independently validated provider accounts | Never label delayed/unknown data real-time or promise unsupported regions |

This section is authoritative for product capability communication until a subsequent release is independently verified. Keep historical v0.1/v0.2 release notes, completed ADRs and the functioning CLI as factual records.

## 5. Core AI-first experience

The user sees **one question and a small set of entry actions**: Research a company, Compare alternatives, Challenge my thesis, and What changed? (latter actions may be disabled or labeled *planned* until implemented).

**Reference end-to-end journey (v0.3):**
1. Enter a natural-language investment question or select a company through search; choose a listed security explicitly when issuer/venue/currency is ambiguous.
2. The bounded AI orchestrator creates an **inspectable research plan** and calls permitted financial-data and deterministic analytical tools; no user-entered CIK, MIC, environment variable, JSON schema or formula is required in the **supported user interface**.
3. Render a concise integrated analysis: business model, financial trend where sourced, valuation methods and eligibility, risks, strongest counterargument, and unanswered questions.
4. Each material numeric statement shows source, fiscal period, quote kind/market timestamp, currency and stale/delayed/unknown status. AI inferences are visibly different from reported facts, forecasts and user assumptions.
5. Allow follow-up questions, grounded scenario changes and source drill-down. Explain unsupported requests and restricted coverage without substituting fabricated values.
6. Ask before saving an investment thesis, changing a decision, exporting private research or enabling recurring tracking. Display what legally **can and cannot** be retained.
7. Where historical views or later monitoring exist, show precise material deltas and **why** a previously recorded condition is or is not met. Never silently revise the original thesis.

A useful **first-session** outcome is a supported investor receiving one comprehensible, challengeable, source-linked answer **without learning the underlying tooling**. A useful **return-session** outcome is understanding new evidence relative to previously approved research; this remains a later release and validation hypothesis.

See [AI Research Experience PRD](ai-research-experience.md) for v0.3 required controls, outputs, failure states and acceptance tests.

## 6. AI system responsibilities and trust boundary

**AI is the coordinator and interpreter; deterministic tools and attributed providers are the sources of financial facts/calculations.**

- **Allowed AI jobs:** disambiguate intent, compose a research plan, select authorized tools, summarize sourced evidence, explain differences, formulate a falsifiable thesis and strongest bear case, identify gaps and answer follow-ups.
- **Tool-only jobs:** authoritatively retrieve entitled quote/fundamental data; verify identities, timestamps, fiscal periods, currencies, licensing and arithmetic; persist exact approved versions of allowed historical inputs.
- **Never:** fabricate financial values/citations, treat retrieved filings or web text as executable instructions, bypass source permissions, silently merge unlike instruments, persist prohibited provider data, make autonomous trades or imply returns are guaranteed.
- **Output contract:** distinguish sourced observation, third-party estimate, calculation, AI inference, investor hypothesis, and unavailable/uncertain fact. A valid citation ID alone does not mean the claim is actually supported.
- **Orchestration:** start with one bounded coordinator and explicit typed tools, step/time/token budgets, transparent partial output, deterministic errors and cancellation. Do not adopt a multi-agent swarm, RAG/vector database or complex background infrastructure merely because it is fashionable.
- **Choice of LLM:** replaceable adapters, evaluated on representative financial tasks; model/vendor selection is not a promise of equivalence in correctness.
- **Consent and memory:** personal preferences, holdings, watchlists, conversations and thesis records are private and opt-in for durable storage. Users can review, correct, export and delete subject to disclosed retention rules. Private context must not enter repository fixtures or unrelated users' sessions.

## 7. Market data, licensed access and research history

All valid v2.0 financial semantics remain binding:
- Company/issuer vs listed instrument/venue/share class/currency; publication, economic, quote and retrieval times are separate.
- Actual provider rights constrain fetching, caching, redistribution, hosting, storage and historical replay. A public OSS license does not grant quote rights.
- Quote status distinguishes real-time/delayed/EOD/unknown **only when verifiable**. Current view is not historical evidence.
- The current view refreshes only on permitted request or properly configured entitlement; a deliberately approved thesis snapshot remains immutable.
- Historical quotes or derivatives unavailable for licensed retention must be omitted **and disclosed**, not reconstructed with today's numbers.
- Start with a narrow legally accessible supported universe and explicit coverage warnings; do not promise worldwide real-time markets.

**Consumer onboarding is a product requirement:** investigate legitimately permitted hosted data, user authorization or public filings/EOD; a technical BYOK configuration is acceptable for developers but **not** the only v0.3 consumer flow. If lawful data terms, cost or user permissions make an accessible experience impossible, **block the consumer release or validate an assistant integration instead of hiding API configuration complexity**.

Cloud persistence, accounts, authentication, entitlement partitioning, privacy notices and encryption become mandatory **when actual shared/private hosted use needs them**. Do not build cloud services before resolving the deployment and data-licensing decision. Offline developer mode remains supported.

## 8. Revised release roadmap (ordered; no delivery dates)

| Release | User-visible outcome | Acceptance / investment gate |
| --- | --- | --- |
| **v0.1.1 — released** | Offline synthetic open-source research toolkit | Historical release; unchanged |
| **v0.2.0 — source release candidate** | BYOK connected CLI, constrained financial facts and private rights-aware replay | Live provider/account/entitlement smoke and public release authorization remain distinct; no AI/UI claim |
| **v0.3 — AI Research Experience (NEXT)** | Accessible natural-language/company-first workflow; bounded AI tool coordination; sourced integrated research, thesis challenge, comparisons limited to compatible supported cases, interactive analysis | Real-user tasks, low-friction entry, citation/financial/permission/AI evaluation gates; detailed [PRD](ai-research-experience.md) |
| **v0.4 — Investor Context & Thesis Continuity** | Opt-in preferences, explicit watchlists, structured decision memory, as-of comparison, material research deltas, opt-in monitoring where operationally/licensably permitted | Saved decisions never silently change; users can correct/delete memory; repeat-session research demonstrably useful |
| **v0.5 — Opportunity Intelligence** | Evidence-based company discovery, comparable peer groups, fundamental/valuation trends, multi-horizon **research** screens and ranking explanations (no guaranteed alpha) | Reproducible data, bias checks, rank stability, no unsupported prediction or sector-inappropriate multiples |
| **v0.6 — Optional Portfolio & Scenarios** | Opt-in portfolio-context research, exposure overlap, concentration and sensitivity scenarios; no automated execution | Secure handling, privacy, trustworthy holdings sources, suitability/regulatory review as relevant |
| **v0.7+ — Conditional Quant Lab** | Historical strategy tests and factor hypotheses only with valid point-in-time datasets | Survivorship/look-ahead/corporate actions/fees/out-of-sample safeguards and data rights |
| **v1.0 — Only if validated** | Stable, adopted research workflow and interoperable APIs | Demonstrated external retention, maintainability, compliance and unit economics |

**Do not interpret release sequence as permission to start every release.** Every expansion requires prior task-based adoption and quality evidence. A browser product and an assistant-native distribution channel are **competing hypotheses** to test, not both predetermined infrastructure commitments.

## 9. Validation before feature expansion

See [Product Validation Plan](validation-plan.md). In brief:
- Compare identical tasks using **InvestIQ prototype**, **general LLM**, and **an incumbent research service** with representative independent investors.
- Collect baseline and follow-up evidence: first useful research completion, time and prompts/steps, unsupported financial claims, mistaken dates/currencies, citation accuracy, user corrections, perceived usefulness, return-session value, willingness to switch/pay and end-to-end unit cost.
- Use pre-agreed test cases (positive, missing, contradictory, stale, unsupported) and blinded expert quality reviews when possible.
- **Proposed target, not measured fact:** independently successful completion of one supported research task by a nontechnical user with **zero required CLI/API configuration**. Numeric speed, quality, retention and economic thresholds must be set after a baseline study, **not invented now**.
- Stop or pivot if differentiation versus alternatives is unconvincing. A polished demo is not product-market fit.

## 10. Delivery sequence after this planning PR

1. **Approve this strategy and [ADR 0009](../decisions/0009-ai-first-product-pivot.md)**; no code change is implied.
2. Prototype *one* supported investment-question-to-answer flow (standalone lightweight UI **and/or** assistant-native distribution variant) using existing permitted data/domain core. Validate onboarding and data rights before hosted public claims.
3. Draft outcome-based v0.3 PR boundaries: **(a) task-based UX / security and provider pathway, (b) tool-bound AI research orchestration and source-linked outputs, (c) financial/semantic AI evaluations and end-to-end real-user acceptance**. Sequence based on a runnable vertical slice; avoid platform-only PRs.
4. Decide distribution/hosting only after tester evidence. If user-facing market data cannot be lawfully provided at acceptable economics, limit scope and visibly disclose coverage rather than claiming capabilities.
5. Expand to research memory, alerts and discovery only when the first repeat-use hypothesis is demonstrated.

**Non-goals:** guaranteed outperformance; unconditional stock buy/sell ratings; automated brokerage execution; managed money/ETF; compulsory personal portfolio connection; unlicensed market-data redistribution; generic platform re-engineering; stock-ranking claims without validation.

## 11. Governance

The roadmap owns **why, who, what, release order and gates**; the [engineering blueprint](../engineering/engineering-blueprint.md) owns **how**. Durable decisions get ADRs. Existing v0.2 release notes, provider-specific ADRs and public Python compatibility remain historical facts. Product-quality, privacy, legal/data rights and research transparency are non-negotiable even when implementation favors AI-first speed.

**Approval status:** This proposed v3.0 baseline is not automatically approved by committing it. Merge/release/product deployment require normal review and deliberate decisions.
