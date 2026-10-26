# ADR 0002 — Explicit observation vintages and distinct historical knowledge views

Status: Accepted

## Context
Published financial values, third-party consensus data, and simulated investment forecasts are different kinds of information. Financial data often changes due to restatements and revised estimates. Backtesting against the latest revised values can create look-ahead bias.

## Decision
- Use immutable value objects and Decimal arithmetic for sourced numeric observations.
- Identify a traded security with venue and trading currency in addition to ticker.
- Require source attribution, publication/retrieval timestamps and observation public-availability/recorded timestamps.
- Model researcher assumptions separately.
- Preserve explicit revisions using `supersedes`, never overwrite a historical vintage silently.
- Provide separate queries for *publicly knowable* versus *actually captured* information sets.
- Do not infer vendor permission to redistribute source content.

## Trade-offs
Extra metadata and ingestion work in exchange for reproducibility and defensible time-based analysis. Historic public availability does not establish point-in-time correctness if vendors cannot supply the earlier revision history. This limitation must remain visible until validated on real source systems.

## Rejected
Ticker-only keys; native floating-point currency values; using fiscal period end as release time; conflating reported figures with scenarios; overwriting latest values in place; introducing a database and web service before domain contracts are tested.
