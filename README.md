# InvestIQ

**Open-source, evidence-aware equity research.** InvestIQ v0.2.0 introduces opt-in, bring-your-own-key connected issuer analysis and private research-decision snapshots alongside the original offline Python toolkit, five AI-neutral research skills and hash-linked thesis history. The synthetic example and offline replay need no accounts or provider keys.

**Product direction:** [InvestIQ's AI-first, open-source roadmap to v1.0](docs/product/product-roadmap.md) starts with a useful local equity research interface (v0.3), then progressively adds source-connected analysis, valid comparisons, configurable screening/scoring, valuation scenarios, thesis monitoring, optional private portfolio research and external-user readiness. **The platform is independent of particular industries, stock selections, research histories and portfolios.** **PR 1–4 provide a synthetic UI, issuer candidate discovery, connected public filing/financial evidence and optional BYOK AI assistance.** Full verified industry economics, interactive valuation, source-to-claim semantic evaluation and saving research through the browser remain future work.

**This is experimental research software, not investment advice, a trading system, live market-data feed, backtesting engine or managed investment product.** No returns or predictive accuracy are claimed.

## What works

| Capability | Implementation |
| --- | --- |
| Attributed financial evidence | Venue-qualified identities, exact decimal amounts, currency and source metadata |
| Historical information cutoffs | Public-availability and locally-recorded as-of views, revision chains |
| Valuation arithmetic | EPS multiples, compound returns, reverse valuation, subjective bear/base/bull sensitivities |
| Research skills | Business, financials, valuation, peer comparison and thesis challenge |
| Research report validation | Structural citations, fact/estimate/hypothesis separation, source timing |
| Thesis version history | Hash-linked snapshots, differences, JSONL export/import, falsification checkpoints |
| Offline workflow | Generate and validate a complete **synthetic** research bundle from the CLI |
| Local research preview (v0.3 PR 1) | Browser-based display of the **existing fictional evidence, deterministic scenarios and thesis history** on loopback; no AI, external providers or persistence |
| Connected research (v0.3 PR 2) | User-initiated SEC candidate lookup, explicit listing and currency confirmation, session-only SEC/Twelve Data credentials, current source-attributed facts and price with conservative rights and freshness |
| Filing evidence inspection (v0.3 PR 3) | On-demand SEC 10-K primary-document passage retrieval, stable excerpt IDs and document provenance; deterministic keyword matching, **not** AI/verified section extraction |
| AI research orchestration (v0.3 PR 4) | BYOK optional model: bounded SEC 10-K passages and annual SEC facts, validated source IDs, critical counter-thesis, explicit per-request consent; no licensed quotes, saved AI output or guaranteed interpretations |
| Interactive follow-ups & scenarios (v0.3 PR 5) | Suggested fresh questions with renewed AI consent, temporary on-page question list and editable bear/base/bull EPS/P-E scenarios recalculated by the deterministic Python core using **manual hypothetical inputs only** |
| Connected issuer research (opt-in) | SEC annual US-GAAP facts + Twelve Data one-minute CLOSE with unknown declared timeliness, sourced via explicit CIK/listing |
| Private decision snapshots | Explicit permission-gated save; offline replay and JSON/Markdown exports, not automatic provider retention |

## Quick start (Python 3.11+)

```bash
git clone https://github.com/jayaprakash87/InvestIQ.git
cd InvestIQ
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
investiq demo --output demo.json
investiq validate demo.json --basis recorded
pytest -q
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`. If shell activation is restricted, run `.venv\Scripts\python -m pip install -e ".[dev]"` and `.venv\Scripts\investiq demo` instead.

The `demo.json` file is locally generated and entirely fictional. `investiq demo` prints JSON to stdout when `--output` is omitted. `python -m investiq_core demo` is an equivalent module entry point. `investiq validate` checks supplied local bundles and prints structured results. It does **not** fetch live prices, execute trades, or certify the meaning of natural-language research conclusions.

For an installed package, use `python -m pip install .` or an official release wheel. No mandatory service or paid dependency.

## Local Research App — synthetic preview (v0.3 PR 1)

Run the same fictional offline workflow in a responsive research interface:

```bash
python -m pip install -e .
investiq app
```

A local browser page opens at `http://127.0.0.1:8765/`; click **Run synthetic research**. If the browser should not open automatically, run `investiq app --no-browser`. Set a different local port with `--port 8766`. Stop the server with Ctrl+C.

**Synthetic demo:** Fictional, offline, key-free evidence and valuations with structural-only validation. The **Run synthetic research** button never contacts market-data or AI providers.

**Optional real-company research (PR 2):** On the same local page, open **Connected research**; enter your actual SEC contact User-Agent (name and email). Add an entitled Twelve Data API key **only if you want quotes**. Credentials are held in the running Python process memory only, never written to disk or returned to the browser. Search a company name or ticker through the SEC directory, choose a **candidate** Nasdaq/NYSE listing, independently check its current listing and USD trading currency, then submit the connected request.

The research view shows eligible SEC annual US-GAAP facts, the provider's most recent minute-candle **CLOSE** price and source/timestamp/session/freshness qualifications. Delivery timeliness/real-time entitlement are **unknown**; exchange, currency and EPS share-basis agreement are not independently proven by the directory. **Annual P/E remains suppressed** pending share-basis confirmation. The UI does not save quotes or thesis revisions, and cannot claim full economic research, financial accuracy, AI capability or an investment recommendation. Provider access may be charged. Use **Disconnect** to discard keys and directory from memory; server termination also clears them. The app runs on loopback HTTP; do not expose it to other devices or untrusted users, and close the page after using private credentials.

**SEC document evidence (PR 3):** After choosing and confirming a supported issuer in Connected research, select **Business**, **Risks** or **Management discussion**. InvestIQ fetches the latest supported 10-K primary HTML from SEC public archives on request, extracts up to four small keyword-matching passages and shows its accession, filing date, original SEC document link, normalized extraction offsets and content hashes. This is *not* AI, proven official filing-section segmentation or an assertion that an excerpt supports an investment thesis. The entire filing body is not returned to the browser, cached or saved. HTML larger than the conservative 8 MB limit, unsupported encodings, unavailable recent filings, malformed data and provider restrictions fail closed. SEC fair-access pacing applies. See [SEC accessing EDGAR data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data).

**Optional AI research (v0.3 PR 4):** Select a supported company and confirm the issuer/currency. Under **Source-grounded AI research**, configure your private OpenAI API key and choose a supported model. Enter a research question, then explicitly consent **for each request** to sending a limited set of public SEC 10-K excerpts, annual US-GAAP SEC facts and that question to OpenAI. Its API fees and data-handling terms apply. InvestIQ sends no Twelve Data quote, price, license token, private holding or saved thesis. API requests use `store:false`, no tools and a fixed maximum output; storage/retention by the external provider is still governed by its policies.

The answer contains structured findings, an opposing interpretation, questions and known source IDs. The source references are attached by InvestIQ, not invented links from the model. **A valid citation means the source was supplied, not that the cited claim is true.** The model is not a calculator, recommender or independently verified investment analyst. Unsupported sources/references cause the request to fail rather than return fabricated evidence. The model key and AI response are not saved by the application. Public SEC document download, quote retrieval and AI requests occur only after direct user actions.

**Interactive research (PR 5):** The AI response suggests additional research questions. Selecting one fills your question field; review and edit it, then explicitly authorize another SEC-only model call. Each request retrieves its own evidence and has **no conversational memory**: previous questions or model responses are not sent as context. A short list of questions stays in the current browser tab only and clears when the issuer/model/session changes.

Use **Hypothetical scenario workbench** for editable bear/base/bull EPS growth, terminal P/E and subjective weights. Enter positive hypothetical annual EPS and entry price **manually** in the same USD/share and compatible split basis. We intentionally do **not** prefill the form from SEC issuer-wide EPS or a quote with unverified rights/split basis. The existing deterministic `evaluate_scenarios` computes per-case terminal prices and price returns, weights terminal values and annualizes the weighted price; it does not average CAGR percentages. No external model/market-data request or saved history is involved. Negative EPS, missing data, non-finite inputs, invalid weight totals and unsupported horizons fail closed. Results are hypothetical **price-only**, not personal financial advice or price targets.

**Independent provider smoke not yet performed:** CI uses injected fake HTTP/provider responses and cannot establish your plan's exchange entitlement, quotation freshness, current SEC directory coverage, user-specific permissions or ability to redistribute vendor data.

## Connected CLI (v0.2.0)

**Opt-in network:** `investiq research` connects to SEC EDGAR and Twelve Data using `INVESTIQ_SEC_USER_AGENT` (your real contact) and `TWELVE_DATA_API_KEY` (your own authorized provider entitlement). Specify a verified issuer CIK/listing, exchange MIC, currency, effective date and a user-selected freshness policy. Source delay can remain `unknown`; that is not a real-time claim.

**Offline:** `investiq replay` opens a deliberately saved, private research decision without any API key or network calls. The default Twelve Data quote does **not** grant snapshot retention, so its price and price-derived calculations are omitted from saved records.

See the [connected CLI guide](docs/methodology/connected-cli.md) and [release acceptance status](docs/engineering/release-acceptance-v0.2.md) for commands, limitations and tests. **The code is not a provider-licensed hosted feed or financial recommendation service.**

## Python library example

```python
from investiq_core.valuation import (
    ValuationScenario, evaluate_scenarios, required_eps_growth
)

analysis = evaluate_scenarios(
    start_eps=5.0, initial_price=75.0, years=3,
    scenarios=[
        ValuationScenario("bear", 0.0, 10, 0.25),
        ValuationScenario("base", 0.10, 15, 0.50),
        ValuationScenario("bull", 0.20, 20, 0.25),
    ],
)
print(round(analysis.expected_terminal_price, 4))  # 105.6125
print(round(required_eps_growth(
    start_eps=5, initial_price=75, years=3,
    terminal_pe=15, target_annual_return=0.10,
), 4))  # 0.1
```

All numbers are **fictional assumptions**, not estimates of a listed company's financial performance. Outputs exclude dividends, dilution, transaction costs and other real-world considerations.

## Documentation

- [Getting started and CLI](docs/getting-started.md)
- [v0.1 scope and limitations](docs/product/scope.md)
- [Evidence contract](docs/methodology/evidence-contract.md)
- [Connected market-data contracts (v0.2 PR 1)](docs/methodology/connected-data-contracts.md) — provider-neutral types
- [Optional provider adapters (v0.2 PR 2)](docs/methodology/provider-adapters.md) — SEC filings and Twelve Data BYOK quote access; not a connected research UI
- [Connected data service (v0.2 PR 3)](docs/methodology/connected-data-service.md) — on-demand data validation, freshness, licensed caching and bounded retries
- [Connected current research (v0.2 PR 4)](docs/methodology/connected-research.md) — SEC annual GAAP facts, qualified P/E and user-supplied scenarios; no persistent theses
- [Private research snapshots (v0.2 PR 5)](docs/methodology/research-snapshots.md) — explicit lawful retention, offline replay and JSON/Markdown outputs
- [Connected and replay CLI (v0.2 PR 6)](docs/methodology/connected-cli.md) — explicit connected research, optional save, and offline replay
- [Research report contract](docs/methodology/research-report-contract.md)
- [Valuation conventions](docs/methodology/valuation.md)
- [Thesis history](docs/methodology/thesis-history.md)
- [Portable AI skills](skills/README.md)
- [Project architecture](docs/architecture/overview.md)
- [Engineering Blueprint](docs/engineering/engineering-blueprint.md) — code quality, architecture, testing, security, AI readiness, future UX and PR gates
- [Proposed Product Roadmap v3.0 → v1.0](docs/product/product-roadmap.md) — personal dogfooding, phased investing capabilities and independent OSS release gates
- [v0.3 Personal AI Research Desk PRD](docs/product/ai-research-experience.md) — first usable local app, supported company research and bounded tools
- [Product Validation Plan](docs/product/validation-plan.md) — first personal daily use, then external install/repeat-use and LLM/tool comparisons
- [ADR 0009 — AI-first product pivot](docs/decisions/0009-ai-first-product-pivot.md) — proposed roadmap decision
- [Architecture Decision: Connected Data](docs/decisions/0003-connected-data-and-research-history.md)
- [Roadmap Summary](docs/roadmap.md)
- [Changelog](CHANGELOG.md)

## Principles

Source-supported analysis over fabricated certainty. Distinct observed facts, consensus estimates, calculations and researcher assumptions. Date-aligned evidence. Explicit uncertainty and missing information. Portable, vendor-neutral interfaces. Synthetic-only public fixtures. No mandatory LLM or brokerage.

**Important:** A validated bundle is only structurally consistent. It has not been fact-checked against external documents, tested for model accuracy, or approved for personal investing.

## Connected research status

The [proposed personal-to-v1.0 AI-first roadmap](docs/product/product-roadmap.md) keeps source-entitled freshness and **immutable saved research**, while planning a **locally runnable research UI as the first personal product (v0.3)**. An assistant/skill/MCP interface is an optional additional distribution channel. Current financial data still come from appropriately entitled provider APIs; local history must **not** masquerade as a live pricing feed.

The v0.2.0 Python/CLI connected vertical slice is **implemented**, but not independently tested against real provider accounts in standard CI. **Verified exchange real-time entitlement, unrestricted price retention, hosted accounts, shared cloud cache, full market coverage, full AI-powered web research application, independent live-provider entitlement verification and true historical backtesting are not shipped.**

## Contributing and safety

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md), the [Engineering Blueprint](docs/engineering/engineering-blueprint.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and [SECURITY.md](SECURITY.md). Use fictional or appropriately redistributable examples only; do not upload positions, account statements, tokens, confidential research or licensed vendor datasets. Local generated bundles should be kept out of Git.

## License

[MIT](LICENSE). Vendor financial-data licenses remain separate from the software license.
