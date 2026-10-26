# Getting started with InvestIQ v0.1

InvestIQ is an offline, open-source research library and CLI. Nothing in this quickstart requires credentials, external subscriptions, a model provider, portfolio holdings or a brokerage account.

## Installation

Install Python 3.11 or newer and Git, clone the public repository and run:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
investiq --help
```

Windows PowerShell activation: `.venv\Scripts\Activate.ps1`. Alternatively invoke the virtual environment's Python directly. Install from a release wheel with `python -m pip install investiq_core-0.1.1-py3-none-any.whl`.

## Reproduce the complete research example

```bash
investiq demo --output demo.json
investiq validate demo.json --basis public
investiq validate demo.json --basis recorded
```

Or use `python -m investiq_core demo` to print the synthetic bundle to stdout.

The bundle includes:
- two fictional, attributed financial observations;
- one explicit, evidence-linked hypothetical growth assumption;
- a source-cited research report with an acknowledged data gap;
- two research thesis vintages linked by a content hash;
- a purely hypothetical valuation scenario with multiple outcomes.

Validation prints counts, scenario arithmetic and the declaration `"validation": "structural_only"`. It checks referenced IDs, venue-qualified securities, report and thesis time cutoffs, supported assumptions and input shape. It does **not** independently verify statement truth, return forecasts or expected probabilities.

The scenario's `hypothetical_entry_price` is **not** a market quote. All example values are synthetic.

## Using the research skills

Each [skills/](../skills/README.md) directory contains a standalone `SKILL.md`. Provide your chosen assistant with the skill instructions and explicit, authorized financial observations. Have the assistant return the documented `ResearchReport` structure; parse and validate that output using `investiq_core.research`. A report passing validation still requires human/source review for actual correctness.

## Python APIs

The package exposes modules `investiq_core.evidence`, `valuation`, `research`, `thesis` and `workflow`. See the executable tests for detailed examples. Use `Decimal` for sourced monetary observations, and explicit hypothetical numeric assumptions for illustrative scenario arithmetic.

## Privacy and data rights

No live data is downloaded and no contents are sent to external services. The program reads and writes local JSON only. Do not commit your research bundles if they contain private information. The MIT software license does not grant redistribution rights to any financial datasets.

## Known limitations

There is no real market-data adapter, persistence database, authentication, PDF ingestion, application UI, stock screener, portfolio tracking, backtesting or trading. Historic public-availability timestamps still depend on the trustworthiness of the source data; a publication date alone cannot prevent every form of historical revision bias.

## Troubleshooting

- `investiq: command not found`: ensure the virtual environment is active or use `python -m investiq_core`.
- `validation failed`: check source availability, explicit citation IDs, input units, research cutoffs and JSON schema version.
- A negative/non-meaningful EPS cannot be modeled through simple P/E scenarios; use an appropriate method when available.
- Check build/test health with `ruff check .`, `pytest -q`, and `python -m build`.
