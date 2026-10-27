# Getting started with InvestIQ v0.2.0

InvestIQ has an **offline synthetic workflow** and an **opt-in connected issuer-research workflow**. Python 3.11+ is required. No account or key is necessary for offline use.

**What this is not:** The current v0.2.0 source release candidate is developer-oriented CLI software, **not an integrated LLM research assistant or consumer UI**. The [proposed v0.3 AI Research Experience](product/ai-research-experience.md) aims to remove API/CIK/terminal setup for a supported nontechnical user; it is not implemented. See the [AI-first roadmap](product/product-roadmap.md) and [user validation protocol](product/validation-plan.md).

## Installation

```bash
git clone https://github.com/jayaprakash87/InvestIQ.git
cd InvestIQ
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
investiq --help
```

For Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` or run the `.venv\Scripts\python` and `.venv\Scripts\investiq` executables directly. A built `0.2.0` wheel can be installed with `python -m pip install dist/investiq_core-0.2.0-py3-none-any.whl` after running `python -m build`.

## Offline synthetic example

```bash
investiq demo --output demo.json
investiq validate demo.json --basis public
investiq validate demo.json --basis recorded
```

The bundle contains fictional issuer observations, explicit assumptions, source-linked reports, valuation scenarios and a hash-linked thesis. A validator result such as `"validation": "structural_only"` **does not** verify a company's actual fundamentals or forecasts.

## Connected one-company research

`investiq research` is optional network access. It needs your authorized `TWELVE_DATA_API_KEY` and a real `INVESTIQ_SEC_USER_AGENT`; specify the **verified** issuer-to-listing source, effective date, ticker, venue/MIC, currency and age policy. Use [the connected CLI guide](methodology/connected-cli.md) for examples, caveats and permissions.

Connected mode shows a source-attributed quote and selected SEC annual facts, with clear freshness/session/missing-data flags. It does not automatically save data, perform currency conversion, claim a real-time feed or recommend securities. Requested annual P/E is withheld unless the required financial context and an independent share-basis confirmation are supplied.

## Explicit research save and offline replay

Use `investiq research ... --save-dir <private-dir> --thesis-id ... --thesis-statement ... --revision-reason ...` to create a private decision **only when requested**. Then run `investiq replay --store-dir <private-dir> --thesis-id ... --revision 1` offline, optionally with `--format markdown` or `--format manifest`.

Market quote prices with UNKNOWN/DENIED snapshot rights—including the current Twelve Data adapter—are **not captured**, and derived prices/valuation are absent in replay. The resulting record still preserves supported SEC public financial facts, authored thesis and eligible assumptions. A GitHub repository is not a private research store.

## Five portable research skills

Read [skills/](../skills/README.md) to use the business-analysis, financial-analysis, valuation-analysis, peer-comparison and thesis-challenge skills. AI-generated prose remains subject to independent source verification; the structural report validator is not a factuality oracle.

## Known limitations and troubleshooting

- `investiq: command not found`: ensure the environment is active or use `python -m investiq_core`.
- Connected-provider errors: check API key, contact User-Agent, subscription/venue permissions, SEC fair access and the explicitly provided CIK/listing metadata. Never paste keys into issues or PRs.
- Stale/unknown quote: increase the age policy **only when analytically justified**, not merely to make a red status disappear; the provider/exchange entitlement remains separate.
- Snapshot save failures: ensure the parent directory exists, your private child directory permissions are suitable and the revision's preceding hash-linked history is present.
- A missing or incompatible EPS does not justify an invented P/E or forecast. US-GAAP annual 10-K support is intentionally narrow.
- Run `ruff check .`, `pytest -q`, and `python -m build --sdist --wheel` to check source quality. No keys/network required for CI.
- The [release acceptance matrix](engineering/release-acceptance-v0.2.md) explicitly separates synthetic automated evidence from manual authorized live-provider verification.

InvestIQ is research software, **not investment advice, a trading service, or permission to retain/redistribute a commercial data feed**.
