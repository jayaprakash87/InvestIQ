# InvestIQ v0.1 Product Scope

## Mission
An open-source, standalone investment research toolkit that makes assumptions, sources, time cutoffs, comparisons and thesis evolution reproducible.

## Intended audiences
Independent researchers, students, educators, financial analysts and software developers. No account, broker, specific data provider or AI model is required.

## v0.1 user journey
1. Install the Python package and run `investiq demo --output demo.json`.
2. Inspect a synthetic research bundle: observations, assumptions, findings and revisions.
3. Validate it using `investiq validate demo.json` with public or recorded basis.
4. Review hypothetical scenario outputs and their assumptions.
5. Reuse five documented research skills and the public Python contracts.

## Capabilities
Deterministic math, source metadata, venue-aware instrument identities, time availability and revision links, structural report validation, linked thesis history, local serialization, CLI and fully offline demo.

## Not yet supported
Live quotes, financial data ingestion, semantic source checking, tailored investment advice, accounts, broker execution, portfolios, performance claims, proper quant backtesting, production web API, hosted UX, authentication, licensing of data or fund management.

## v0.1 release acceptance
Clean Python 3.11 install, successful lint and tests, wheel and sdist building, functional CLI roundtrip from installed wheel, documented method limitations, no private fixtures and an MIT license. This does not imply financial strategy validation.
