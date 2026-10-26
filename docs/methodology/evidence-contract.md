# Research Evidence and Point-in-Time Contract v0.1

**Scope:** generic, public equity research; no client accounts, private positions, securities recommendations, vendor price feeds, or strategy results.

## Identification
Identify instruments by `(ticker, ISO 10383 venue MIC, trading currency)`; bare ticker alone is ambiguous and historical symbol changes still require an explicit mapping layer in a later PR. The identifier is an instrument key, **not** a stable corporate-entity identifier.

## Numeric values and units
Use exact finite decimal values. In JSON, decimal values are strings to prevent binary floating-point rounding. Monetary and per-share amounts require a three-letter currency. Ratios are fractions: `"0.15"` means 15%, not `"15"`. Currency conversion requires an independently attributed, date-consistent exchange rate; the research model must not silently convert currencies.

Observations have an explicit kind: `reported`, `consensus`, `estimate`, or `derived`. This origin label is not a claim that the input is accurate or permitted to redistribute. Hypotheses belong to a separate `ResearchAssumption` record rather than being represented as sourced observations.

## Temporal axes
- `effective_at`: the economic instant described by a point observation, or reference instant of a reported period.
- `period_start`/`period_end`: optional fiscal coverage; supply both or neither.
- `source.published_at`: source's release timestamp, when verified.
- `publicly_available_at`: earliest verified public availability of this particular *vintage* of the observation.
- `source.retrieved_at`: actual time the source was fetched.
- `recorded_at`: actual time InvestIQ stored this particular observation.

All timestamps must have a timezone. Never substitute period end for release date. Date-only financial statements need an explicitly documented publication-time convention in ingestion adapters; do not assume midnight implies public availability.

## As-of query semantics
`observations_as_of(..., basis="public")` filters by observed public availability and is a *potential historical information-set* view. It may show publicly available history retrieved into the system later. This alone **does not prove** that a source preserved original historic revisions.

`basis="recorded"` additionally limits to observations recorded in the dataset by cutoff: useful for replaying an actual append-only research log.

`supersedes` explicitly identifies a new vintage of a prior observation. Only a revision already visible at cutoff can hide its older version. Incompatible, unlinked revisions are not automatically deduplicated. Unique IDs and acyclic revision chains are required within a query.

## Evidence and copyright
Every observation references a publisher, source reference and retrieval time. When available, include an absolute source URL and publication time. Source redistribution permission is `unknown` unless verified. Public repositories must not commit paid datasets, client portfolios or copyrighted research beyond the applicable license. Synthetic fixtures are safe examples, not evidence of financial performance.

## Limitations and extension points
This v0.1 contract covers finite numeric observations. It deliberately does not yet solve corporate actions, instrument lineage, fiscal calendar comparability, restated statements without historical vintages, vendor-specific symbol mappings, account holdings, continuous real-time quotes, source authentication, or investment performance. These require explicit later designs and tests before historic backtesting or live-market use.

## Example
```python
from datetime import datetime, timezone
from decimal import Decimal
from investiq_core.evidence import (
    InstrumentId, EvidenceSource, FinancialObservation, ValueUnit, ObservationKind
)

utc = timezone.utc
source = EvidenceSource(
    reference="synthetic:example-v1",
    publisher="Synthetic test dataset",
    published_at=datetime(2025, 3, 1, 12, tzinfo=utc),
    retrieved_at=datetime(2025, 3, 2, 12, tzinfo=utc),
)
observation = FinancialObservation(
    observation_id="synthetic:revenue:v1",
    instrument=InstrumentId("TEST", "XNAS", "USD"),
    metric="revenue", value=Decimal("125.50"),
    unit=ValueUnit.MONEY, currency="USD", kind=ObservationKind.REPORTED,
    source=source,
    effective_at=datetime(2024, 12, 31, 12, tzinfo=utc),
    publicly_available_at=datetime(2025, 3, 1, 12, tzinfo=utc),
    recorded_at=datetime(2025, 3, 2, 13, tzinfo=utc),
)
assert observation.to_record()["value"] == "125.50"
```
