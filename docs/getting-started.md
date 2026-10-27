# Getting started with InvestIQ (v0.2 core and v0.3 synthetic UI preview)

InvestIQ has an **offline synthetic workflow** and an **opt-in connected issuer-research workflow**. Python 3.11+ is required. No account or key is necessary for offline use.

**What this is not:** The current v0.2.0 source release candidate is developer-oriented CLI software, **not** an integrated LLM research assistant or consumer UI. The [proposed v0.3 Personal AI Research Desk](product/ai-research-experience.md) will be a **locally runnable app** with guided permitted provider/model setup and a no-key synthetic demo; neither interface nor one-time configuration wizard is implemented now. The [complete v0.3→v1.0 open-source roadmap](product/product-roadmap.md) adds peers, explainable scoring, entry scenarios, watchlists, optional portfolio and external packaging through validated increments. See [capability and release acceptance](product/product-roadmap.md) and [initial/external validation](product/validation-plan.md).

## Installation

```bash
git clone https://github.com/jayaprakash87/InvestIQ.git
cd InvestIQ
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
investiq --help
```

For Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` or run the `.venv\Scripts\python` and `.venv\Scripts\investiq` executables directly. A built `0.2.0` wheel can be installed with `python -m pip install dist/investiq_core-0.2.0-py3-none-any.whl` after running `python -m build`.

## Local read-only research preview — v0.3 PR 1

From the installed repository or wheel, run `investiq app` (or `python -m investiq_core app`) and open the printed `http://127.0.0.1:8765/` address. Use `--no-browser` to disable automatic browser launch or `--port 8766` to choose a different port.

The **Run synthetic research** control invokes InvestIQ's existing offline fixture and validator. It renders fictional observations, a structured report, deterministic scenarios and fictional thesis history. The synthetic demo makes **no** provider/model calls.

For **opt-in connected issuer research (PR 2)**, use **Connected research** on that local page:
1. Configure a valid SEC contact User-Agent and your own authorized Twelve Data API key. Credentials are held in this Python server's memory only (not in files, logs or browser storage); remove them using **Disconnect** or by stopping the process.
2. Search a listed company name or ticker. The SEC company directory supplies **candidates** for XNAS and XNYS, not authoritative historical effective listing dates, currency verification, corporate actions or share-class compatibility.
3. Independently check and confirm the selected current listing and proposed USD currency. Set your maximum acceptable price age. Submit to retrieve sourced annual US-GAAP SEC facts and a quoted Twelve Data minute-candle close where your key/venue permits.
4. Inspect explicit source, event time, delay/timeliness classification, staleness, limited fiscal coverage and warnings. Current share-basis confirmation is intentionally unavailable in the browser, so annual P/E is suppressed. All quote snapshot rights default to unknown; the app does not persist connected research.

**Read issuer-document evidence (PR 3):** Confirm a supported issuer in Connected research, then choose Business, Risks or Management discussion under **Inspect annual filing evidence**. The app fetches recent SEC 10-K metadata and a single supported primary filing. It displays at most four bounded excerpts, SEC accession/date/URL and exact excerpt positions in normalized HTML text. **Keyword matches are not identified legal Item sections or validated investment claims.** No document is saved, AI is not involved, and unsupported oversized documents and inaccessible SEC archives yield an explicit error rather than invented narrative. Connected use requires permitted SEC access and a declared contact. Content retrieval is user-triggered.

**Opt-in AI source interpretation (PR 4):** A Twelve Data key is **optional** for SEC company discovery and this AI workflow; it is required only for market quotes. After confirming a company, use **Source-grounded AI research** to configure a private OpenAI API key (stored in the local server session, not in files). Enter a question and select the explicit, per-request consent for transmitting **public SEC excerpt text, annual SEC numeric facts and your question** to the external model. A bounded single request returns structured observations, a counter-thesis, open questions and source IDs; OpenAI API fees and usage/data-retention policies apply. The request explicitly sets `store:false`, disables tools and caps output. Do not enter private portfolio details in the free-text question.

**Research limitations:** Sources may be incomplete, financial facts cover a narrow annual US-GAAP subset, and an apparently relevant citation is *not a verified source-to-claim entailment*. Inspect every claim against the linked original SEC document and independently verify before making decisions. No private quotes, model credentials or saved research are transmitted. The AI output is deliberately **not saved**. It does not provide stock-return predictions, live prices, trade instructions, generic web research or trustworthy multi-sector conclusions.

**Follow-up and scenario interactions (PR 5):** After a successful AI response, click a suggested open question to populate the editable input. This is **a fresh independent question**, not a stateful chat. Review the question and grant **new consent** before submitting each time. Recent question text exists only in the open page; it is not sent as additional context, saved to the server or retained on disk.

To test valuations without a model or quote API, select and confirm a supported issuer and use **Hypothetical scenario workbench**. Enter hypothetical annual positive EPS and entry price (USD/share), a holding period of 1–15 years, and three growth/terminal multiple/weight cases. Weights total 100%. The default growth/multiple/weight numbers are **illustrative, not forecasts**. Results come only from the existing Python financial functions. Crucially, InvestIQ does **not** automatically use an issuer-wide SEC EPS or a Twelve Data price because their class/currency/split comparability is unverified. Only enter a compatible pair of inputs if you have independently assessed it. No quote or model key is required for scenario computation after the company is selected; nothing is saved.

