# Changelog

The software is under active development. The public API may evolve; use versioned research bundles.

## [0.2.0] — source release candidate (2026-10-27)

Connected Company Research vertical slice: SEC EDGAR/Companyfacts and Twelve Data BYOK provider adapters, explicit instrument/issuer contracts, freshness/entitlement metadata, conservative annual financial analysis and P/E eligibility, researcher-authored scenario assumptions, private rights-gated snapshots and deterministic offline replay.

Added an opt-in connected `investiq research` command and an offline `investiq replay` command. Existing synthetic demo/validate remain compatible. New synthetic end-to-end adapters/CLI/replay acceptance; bounded no-redirect HTTPS, sanitized errors and precise Decimal computations.

**No automatic public GitHub release or package-index publication from this change.** The v0.2.0 source version and notes are prepared; actual publication still requires an explicit release-intent manifest after manual acceptance.

**Not included:** verified real-time exchange feed, unlimited cache/snapshot license, historic backtest, cloud/hosted UI, public company search, quarterly/TTM finance normalization or stock recommendations. No live-provider credentials used in CI.

## [0.1.1] — 2026-10-26

Maintenance release improving provenance validation and safe, repeatable release publication.

### Fixed
- Verify the cited financial support for a valuation-only growth assumption, even when that hypothesis is not present in the narrative report or thesis; enforce evidence identity, instrument and historical availability.
- Verify that an existing remote release tag points to the exact tested source commit before uploading artifacts, especially when recovering an incomplete release.

### Compatibility
The JSON bundle format remains `schema_version: "0.1"`. No account, brokerage or live-data integration has been added.

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
