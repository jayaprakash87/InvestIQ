# v0.2.0 connected research CLI — BYOK, optional save and offline replay

The CLI now offers **two separate workflows** alongside the existing `demo` and `validate` commands. `research` explicitly connects to the SEC and Twelve Data; `replay` reads only a previously saved private decision. Neither command guesses symbol-to-issuer mapping or grants data rights.

## 1. Opt-in connected current view

Set a real contact User-Agent required by SEC and an individually licensed Twelve Data API key. **Do not commit these values, include a key on the command line, or put it into the source repository.**

```bash
export INVESTIQ_SEC_USER_AGENT="Researcher YourRealContact@example.org"
export TWELVE_DATA_API_KEY="your-own-authorized-key"
investiq research \
  --symbol AAPL --venue XNAS --currency USD --cik 320193 \
  --listing-source "your-independent-company-listing-reference" \
  --listing-from 2020-01-01 --max-age-minutes 30
```

Windows PowerShell uses `$env:INVESTIQ_SEC_USER_AGENT = "Researcher YourRealContact@example.org"` and `$env:TWELVE_DATA_API_KEY = "your-own-authorized-key"`. These placeholders are **not** valid credentials. The listing reference and effective date are **researcher-supplied assertions**; InvestIQ does not independently verify CIK-to-listed-share-class identity. Replace them with a genuinely checked source/effective date before performing actual research.

Output is JSON describing the **current viewed** quote (exact price, original market-event timestamp, receipt time, source, session, declared timeliness, age-policy result and source snapshot permission), available annual SEC facts with fiscal periods/accessions and a list of data-quality warnings. The program does **not** write any file or snapshot by default.

The `--max-age-minutes` policy is required, not guessed by InvestIQ; it is **not** proof of a live feed, permitted exchange access or an appropriate trading/session TTL. A quote may be stale or `timeliness=unknown` even if retrieved now. The price is a `CLOSE` of a one-minute provider bar, not a trade tick. Annual EPS is not TTM or a forecast.

### Optional P/E eligibility (researcher attestation)

```bash
investiq research \
  --symbol AAPL --venue XNAS --currency USD --cik 320193 \
  --listing-source "your-independent-company-listing-reference" \
  --listing-from 2020-01-01 --max-age-minutes 30 \
  --confirm-share-basis \
  --basis-rationale "I independently checked this share class and the quote/EPS split basis"
```

Only use these flags after confirming share-class comparability. InvestIQ cannot infer or verify that confirmation. Nonpositive or absent annual diluted EPS, incompatible currency or fiscal timing, and stale quotes suppress the annual P/E proxy. A returned ratio is **price / last reported annual diluted EPS**, not forward P/E or a target.

## 2. Explicitly save a private decision

Append `--save-dir`, `--thesis-id`, `--thesis-statement` and `--revision-reason` to an authorized `research` command. For example:

```bash
investiq research \
  --symbol AAPL --venue XNAS --currency USD --cik 320193 \
  --listing-source "your-independent-company-listing-reference" \
  --listing-from 2020-01-01 --max-age-minutes 30 \
  --save-dir ./investiq-private-snapshots \
  --thesis-id research_AAPL --revision 1 \
  --thesis-statement "My independently authored research hypothesis" \
  --revision-reason "Initial analysis"
```

The designated **parent** directory must already exist. On POSIX, InvestIQ creates a private child directory (0700) and writes revision-specific create-only files (0600). The user controls encryption, privacy, backups and export/redistribution permissions; this is not a multi-user service. The local digest is a corruption detector, not a trusted timestamp or signature.

**Critical:** Twelve Data's current adapter returns `MarketDataRights.snapshot=UNKNOWN`. Therefore, this command **will not save that provider's price, quote ID/source reference or any price-derived valuation**. It saves selected public SEC annual facts and user-authored thesis information. The JSON response to the connected `research` command can still **display** the current entitled quote; redirecting that response into a file is a user-controlled action potentially subject to provider license restrictions.

To create revision 2 or later, supply the same `--thesis-id` and `--revision 2` (or 3 etc.). The store loads and checks the previous hash-linked thesis chain and refuses overwrites.

## 3. Replay offline with no credentials

```bash
unset TWELVE_DATA_API_KEY
unset INVESTIQ_SEC_USER_AGENT
investiq replay --store-dir ./investiq-private-snapshots \
  --thesis-id research_AAPL --revision 1
investiq replay --store-dir ./investiq-private-snapshots \
  --thesis-id research_AAPL --revision 1 --format markdown
investiq replay --store-dir ./investiq-private-snapshots \
  --thesis-id research_AAPL --revision 1 --format manifest
```

These are **offline**. `summary` (default) returns a minimal JSON replay result; `markdown` gives the human-readable captured thesis and eligible facts/valuation; `manifest` exports the original versioned JSON with its SHA-256 integrity digest. With snapshot rights unavailable, replay deliberately shows **no historical price/P-E** rather than using today's quote.

The Python API additionally supports explicit researcher-authored scenarios, which this first CLI entry point does **not** expose. See [connected analysis](connected-research.md), [private snapshots](research-snapshots.md) and [ADR 0008](../decisions/0008-private-research-snapshots.md).

## 4. Failure modes and truthful limitations

- Missing environment variables or issuer/listing arguments: fail **before** contacting a provider.
- Unknown or unsupported listing MIC, wrong currency, unavailable vendor plan, invalid quote or SEC facts: explicit provider failure, not a substitute or fabricated estimate.
- SEC's public Companyfacts endpoint contains annual US-GAAP data from selected 10-K/10-K/A tags, not a complete comparable-income-statement or exact intraday public-availability feed. Same-day filing facts are conservatively withheld.
- The user is responsible for SEC declared contact/fair-access behavior and the specific Twelve Data contract, entitlements and exchange rights.
- Offline synthetic CI tests exercise these code paths with actual adapters and mocked HTTP; **no authorized real-provider end-to-end smoke has been performed by CI.** See the [release acceptance and manual smoke checklist](../engineering/release-acceptance-v0.2.md).
- No brokerage actions, personal portfolio management, cloud hosting, market-wide coverage, unrestricted snapshot retention, verified real-time feed or investment advice are included.
