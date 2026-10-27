# Contributing to InvestIQ

All contributors are welcome. Propose changes via an issue or pull request.

## Development

For fewer unnecessary GitHub Actions runs, follow the [draft-to-ready CI policy](docs/engineering/ci-efficiency.md): group local changes, keep unfinished PRs in draft, and make the PR ready only when the head is reviewable. CI still runs on every update **after** ready so the final-commit gate is never bypassed.


Follow the [InvestIQ Engineering Blueprint](docs/engineering/engineering-blueprint.md) for architecture, financial correctness, naming, tests, security, AI readiness and future UX requirements. The [connected-research roadmap](docs/product/product-roadmap.md) determines scope and release order; this blueprint determines how we build.

- Python 3.11+ and a virtual environment.
- Install: `python -m pip install -e ".[dev]"`.
- Verify locally: `ruff check .`, `pytest -q` and, for packaging changes, `python -m build --sdist --wheel`.
- Keep the codebase's current checks green; formatter/type/coverage/provider/browser/AI gates are adopted only when implemented and applicable, not by the blueprint alone.
- Keep pull requests outcome-based with a clear motivation, tests, and documentation updates.
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
