# Explicit Research Snapshots and Offline Replay — v0.2 PR 5

> **Implemented:** user-triggered immutable local research-decision snapshots, deterministic allowed-input replay and JSON/Markdown outputs. **Not implemented:** provider-entitlement verification, automatic quote retention, connected CLI wizard, hosted workspace/cloud database, encrypted sync, TTM valuations or historical backtesting.

[ADR 0008](../decisions/0008-private-research-snapshots.md) covers architecture, security and licensing tradeoffs. This feature extends, rather than replaces, the original [thesis ledger](thesis-history.md).

## Two deliberately separate views

- **Connected current view:** `ConnectedResearchService.analyze(request)` fetches current entitled provider inputs as of the request. It does **not** save any market data.
- **Saved decision:** the researcher explicitly calls `capture_research_snapshot(result, request, thesis, saved_at=...)`, followed by `LocalSnapshotStore(...).save(snapshot)`. Retained inputs and analyst assumptions are fixed thereafter. `store.load()` and `replay_snapshot()` never call providers.

**Rights gate:** the Twelve Data BYOK quote currently has `MarketDataRights.snapshot=UNKNOWN`. For such a quote, the snapshot intentionally **does not contain its price, quote reference or price-derived P/E and scenario output**. It keeps selected SEC public annual facts, the author's thesis and independent scenario inputs; replay explicitly reports price omission. If a different provider grants quote snapshot rights through its verified source contract, an approved quote may be retained and fully replayed offline. The module alone does not certify any vendor license.

## Using a private snapshot store

```python
from datetime import UTC, datetime
from pathlib import Path
from investiq_core.research_snapshot import (
    REPLAY_METHOD, capture_research_snapshot, replay_snapshot
)
from investiq_core.snapshot_store import (
    LocalSnapshotStore, export_snapshot_json, render_snapshot_markdown
)
from investiq_core.thesis import ThesisSnapshot, ThesisStage

# 'request' and 'result' were obtained through ConnectedResearchService
# as described in connected-research.md. Do not call network providers
# inside the save/replay code.
saved_at = datetime.now(UTC)
thesis = ThesisSnapshot(
    thesis_id="example_decision",
    revision=1,
    instrument=request.listing.instrument,
    as_of=result.observed_at,
    recorded_at=saved_at,
    method_version=REPLAY_METHOD,
    stage=ThesisStage.RESEARCHING,
    statement="Analyst-authored business thesis, not an AI-generated rating",
    revision_reason="Initial explicit research decision",
)
snapshot = capture_research_snapshot(result, request, thesis, saved_at=saved_at)
store = LocalSnapshotStore(Path.home() / "investiq-private-snapshots")
path = store.save(snapshot)  # create-only private JSON, never overwrite
restored = store.load("example_decision", 1)
print(replay_snapshot(restored).annual_pe_proxy)
print(render_snapshot_markdown(restored))
# export_snapshot_json(restored) returns validated JSON text; do not
# publish it publicly without separately reviewing source licenses/privacy.
```

For revision 2 use the same thesis ID, set `revision=2`, make `parent_digest=previous.thesis.digest`, describe the reason for revision, and call save again. The store requires the preceding revision and validates lineage, issuer and timestamp chronology.

**Note:** `as_of=result.observed_at` labels the research cutoff; `saved_at` records when it was actually captured, and must not precede the analysis. The SEC filing-date caveat remains: even a saved annual fact is not verified evidence of the exact moment an SEC filing became public.

## Retained inputs and output policy

| Input | Snapshot treatment |
| --- | --- |
| Thesis, stage, rationale, risks, assumption parameters | Retained locally on explicit save |
| SEC Companyfacts selected annual GAAP values | Retained with fiscal period, filing date, accession and SEC source reference |
| Quote where `snapshot=ALLOWED` | Minimal exact price and source/time context permitted for offline replay |
| Quote where `snapshot=UNKNOWN` or `DENIED` | **No numeric price, quote ID or source reference saved**; price-derived output withheld |
| Provider API keys and entitlement/cache scopes | **Never included** in the structured snapshot |
| Computed annual P/E and scenarios | Regenerated only from retained permissible inputs and saved method/assumptions |
| Full filings, unrestricted price history, news bodies | Not captured |

`export_snapshot_json` produces a versioned JSON manifest plus SHA-256 checksum. `render_snapshot_markdown` renders the saved decision and eligible calculations. Neither is a guaranteed safe-to-publish license grant: user-authored thesis text can be private, and an analyst could personally type restricted source data into free-text fields. Review exports before distributing.

## Storage and failure behavior

The store uses a caller-chosen existing parent directory, creates a private child directory, and writes separate create-only `.json` files. On POSIX, the child directory must be mode 0700 and files mode 0600. Filenames have safe identifiers; symlink destinations are rejected; corrupt/differently named files and hash mismatches fail closed. Saving a revision twice raises `FileExistsError`; a higher revision must point to its direct predecessor's `ThesisSnapshot.digest`.

The local checksum is not a proof of authorship, external timestamp, encryption or tamper-resistant ledger. Users should use OS disk encryption and separately secured backups. Concurrent writers, NFS semantics, Windows ACL policy and shared/multi-tenant workloads require additional assessment.

**Method version:** `connected-annual-pe-v1`. Replay does not query current stock prices and will fail on incompatible future schema/method versions rather than silently producing different historical values. Future methodology changes should provide explicit versioned readers/migrators.

## Test and release gate

```bash
ruff check .
pytest -q
python -m build --sdist --wheel
```

All snapshot tests use synthetic annual facts and quotes and temporary private directories. PR 6 must validate the complete connected-user workflow and the product's available user interface without treating missing licensed quote history as reproducible financial truth.
