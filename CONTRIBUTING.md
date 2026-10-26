# Contributing to InvestIQ

All contributors are welcome. Propose changes via an issue or pull request.

## Development
- Python 3.11+ and a virtual environment.
- Install: `python -m pip install -e ".[dev]"`.
- Verify: `ruff check .` and `pytest`.
- Keep pull requests outcome-based with a clear motivation, tests, and documentation updates.
- Use synthetic fixtures; never include personal or licensed non-redistributable market data.
- Explain financial methods and assumptions whenever calculations change.
- Identify sources and dates for factual financial claims. Do not claim backtested returns without reproducible methodology.
- Record architectural changes in `docs/decisions/` when they affect public contracts.
- PR authors must have rights to contribute code and data under MIT.

## Review checklist
- [ ] Behavior is covered by deterministic tests
- [ ] No missing-data fabrication or look-ahead bias
- [ ] New external inputs have provenance and licensing considerations
- [ ] No credentials, PII, or private portfolios
- [ ] Public documentation and examples still work
- [ ] Changes are backward compatible or explicitly documented

Be respectful and constructive. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
