# Portable Research Report Contract v0.1

InvestIQ research skills share a stable, model-agnostic JSON representation. All fields represent research *claims* or source references, **not** certified truths.

## Structure
```json
{
  "skill": "financial-analysis",
  "as_of": "2025-03-15T12:00:00+00:00",
  "subjects": [
    {"ticker": "DEMO", "venue": "XNAS", "trading_currency": "USD"}
  ],
  "findings": [
    {
      "finding_id": "finding-1",
      "kind": "reported_fact",
      "text": "Synthetic example revenue was 125.50 USD.",
      "evidence_ids": ["synthetic:revenue:q4"],
      "assumption_ids": []
    },
    {
      "finding_id": "finding-2",
      "kind": "data_gap",
      "text": "Comparable cash-flow information was not provided.",
      "evidence_ids": [],
      "assumption_ids": []
    }
  ],
  "questions": ["What was the operating cash flow for the same period?"]
}
```

## Finding classifications
- `reported_fact`: cite only observations explicitly marked `reported` and no hypotheses.
- `external_estimate`: cite only externally sourced `consensus` or `estimate` observations.
- `assumption`: cite hypothesis IDs, not financial observations; assumptions are not actual data.
- `inference`: cite relevant observation and/or assumption IDs; arithmetic must be externally calculated and verified.
- `data_gap`: a self-contained description of missing information; no fabricated substantiation.

Each finding and citation ID must be unique where uniqueness is required. The report references venue-qualified instruments and a timezone-aware `as_of` cutoff. Peer comparisons require at least two subjects.

## Historical views and failure rules
`validate_research_report` verifies that cited input IDs exist, belong to subjects, and were publicly available by the cutoff. With `basis="recorded"` it also requires records to have been captured by then. It rejects missing references, later assumptions, incorrect fact/estimate classifications, and duplicated IDs. These checks do not replace the underlying financial evidence/revision validation.

## Critical limitation
**Passing this validator does not prove that the text is correct, faithful to its cited sources, comprehensive, or accurate financial analysis.** Inference quality and ungrounded language must be assessed with independent source review and future model evaluations. This contract intentionally does not imply direct brokerage suitability or investment advice.

The `examples/synthetic_research_bundle.json` file contains a complete public, fictional report and source observation. Load it with `FinancialObservation.from_record` and `ResearchReport.from_record`.

## Versioning
The wire schema is experimental v0.1. Breaking field changes require a new documented contract revision and migration notes.
