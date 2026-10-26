# Architecture — Modular Monolith First

## Dependency direction
- `src/investiq_core`: pure Python financial calculations; no AI, web, credentials, external services or database.
- Future adapters for data providers and normalization: version source metadata and as-of timestamps.
- Future research engine: typed facts, assumptions, evidence and thesis records.
- Future skills: portable instructions with structured input/output validated by shared domain schemas.
- Future quant module: separate portfolio simulations with point-in-time checks and explicit transaction costs.
- Future CLI/API/UI: thin interfaces to underlying domain services, not sources of business logic.

Start with a Python package and CI, not placeholder microservices or a heavy application stack. Add storage only when decision-history requirements are established; add a web app only when a working research workflow exists.

## Data contracts
Always distinguish observed facts, sourced estimates, user hypotheses and computed values. Missing is not zero. Do not silently fill missing data or treat an LLM output as a primary source.

## Security and openness
No credentials in code or test data; prohibit real user positions and personal details in public fixtures; include license and provenance review when integrating external market data. Public software does not imply free redistribution rights to vendor datasets.

## Architecture decisions
Document decisions affecting public semantics in `docs/decisions/`, with rationale and rejected alternatives.
