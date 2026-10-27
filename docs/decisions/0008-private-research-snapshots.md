# ADR 0008 — Explicit, rights-aware research decision snapshots

**Status:** Accepted for v0.2 PR 5 · 2026-10-27  
**Depends on:** [ADR 0003](0003-connected-data-and-research-history.md), [ADR 0006](0006-connected-data-service.md), [ADR 0007](0007-connected-research-analysis.md).

## Decision

Implement an **explicit user-triggered capture → append-only local store → offline replay** workflow, using the existing `ThesisSnapshot` hash-linked revision lineage and a new immutable `ResearchSnapshot` input manifest. Preserve a strict boundary between today's connected source view and a saved decision. Never automatically save market data when refreshing research.

### Record and reproduction

- The snapshot records researcher-authored thesis, revision rationale, status, market instrument and SEC issuer, method/schema version, exact researched/saved timestamps, selected source-attributed annual SEC facts and the exact user-provided scenario inputs and share-basis confirmation.
- Only **SEC Companyfacts US-GAAP facts** with a recognized original SEC reference and matching CIK may be retained by the initial implementation. General licensed fundamentals and news/estimates require their own rights contracts; raw Companyfacts responses are not dumped into the repository or file store.
- A quote is captured **only when the source record expressly grants `MarketDataRights.snapshot=ALLOWED`**. Otherwise price, quote source reference and every price-based valuation remain absent in the stored JSON, Markdown and offline replay. We deliberately favor incomplete-but-lawful replay over a seemingly complete record of unlicensed data.
- For a permitted quote, store a minimal exact-Decimal price, source reference, quote kind/currency, event/receipt time, original market session, source-declared timeliness and freshness classification **at capture**. Do **not** persist provider API keys, cache entitlement scope or user credentials. Captured values never become current/live by replay.
- Reconstruct the reported-annual P/E proxy and optional user-supplied scenarios from retained inputs **without network calls or current clocks**, using a declared immutable method identifier `connected-annual-pe-v1`. Missing/nonpositive EPS, currency mismatch, unconfirmed share-class/split basis, quote time predating filings or nonfresh captured prices withhold valuation. Scenario probabilities are hypotheses, never calibrated likelihoods. Unsupported schema/method versions fail rather than silently change old interpretations.
- The connected analysis is a **current-information view** and may change on the next provider call. Creating a saved thesis is a separate explicit action. We do not assert that a `ThesisSnapshot.as_of` value proves the thesis was authored then: recording time is the actual capture time, and hash chains are not externally signed evidence.

### Local private storage

- Default storage is **opt-in local filesystem**, not an automatically created cloud workspace. The caller explicitly chooses a directory and calls `LocalSnapshotStore.save(snapshot)`. The store creates a private directory (POSIX mode 0700), writes immutable regular JSON files (0600) using a same-directory temporary file, file flush and an atomic create-only hard link. It refuses overwrites, unsafe thesis identifiers, path symlinks and insecure existing file/directory permissions.
- One version per file: `thesis_id-00000001.json`, `thesis_id-00000002.json`. Revision 2+ must follow the prior `ThesisSnapshot.digest`; all earlier records remain intact. No automatic rewrite of earlier snapshots on market refresh. A JSON envelope includes a canonical SHA-256 digest over its payload and is checked on load, together with format, identity and offline computation validation.
- The hash detects corruption and makes accidental modifications observable; a local adversary with write permissions can rewrite/recompute an entire chain. It is **not** an external timestamp authority, a digital signature, encrypted-at-rest storage, legally certified record or multi-user concurrent transaction database.
- No remote synchronization, hosted identity or privileged reusable cache is introduced. Parent-directory symlink defenses and OS permissions vary by platform; shared-machine use needs separate threat-model review, and users remain responsible for disk encryption and backups.

### Exports

- `export_snapshot_json` gives the exact input manifest + checksum; `import_snapshot_json` verifies it before constructing data objects. The JSON parser rejects duplicate keys, malformed envelope and nonfinite values; input and file sizes are bounded. Unrecognized schema/method versions fail explicitly.
- `render_snapshot_markdown` produces a readable, offline report with source dates, decision text, retained facts and eligible calculated outputs. It excludes restricted quote prices. It escapes HTML and basic Markdown delimiters in researcher-authored strings.
- No new CLI/web dashboard is required for PR 5. This is a reusable Python application capability; a product-facing connected CLI UX belongs to v0.2 PR 6 acceptance/polish.

## Options rejected

- Automatically write every quote whenever the user requests research — violates source rights and conflates current vs historic views.
- Store price or precomputed price-derived P/E when `rights.snapshot` is UNKNOWN/DENIED — would leak licensed numerical data through another field.
- Store only a price reference but claim exact numeric replay — no reproducible numeric price without a retained lawful input.
- Use SQLite/cloud/Redis by default — no demonstrated need for infrastructure at this release stage.
- Duplicate the existing thesis lineage system — creates ambiguous source of truth.
- Implicitly recompute historical results with today's prices or a changed calculation method — fundamentally breaks decision reproducibility.
- Promise encryption, legal immutability or proof of record creation from local SHA-256 alone.

## Verification and limits

Synthetic tests verify explicit ALLOWED vs DENIED/UNKNOWN rights, omitting restricted prices across JSON/Markdown/replay, deterministic permitted replay, repeated saves, revision ancestry, secret-bearing references, source CIK enforcement, corrupted/duplicated JSON, private permissions and symlink refusal. Tests do not contact external providers.

**Not a complete replay for sources with disallowed snapshot rights.** Such records preserve the legally retainable SEC facts, thesis and scenario assumptions but intentionally lack historical price-based calculations. A user must secure appropriate source rights or use separately legitimate price inputs before declaring a numerically reproducible price thesis.

**Next:** v0.2 PR 6 — end-to-end acceptance, real-provider smoke with authorized credentials (opt-in), coherent connected CLI UX, release packaging and documented gaps.
