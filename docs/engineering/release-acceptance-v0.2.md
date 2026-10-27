# v0.2.0 — Connected Research Release Acceptance

**Status:** release-candidate acceptance specification for PR 6. **Important:** a green synthetic test suite does **not** certify live provider coverage, market freshness, exchange entitlement, economic correctness or redistribution rights. Tagged publication is handled separately by the existing explicit release-manifest workflow.

## Implementation boundaries

1. **Offline baseline:** `investiq demo` and `investiq validate` remain backward compatible with v0.1.1 research bundles.
2. **Connected read:** `investiq research` requires the user's explicit SEC CIK, ticker, venue, currency, independent listing reference and effective date, and maximum quote age. Credentials come only from environment variables. No implicit price/issuer lookup and no automatic save.
3. **Source correctness:** SEC annual US-GAAP facts retain filing date/accession and avoid fake intraday publication times. Twelve Data one-minute CLOSE validates symbol, MIC, currency and event timestamp. Declared source timeliness is UNKNOWN; freshness is a distinct caller-policy result.
4. **Financial safeguards:** no implied FX, no TTM/forward earnings, no calculation for nonpositive EPS, missing share-basis confirmation or stale quotes; scenario assumptions only when deliberately supplied via Python API.
5. **Save/replay:** private create-only snapshots require explicit user save intent. When quote snapshot rights are UNKNOWN/DENIED, **no quote price or price-derived valuation** is retained; offline replay never queries today's feed.
6. **Fault and threat behavior:** malformed HTTP, truncated responses, excessive payloads, 429 Retry-After (including HTTP dates), missing permissions, wrong identity and invalid evidence fail closed; safe exceptions avoid credential-bearing URLs. A local SHA-256 hash detects corruption but does not provide trusted historical attestation.

## Automated release gate

| Gate | How | Expected |
| --- | --- | --- |
| Code quality | `ruff check .` | Zero violations |
| Full synthetic suite | `pytest -q` | All tests passing, no API credentials or network |
| End-to-end adapters | `tests/test_release_acceptance.py` | Fake HTTP -> real SEC/quote parsers -> connected analysis -> explicit private save -> offline CLI replay |
| Rights isolation | Same synthetic workflow | UNKNOWN quote's price/ID/source never reaches the saved manifest or Markdown |
| Failure handling | Acceptance + provider tests | Bad MIC, unauthorized data, stale data and unsupported paths fail or warn explicitly |
| Legacy | CLI demo and validator smoke | Existing v0.1 JSON bundle remains valid |
| Build | `python -m build --sdist --wheel` | Both distributions valid |
| Installed CLI | Wheel reinstall, `investiq demo`, `validate`, `research --help`, `replay --help` | No keys, no network calls to display help |
| Review | Codex review on latest PR head | No unresolved findings |
| Main integration | CI on merge commit | All above gates pass |

**Release automation:** bump `pyproject.toml` to **0.2.0** and include changelog/release notes. **Do not add `.release/v0.2.0.json` to this implementation PR**, because merging that file triggers a *public tag and artifact publication*. The manifest should be added only in a separate, consciously approved publication PR after live/manual gating.

## Manual provider smoke — opt-in only

Prerequisites: actual **personal/authorized** Twelve Data subscription/API key, real SEC contact User-Agent, verified US issuer CIK ↔ security/MIC/share class mapping and active provider/exchange entitlement. Never use paid or personal market data in GitHub Actions or fixtures.

1. Read [connected CLI instructions](../methodology/connected-cli.md). Check the user's provider plan supports `/quote?interval=1min` and the selected venue; confirm the right to *view* that data.
2. On a trusted local machine, configure `TWELVE_DATA_API_KEY` and `INVESTIQ_SEC_USER_AGENT` securely, run one `investiq research` request with a validated issuer instrument, and independently compare MIC, currency, timestamp, price kind and source-reported session/timeliness against the vendor response.
3. Test an invalid/unsupported listing, missing entitlement and rate-limited outcome in a way that does not violate provider fair-access requirements. Observe typed, sanitized failures and no hidden venue downgrade.
4. Repeat around market close or with an intentionally strict freshness policy and confirm stale/closed data is **never labeled live**.
5. Explicitly save a private thesis, verify a Twelve Data price with UNKNOWN snapshot rights is absent from the created file, delete API variables, then replay the decision. Validate that the snapshot contains only permitted public annual facts and thesis content.
6. Verify a different, **legally retainable** quote only if an actual source provides explicit snapshot rights (and exchange reuse rights as applicable). Absent permission, this remains a synthetic-only test.
7. Inspect release notes, environment/setup documentation, GitHub Actions status, packaging metadata and dependency/security concerns. Record date, ticker/MIC, provider plan tier and observed limitations **without storing keys or restricted market data**.

**No claim that this manual smoke was performed:** it requires user-held credentials, independent licensing confirmation and a trusted real machine.

## Outstanding risks and post-v0.2 backlog

- BYOK provider/exchange access, real-time authorization, contract changes, quote normalization and coverage not live-verified here.
- SEC Companyfacts annual selected GAAP tags only; no quarterly/TTM, IFRS, restatement-complete historical vintages or full audited financial-report reconstruction.
- CLI performs one connected issuer study with manually provided CIK-to-listing mapping and a simple optional save; no browsing/search, portfolio, scheduling or hosted UI.
- Current quote available in CLI output is not automatically permissible to **store** or redistribute. Price-based snapshot replay unavailable for Twelve Data under UNKNOWN rights.
- Local snapshot store not encrypted, independently time-attested, multi-writer or cloud-distributed.
- No economic backtest, audited stock recommendation model or AI forecasting/LLM factuality evaluation (AI remains structured prompts/skills).

## Decision

Treat v0.2.0 as **code-complete release candidate once latest-head and merged-main checks pass**. Public/tagged release needs explicit authorization and the separate release-manifest step, plus manual provider/license acceptance where a claim of actual live-provider support is desired.
