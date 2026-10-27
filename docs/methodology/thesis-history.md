# Immutable Thesis History — Research Ledger v0.1

## Goal
Allow researchers to preserve *what was actually concluded, using which evidence and hypotheses, and under which version of the methodology*. This is an open-source mechanism, not a personal portfolio database or record of investment orders.

## Core concepts
- `thesis_id` is a stable research-thesis identity, `revision` begins at 1, and the `instrument` is venue-qualified.
- `as_of` is the latest information date the thesis claims to use. It is **not** proof the thesis existed then.
- `recorded_at` is the actual creation/storage timestamp for the snapshot. A reconstruction using today's data must not be passed off as an original decision.
- `method_version` identifies the applicable research approach.
- `stage` is a neutral research state: researching, watching, challenged, archived.
- `evidence_ids` and `assumption_ids` identify independently retained source objects, without embedding licensed datasets in public code.
- `invalidation_triggers` identify falsifiable conditions for a thesis; `risks` preserve potential disconfirming mechanisms.
- Each revision links the prior snapshot with `parent_digest` (SHA-256 of canonical JSON), and `revision_reason` explains why the thesis changed.

## Usage
```python
from dataclasses import replace
from investiq_core.thesis import (
    ThesisSnapshot, ThesisStage, validate_thesis_history,
    compare_thesis_revisions, export_thesis_jsonl, import_thesis_jsonl,
)

# Build snapshot v1 with a synthetic InstrumentId and attributed source IDs.
# Then create revision v2 referencing v1.digest as parent_digest.
# Validate [v1, v2] with evidence and assumptions before exporting:
# validate_thesis_history([v1, v2], evidence=[...], assumptions=[...])
# serialized = export_thesis_jsonl([v1, v2])
# restored = import_thesis_jsonl(serialized)
```

Run `pytest -q tests/test_thesis.py` to inspect complete executable synthetic examples.

## Guardrails
- No overwrite-in-place API: earlier snapshots remain unchanged; comparisons verify direct ancestry.
- Research evidence and source dates are checked at each snapshot's `as_of`.
- Assumption support is checked for availability **when the assumption was created**.
- For research captured in a specific dataset, `basis="recorded"` enforces recording timestamps; public-only availability is weaker.
- Missing evidence, mismatched instruments, broken digest chains and backward-moving chronology fail validation.
- JSONL is a portable **serialization format**, not a secure or transactional multi-writer database. Do not commit private copies to the public repository.
- A content hash catches accidental or unsanctioned revisions **when earlier trusted digests are retained separately**. Anyone able to rewrite the entire chain can recalculate all hashes. This is not a cryptographic attestation of past investment decisions.
- The ledger does not verify semantic accuracy or reconstruct erased historical market-data vintages. Never advertise historic accuracy without independently timestamped evidence.

## Connected-research extension (v0.2 PR 5)

The [private research snapshot workflow](research-snapshots.md) now reuses `ThesisSnapshot` history with an explicit, rights-gated connected input manifest and a create-only local JSON store. This is a distinct retained-analysis layer; the core thesis ledger is unchanged. Restricted quote prices are **not** persisted, and missing retention permission means the price-based valuation cannot be replayed numerically. No externally signed time attestations or general historical backtest claims are provided.

## Deferred
Encryption/sync, multi-writer transactions, shared/cloud stores, arbitrary provider-retention licensing, schema migration across methodology versions, portfolios and automated trading.
