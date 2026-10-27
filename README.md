# InvestIQ

**Open-source, evidence-aware equity research.** InvestIQ v0.2.0 introduces opt-in, bring-your-own-key connected issuer analysis and private research-decision snapshots alongside the original offline Python toolkit, five AI-neutral research skills and hash-linked thesis history. The synthetic example and offline replay need no accounts or provider keys.

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
- [Approved Product Roadmap v2.0](docs/product/product-roadmap.md) — connected research, truthful quote freshness, provider strategy and releases
- [Architecture Decision: Connected Data](docs/decisions/0003-connected-data-and-research-history.md)
- [Roadmap Summary](docs/roadmap.md)
- [Changelog](CHANGELOG.md)

## Principles

Source-supported analysis over fabricated certainty. Distinct observed facts, consensus estimates, calculations and researcher assumptions. Date-aligned evidence. Explicit uncertainty and missing information. Portable, vendor-neutral interfaces. Synthetic-only public fixtures. No mandatory LLM or brokerage.

**Important:** A validated bundle is only structurally consistent. It has not been fact-checked against external documents, tested for model accuracy, or approved for personal investing.

## Connected research status

The [connected-research roadmap](docs/product/product-roadmap.md) targets **provider-agnostic, appropriately current market information** with visible source, session and delay, optional freshness-aware caching, and **immutable saved research decisions**. A local workspace may hold a user's private historic theses, but it must **not** masquerade as a live pricing feed.

The v0.2.0 Python/CLI connected vertical slice is **implemented**, but not independently tested against real provider accounts in standard CI. **Verified exchange real-time entitlement, unrestricted price retention, hosted accounts, shared cloud cache, full market coverage, web application and true historical backtesting are not shipped.**

## Contributing and safety

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md), the [Engineering Blueprint](docs/engineering/engineering-blueprint.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and [SECURITY.md](SECURITY.md). Use fictional or appropriately redistributable examples only; do not upload positions, account statements, tokens, confidential research or licensed vendor datasets. Local generated bundles should be kept out of Git.

## License

[MIT](LICENSE). Vendor financial-data licenses remain separate from the software license.
