# InvestIQ v0.3 — AI Research Experience PRD

> **Status:** Proposed, **not implemented** · **Date:** 2026-10-27
> **Owner:** Product / Engineering · **Roadmap:** [v3.0](product-roadmap.md)
> **Primary user:** self-directed equity investor who cannot or does not want to use Python, API keys, JSON or prompt-engineering recipes.

## 1. Product hypothesis

A single, source-linked AI research workflow can reduce investor research effort and provide a better challengeable decision record than a general-purpose LLM prompt sequence. This is unproven until matched-task user testing. The next product objective is **a complete answer**, not a feature-complete financial terminal.

**Hero use case:** "Evaluate [supported listed company] for a multi-year holding period. Explain the business, key fundamental trend, how valuation depends on assumptions, the strongest bear case, and the evidence we still need."

## 2. End-to-end user journey

1. **Ask/select:** Investor enters a natural-language question or searches a company. Show the supported coverage boundary; choose the exact instrument and venue if ambiguous. No CIK/MIC knowledge required.
2. **Research:** A bounded, cancellable AI coordinator requests only approved source, identity, valuation and report tools. Disclose that an external model/data provider is used and request necessary consent.
3. **Review:** Present a concise answer first; then progressive disclosure of business, key facts/trend (only available periods), qualified valuation/scenarios, risks, strongest contradiction, gaps and source drawer.
4. **Interact:** Allow grounded follow-up questions and investor-edited scenario parameters; recompute via deterministic functions, not LLM arithmetic.
5. **Record (opt-in):** Offer an explicitly user-approved, versioned thesis summary. Show permissible stored fields, omissions under provider restrictions and deletion/export controls.
6. **Return:** In v0.3, reopen only saved permitted records; **automated material change detection and alerts belong to v0.4**, not this release.

**Product navigation:** question bar + Research / Compare / Challenge actions. "What changed?" may appear only as visibly unavailable/planned before v0.4; no fake actionable navigation.

## 3. Functional acceptance criteria (v0.3)

- **F01 Usable entry:** Representative nontechnical tester can begin and complete one supported case without command line, configuring developer secrets or manually selecting a CIK. Consumer data licensing must be verified; otherwise no public/consumer-release claim.
- **F02 Tool contracts:** Document and exercise typed tool calls for identity resolution, entitled current/filing data retrieval, deterministic analysis, source lookup, research output and explicit snapshot request. Model must not call network directly or write private snapshots without approval.
- **F03 Integrated answer:** Includes business description with citations where available, key financial observations, qualified valuation or explicit N/A, bear case, and concrete information gaps. No invented financial facts, price targets or unsupported comparisons.
- **F04 Transparent evidence:** Material numeric claims have authoritative observation IDs and accessible source, unit/currency, periods and market-source timestamp/timeliness. Separate *reported / consensus / calculated / AI inference / investor assumption / unavailable*.
- **F05 Challenges:** A visible counter-thesis with testable conditions, not a generic risk list; summarize why the investment may be unattractive despite a positive narrative.
- **F06 Honest coverage:** Explain unsupported companies, missing metrics, source outages, stale/unknown quote states, conflicting or amended filings, wrong share basis, ambiguous listing and licensing denials; no silent fallback.
- **F07 Interactive grounded scenarios:** Editable assumptions map to typed validated inputs; recomputed figures come from deterministic domain functions. Unsupported forecasts and historical claims are labeled as such.
- **F08 Accessible experience:** Responsive layout; semantic controls; keyboard and screen-reader paths; clear loading/cancellation, retry, error and partially available states. Link directly from key claims to evidence.
- **F09 Privacy:** No implicit storage of investor profile, private research, holdings or chat transcripts. Disclose model and data providers, consent for sending private content, approve saves and provide applicable export/delete actions; protect secrets.
- **F10 Operational economics:** Instrument research request counts, model tokens/cost, elapsed latency, failures, stale rates and usage of entitled datasets using privacy-respecting aggregate/opt-in metrics; budgets and caps enforced.
- **F11 Comparisons are scoped:** Compare only supported, economically comparable instruments/periods; otherwise produce an explicit mismatch/gap report. Broad discovery/screening is deferred to v0.5.
- **F12 User validation:** Complete the [matched-task study](validation-plan.md) and record comparative findings and the proceed/narrow/pivot decision before moving to v0.4.

## 4. AI output and behavior contract

Use the structured ResearchReport/evidence contracts where appropriate, extended *only as needed* for answer blocks, tool-run trace IDs, source attribution and uncertainty. Do not conflate structural schema validity with factual validation.

**Answer structure:** Short answer with uncertainty → source-grounded evidence → key valuation conditions (or inapplicability) → strongest disconfirming evidence → evidence gaps → optional user-controlled scenario and save.

No autonomous trades, guaranteed-alpha rankings, price alerts before lawful scheduling, background monitoring without explicit opt-in, or automatic overwrite of research records.

**Failure behavior:** If credible data are unavailable, return "cannot substantiate" plus why and safe next steps; never fill source gaps with plausible-looking values. If model output fails factual/numeric gating, repair within bounded retry budget or show partial deterministic evidence with a visible AI-analysis failure.

## 5. Quality and security gates

- Frozen/redistributable fixtures + expert-reviewed golden answers for correct, stale, conflicting, unsupported, malicious-document and cross-issuer cases.
- CI checks where implemented: schema/tool contract; exact arithmetic delegation; source-claim semantic alignment; chronology/look-ahead; refusal of unauthorized retention; injection attempts; privacy/tenant boundary; regression after model/prompt changes.
- Manual task acceptance: researcher interviews, screen-sharing-free usability tasks, accessibility review, source drill-down and informed-consent comprehension. Report results rather than claiming success.
- A public hosted experience is blocked until rights to display/retain provider data, LLM processing, privacy/GDPR obligations, authentication/security and cost are assessed and approved.
- A connector/assistant-native research distribution path is a valid alternative if it passes user/value tests with less burden than a custom UI.

## 6. Outcome-based PRs (planning proposal, not authorization to build)

1. **Thin task UI + supported data/onboarding path:** validate exact user journey and lawful quote/filing sourcing, with mocks where necessary; no generic dashboard scaffolding.
2. **Bounded AI tool orchestration + grounded research renderer:** one company question and one supported comparison, transparent reasoning artifacts (not hidden model internals), negative/error paths.
3. **AI semantic/financial evaluations + real-user acceptance:** model regression harness, prompt-injection/security review, provider trial evidence and first-session usability study.

**Stop gate:** The complete journey does not beat a general LLM or current research tool on enough valued dimensions, provider economics are unacceptable, or source fidelity is not safe. Do not add v0.4 persistence/monitoring as a workaround for a failed v0.3.