**No independently tested live-provider/model account, secure hosted access, user account, portfolio, broker integration or connected-thesis storage is included.** Quote provider contracts and charges belong to the operator. This preview is loopback HTTP only; do not forward its port, expose it to a network, or run it in a shared untrusted environment. Stop with Ctrl+C.

**Planned later PRs:** cited issuer-document evidence, bounded AI research, interactive valuation, permission-aware private decision storage and complete personal acceptance. The v0.2 developer CLI remains supported.

## Offline synthetic example

```bash
investiq demo --output demo.json
investiq validate demo.json --basis public
investiq validate demo.json --basis recorded
```

The bundle contains fictional issuer observations, explicit assumptions, source-linked reports, valuation scenarios and a hash-linked thesis. A validator result such as `"validation": "structural_only"` **does not** verify a company's actual fundamentals or forecasts.

## Connected one-company research

`investiq research` is optional network access. It needs your authorized `TWELVE_DATA_API_KEY` and a real `INVESTIQ_SEC_USER_AGENT`; specify the **verified** issuer-to-listing source, effective date, ticker, venue/MIC, currency and age policy. Use [the connected CLI guide](methodology/connected-cli.md) for examples, caveats and permissions.

Connected mode shows a source-attributed quote and selected SEC annual facts, with clear freshness/session/missing-data flags. It does not automatically save data, perform currency conversion, claim a real-time feed or recommend securities. Requested annual P/E is withheld unless the required financial context and an independent share-basis confirmation are supplied.

## Private decisions from the local browser — v0.3 PR 6

By default, **no** web decision storage is enabled. Choose a parent folder that already exists, then launch `investiq app --research-dir /your/private/parent/decisions`. The app uses existing create-only, integrity-checked snapshots; on POSIX it creates its private child folder as 0700 and individual revisions as 0600. **On each launch the terminal prints a new private-history unlock code.** Paste it into the **Private local access** form before listing, saving or exporting research. The code is not stored in the browser URL or persisted; disconnecting or restarting requires unlocking again. Keep the terminal private. Another local HTTP client cannot access history with only its own cookie/CSRF token. No cloud account or synchronizer is used. Local machine users or processes with sufficient OS access may still read the data; use disk encryption and backups.

Choose a supported SEC issuer and confirm its current listing and USD currency. Under **Research decisions & revisions**, manually author your thesis and stage, reason, risks and invalidation conditions, then explicitly approve saving. Do **not** paste an AI-generated claim, private account statement, restricted financial-data extract or credential into the editable text. Revisiting a saved version requires no provider key or network connection; the saved content has its own digest and hash-linked ancestry. Export private JSON or Markdown for review, not automatic publishing.

**Important rights boundary:** The browser saves only author-written decision text and, optionally, user-supplied growth/P-E/subjective-weight assumptions and years. It never saves Twelve Data quotes, typed entry-price or EPS values, any AI answer or full SEC filing body. Therefore its **offline replay intentionally cannot recreate numeric price returns**, even when you used the hypothetical workbench earlier. The existing independently rights-gated CLI capture remains available separately for authorized retained public SEC facts. A content hash is not certified historical authorship, strong encryption or independent evidence that a decision was recorded at a claimed market time.

## Explicit research save and offline replay

Use `investiq research ... --save-dir <private-dir> --thesis-id ... --thesis-statement ... --revision-reason ...` to create a private decision **only when requested**. Then run `investiq replay --store-dir <private-dir> --thesis-id ... --revision 1` offline, optionally with `--format markdown` or `--format manifest`.

Market quote prices with UNKNOWN/DENIED snapshot rights—including the current Twelve Data adapter—are **not captured**, and derived prices/valuation are absent in replay. The resulting record still preserves supported SEC public financial facts, authored thesis and eligible assumptions. A GitHub repository is not a private research store.

## Five portable research skills

Read [skills/](../skills/README.md) to use the business-analysis, financial-analysis, valuation-analysis, peer-comparison and thesis-challenge skills. AI-generated prose remains subject to independent source verification; the structural report validator is not a factuality oracle.

## Known limitations and troubleshooting

- `investiq: command not found`: ensure the environment is active or use `python -m investiq_core`.
- Connected-provider errors: check API key, contact User-Agent, subscription/venue permissions, SEC fair access and the explicitly provided CIK/listing metadata. Never paste keys into issues or PRs.
- Stale/unknown quote: increase the age policy **only when analytically justified**, not merely to make a red status disappear; the provider/exchange entitlement remains separate.
- Snapshot save failures: ensure the parent directory exists, your private child directory permissions are suitable and the revision's preceding hash-linked history is present.
- A missing or incompatible EPS does not justify an invented P/E or forecast. US-GAAP annual 10-K support is intentionally narrow.
- Run `ruff check .`, `pytest -q`, and `python -m build --sdist --wheel` to check source quality. No keys/network required for CI.
- The [release acceptance matrix](engineering/release-acceptance-v0.2.md) explicitly separates synthetic automated evidence from manual authorized live-provider verification.

InvestIQ is research software, **not investment advice, a trading service, or permission to retain/redistribute a commercial data feed**.
