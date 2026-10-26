# InvestIQ

**Open-source investment research infrastructure.**

InvestIQ helps anyone build evidence-based, reproducible equity research workflows: analyze financials, compare businesses, document investment theses, test assumptions, and eventually research systematic strategies.

InvestIQ is **software and research tooling**, not investment advice, a brokerage, a managed fund, or a promise of returns. It does not require a user account or brokerage connection.

## Project status
Early development. The first release focuses on an independently testable Python core and public methodology. There is no production API, investment recommendation service, live-price feed, or execution integration.

## Core principles
1. **Reproducible:** calculations and methods are explicit, versioned, and tested.
2. **Evidence-aware:** distinguish reported figures, third-party estimates, assumptions, and model outputs.
3. **Point-in-time:** track effective and available-as-of dates to prevent hindsight bias.
4. **Uncertainty-aware:** missing data is never silently estimated.
5. **Portable:** build a library first; apps, AI skills, and connectors are adapters.
6. **Community-first:** examples are synthetic; no personal portfolio or confidential research is committed.
7. **Neutral:** compare opportunities with documented assumptions, not unverified claims of superiority.

## Quick start
Requires Python 3.11+.

```bash
git clone https://github.com/jayaprakash87/InvestIQ.git
cd InvestIQ
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
python -m pip install -e ".[dev]"
pytest
```

Example:

```python
from investiq_core.valuation import scenario_return

result = scenario_return(start_eps=5.0, annual_eps_growth=0.10, years=3,
                         terminal_pe=15.0, initial_price=75.0)
print(round(result, 4))  # 0.331
```

This is a synthetic illustration of price-return arithmetic, not a forecast.

## Roadmap
- **Foundation:** public product scope, methodology, source rules, contribution guidelines, CI.
- **Core:** typed financial calculations, scenarios, confidence and missing-data handling.
- **Skills:** portable analysis instructions with source-backed, schema-checked output.
- **Decision records:** versioned investment theses and changing assumptions.
- **Strategies:** point-in-time backtests, realistic costs, documented risk constraints.
- **App/API (later):** optional web research interface and integration endpoints.

Read [Product Scope](docs/product/scope.md), [Methodology](docs/methodology/principles.md), [Architecture](docs/architecture/overview.md), and [Contributing](CONTRIBUTING.md).

## Data and privacy
Use synthetic or openly licensed sample data. Do not commit private holdings, passwords, paid market-data dumps, personal records, or licensed third-party research without permission. See [Security](SECURITY.md).

## License
MIT; see [LICENSE](LICENSE).

## Disclaimer
InvestIQ is experimental research software for informational and educational use only. It does not provide individualized investment advice. Investing can result in loss of principal; outputs are conditional on data and assumptions.
