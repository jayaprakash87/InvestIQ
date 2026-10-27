## Outcome and user value
What behavior or documented engineering decision changes? Why now?

## Architecture and data
- [ ] Respects [Engineering Blueprint](../docs/engineering/engineering-blueprint.md) or explains a documented exception
- [ ] Contracts, financial units, source/time semantics, provider entitlement and versioning addressed where applicable
- [ ] No speculative scaffolding, unjustified dependency or unrelated refactor

## Evidence and tests
- [ ] Deterministic tests and negative/boundary cases added where behavior changes, or docs-only rationale provided
- [ ] Existing lint, tests, distribution build and installed CLI checks pass
- [ ] New applicable capability gates (provider/API/frontend/AI) are run **only if implemented**
- [ ] User-facing errors, freshness, accessibility and recovery states considered when relevant

## Safety, privacy, licensing
- [ ] No secret, private position, identifying user data or unlicensed market-data dump
- [ ] No invented live-data status, fabricated inputs, unsupported return promises or AI-certified claims
- [ ] External content and cache/license/entitlement risks handled when applicable

## Documentation and release
- [ ] Docs and examples updated; ADR for durable decisions where warranted
- [ ] API/schema compatibility, migration/rollback and release notes considered
- [ ] Material review comments resolved; exceptions approved with rationale
