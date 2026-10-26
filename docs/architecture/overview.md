# InvestIQ Architecture — Portable Core First

The open-source project is a small modular Python package, not a premature web application or microservice system.

```text
src/investiq_core/
  evidence.py    Numeric observations, sources, assumptions and point-in-time dates
  valuation.py   Pure mathematical scenarios and sensitivity calculations
  research.py    Research report structure and provenance validator
  thesis.py      Hash-linked thesis snapshots, diffs, local JSONL export
  workflow.py    Offline synthetic bundle and integrated structural validator
  cli.py         Thin local interface, no external dependencies
  __main__.py    python -m investiq_core
skills/
  */SKILL.md     Portable model-neutral analysis instructions
tests/           Synthetic deterministic and negative-case regression tests
docs/            Methodology, product scope, architecture, releases
```

## Dependencies
`evidence` and `valuation` provide foundational contracts; `research` and `thesis` depend on evidence; `workflow` orchestrates those modules, and `cli` calls workflow. No model provider, market API, database or brokerage dependency appears in the public v0.1 package.

## Data and trust boundaries
- Observations have source/availability/recorded timestamps, currency, metric, units and source classification.
- Assumptions are a separate class with their own evidence lineage.
- Deterministic validators check structure and timing, not correctness of natural language.
- Valuation inputs are hypothetical and do not constitute real-time market-price facts.
- Hash links detect changes to a thesis chain if a trusted earlier digest is independently preserved; they cannot prove historic authorship.
- Only synthetic fixtures are included. Private research should be stored outside this repository.
- Optional integrations must establish provenance and redistribution rights independently.

## Engineering posture
Lightweight, tested and public reuse first. Add a local persistence adapter and sourced financial-data ingestion only when contracts and license rules are proven. Add a web frontend after a complete research workflow is validated and desired by users.

Architecture decisions are recorded under `docs/decisions/`.
