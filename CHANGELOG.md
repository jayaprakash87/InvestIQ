# Changelog

The software is under active development. The public API may evolve; use versioned research bundles.

## [0.1.0] — 2026-10-26

First public research-toolkit release.

### Added
- Installable, no-account Python package and offline CLI.
- Synthetic, end-to-end research demo and validation command.
- Venue-qualified securities, source provenance and separate public/recorded historical cutoffs.
- Precision-safe serialization for evidence and assumptions.
- Source-cited research report format and structural validation.
- Fundamental valuation primitives, reverse EPS-growth scenarios and weighted terminal-price sensitivity.
- Five portable investment research skills with documented limitations.
- Immutable, linked investment thesis vintages with JSONL import/export and revision comparison.
- Automated linting, unit tests, distribution packaging and CLI smoke validation.

### Explicitly not included
Real-time market data, strategy backtesting, security recommendations, broker execution, regulated services, multi-tenant SaaS, verified forecasts or a hosted web application.

### Important caveat
A structurally valid research record can still contain incorrect prose or biased inputs. Scenario probabilities are not empirically calibrated and return calculations exclude dividends, dilution and costs.
