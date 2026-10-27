# InvestIQ — Product Validation, Dogfooding and External Adoption

> **Status:** Proposed evidence protocol · **Date:** 2026-10-27 · **No user-study or model-evaluation outcome is claimed.**
> **Scope:** [Complete v0.3→v1.0 roadmap](product-roadmap.md) · [Personal Desk PRD](ai-research-experience.md).

## 1. Validate in the right order

InvestIQ is **already open-source**, but its source release candidate is still developer-oriented. Validate usefulness with the original research user **first**, then validate whether independent investors can install/use it without developer assistance.

- **Initial use validation (v0.3–v0.6):** an investor uses real supported companies and evaluates the workflow against an LLM and existing research tools; records errors, repeated prompting, sourced detail, coverage gaps, time saved and whether conclusions changed after correct data.
- **Personal repeat use (v0.7–v0.8):** user revisits tracked hypotheses across real filings/price changes, sees relevant material deltas and optionally uses private portfolio context.
- **External OSS beta (v0.9):** small independent group configures, uses, evaluates, exports and attempts to extend the same supported code with their own watchlists and data.
- **v1.0 gate:** stable installation, end-to-end research tasks, maintained schemas/security/permission constraints and observed repeat engagement; not arbitrary GitHub star counts or feature checklist alone.

## 2. Ground tests in prior real research

| Task | Existing-workflow pain | Expected product value | First milestone |
| --- | --- | --- | --- |
| Analyze a supported listed company | Repeated source collection and prompts, stale quotes, weak historical continuity | One bounded, cited AI/finance research flow with risks and explicit data gaps | v0.3 |
| Compare economically different companies and business models | Misleading one-size-fits-all P/E/score and subjective comparable lists | Explain industry/value-chain exposure, appropriate unit economics and inappropriate comparison cases | v0.4 |
| Rank a theme/industry universe | Manually updated large spreadsheet, opaque weights and rank instability | Versioned factor methods, dated coverage, uncertainty and sensitivity | v0.5 |
| Test valuation/entry price | Return scenarios manually recalculated using approximate forward EPS and assumed terminal multiples | Transparent exact, dated reverse underwriting with explicit conditional limits | v0.6 |
| Revisit research thesis | No reliable answer to "what changed since my last work?" | Distinguish market/financial/source/method and assumption changes; original thesis preserved | v0.7 |
| Assess overlapping exposures | Holdings, thematic allocations and watchlists managed separately | Private optional portfolio/context comparison | v0.8 |
| Install independently | Developers' CIK/MIC, API env vars, shell commands and opaque data terms | Documented package, guided setup, synthetic demo and complete browser/task UX | v0.9–v1.0 |

## 3. Personal weekly acceptance log

For each product milestone record **research session date, qualified instrument, question, exact supported data period, expected output, actual result, missing data, corrections, task time, provider/model usage/cost, usability friction and follow-up decision** in a *private* notebook/test record, never public Git.

Do not silently turn this personal log into a persistent cloud service or require sending private holdings to an LLM. Publish sanitized issue summaries with synthetic or permitted fixtures only.

**Proposed initial-use success criteria (qualitative until baseline):** an initial investor voluntarily prefers InvestIQ over general-purpose AI prompting and manual research assembly for a bounded supported task; major numeric/source errors are absent and unsupported-data warnings are credible. Record failures openly. No performance/accuracy threshold invented before tests.

## 4. Matched-task comparison with alternatives

Compare the same dated research question through (a) InvestIQ, (b) generic ChatGPT or comparable model with permitted research access and (c) a credible financial research tool. Use the same supported universe, task times and source information where feasible; counterbalance order and disclose differential provider entitlements.

Collect **first-useful-answer time**, prompts/corrections, source-to-claim correctness, numerics/units, valid peer choice, meaningful bear-case quality, missing-data honesty, usability, model/data cost and repeat research reuse. Use independent, partially blinded expert review for unsupported numbers, citations and financial implications.

**Distribution decision:** The planned personal default is a **simple locally runnable task UI**; an assistant-native plugin/skill/MCP integration may supplement it or become a preferred external distribution channel if real evidence justifies it. Do not use undecided distribution as an excuse to postpone the user's personal app.

## 5. External OSS testing (v0.9)

Recruit a small mix of independent equity researchers and less technical investors; test fresh install on declared supported OS, no-key synthetic demo, one authorized market/model setup path, supported company research, scenario analysis, lawful private save/replay, watchlist and export. Verify no need to code or manually fill CIK/MIC during normal user use.

Capture completion, time, comprehension of real-time/delayed status and missing data, whether source restrictions are understood, privacy controls, provider/model cost transparency and user preference. Record sample size, bugs, drop-off, quote licensing, and corrections instead of claiming PMF from a few anecdotes.

Test plugin/adapter extensibility by having an external contributor follow documented interfaces and synthetic fixtures without accessing private credentials or live licensed datasets.

## 6. Stop/go decision criteria

- **Proceed** when personal weekly use and correct sourced research justify the next dependent milestone; external adoption supports release stabilization.
- **Reduce scope** when a selected source or geographic accounting regime cannot reliably support advanced comparisons/valuation.
- **Change channel** when assistant-native delivery provides comparable value with much less user effort and maintenance cost.
- **Stop** when material hallucinations, wrong financial comparisons, source rights, costs, privacy or sustained nonuse make a trustworthy product impractical.

**Hard safety constraints at every milestone:** zero knowingly fabricated "official" prices/financials; no unsupported current/live status; no unlicensed retention or distribution; no silent thesis/holdings modification or automated trade execution; privacy of real positions and model credentials.
