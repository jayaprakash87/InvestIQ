# Contributing to InvestIQ

All contributors are welcome. Propose changes via an issue or pull request.

## Development

For fewer unnecessary GitHub Actions runs, follow the [draft-to-ready CI policy](docs/engineering/ci-efficiency.md): group local changes, keep unfinished PRs in draft, and make the PR ready only when the head is reviewable. CI still runs on every update **after** ready so the final-commit gate is never bypassed.


Follow the [InvestIQ Engineering Blueprint v2.0](docs/engineering/engineering-blueprint.md) for financial integrity, bounded AI orchestration, evaluation, security, architecture and v0.3 UX gates. The [proposed AI-first Product Roadmap v3.0](docs/product/product-roadmap.md) sets user outcomes and priorities; the blueprint sets implementation standards. [ADR 0009](docs/decisions/0009-ai-first-product-pivot.md) records the proposed strategic change; it does not alter completed v0.2 behavior.

- Python 3.11+ and a virtual environment.
- Install: `python -m pip install -e ".[dev]"`.
- Verify locally: `ruff check .`, `pytest -q` and, for packaging changes, `python -m build --sdist --wheel`.
- Keep the codebase's current checks green; formatter/type/coverage/provider/browser/AI gates are adopted only when implemented and applicable, not by the blueprint alone.
- Keep pull requests **user-outcome-based** with a clear motivation, tests, documentation and applicable product-validation evidence. Do not add general backend infrastructure without a demonstrated user need.
- Use synthetic fixtures; never include personal or licensed non-redistributable market data.
- Explain financial methods and assumptions whenever calculations change.
- Identify sources and dates for factual financial claims. Do not claim backtested returns without reproducible methodology.
- Record architectural changes in `docs/decisions/` when they affect public contracts.
- PR authors must have rights to contribute code and data under MIT.

## Review checklist

Apply the [engineering review checklist](docs/engineering/engineering-blueprint.md#11-review-ownership-and-practical-release-gate) for the affected module. Docs-only changes do not require invented unit-test changes, but links/status claims must be accurate.

- [ ] Behavior is covered by deterministic tests
- [ ] No missing-data fabrication or look-ahead bias
- [ ] New external inputs have provenance and licensing considerations
- [ ] No credentials, PII, or private portfolios
- [ ] Public documentation and examples still work
- [ ] Changes are backward compatible or explicitly documented

Be respectful and constructive. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
