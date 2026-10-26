# ADR 0001 — Open-source Python core before applications

Status: Accepted for initial foundation

## Context
InvestIQ targets public reuse and does not yet have a stable investment research domain schema or proven quantitative strategy.

## Decision
Start with a dependency-light Python package, deterministic calculations, versioned methodology, synthetic examples and CI. Keep AI skills, market-data adapters, research storage, strategies and interfaces modular and optional. Do not use personal research records as public fixtures.

## Consequences
Easy offline installation, clear numerical tests and an auditable foundation. Rich UI, live data, brokerage execution and external services are deliberately deferred. Add domain modules based on validated user workflows rather than anticipated architecture.
