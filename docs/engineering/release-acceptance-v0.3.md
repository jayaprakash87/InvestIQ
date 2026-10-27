# InvestIQ v0.3 — Personal Research Desk Release Acceptance

> **Status:** Release-acceptance gate for v0.3 PR 7; **not** a production-readiness certificate or approval to tag/publish.  
> **Evaluation basis:** Source code and automated offline/injected-port tests. Check the latest PR-head and merged-`main` CI runs before asserting automated gates passed.  
> **Scope:** First sector-neutral local investor research loop with limited US SEC issuer evidence, optional BYOK providers and explicit private decisions.

## Release decision: split engineering completion from independently verified operation

A fully green offline suite qualifies a **local personal-alpha / engineering milestone**, not a real-market research release. The v0.3 capability exists in the repository but the installed package still declares version `0.2.0` until explicit release/version approval. Do **not** add a public release manifest or tag as part of PR 7.

- **Engineering gate:** Build, installed CLI, local HTML/CSS/JS asset delivery, session-protected HTTP workflow, injected provider/model boundaries, bounded math, private snapshot integrity and no-key synthetic demonstration.
- **Live-provider gate (outstanding unless independently recorded):** Real SEC directory, accepted contact User-Agent, at least one real filing document and Companyfacts response; a personally authorized Twelve Data quote/entitlement if exercising priced analysis; user-authorized OpenAI Responses account with supported model and fees/terms understood.
- **Investment-quality gate (outstanding):** An investor checks claims against actual filings, quote timestamp/venue/rights and assumptions, records missing evidence, compares same task to existing research workflow, and verifies that the bear case is meaningful rather than plausible-sounding invented analysis.
- **Product gate (outstanding):** Manual keyboard/screen-reader/accessibility testing, supported OS fresh install, first-use setup without developer handholding, usability observation and corrections. Automated syntax/tests alone cannot certify accessibility.
- **Publication gate (separate approval):** Licensing/redistribution and retention rights, dependency/security review, published release notes, explicit version/tag/manifest and distribution authorization.

## Automated release acceptance matrix

| Requirement | Verification | What a passing test establishes | What it cannot establish |
| --- | --- | --- | --- |
| Offline entry without credentials | `investiq demo`, `validate`, local `/api/v1/demo` | Fictional bundled fixture and validator work without network or persistence | Real-company coverage |
| Protected local app | Existing local app HTTP/security tests and `test_v03_release_acceptance.py` | IPv4 loopback, Host/Origin/CSRF/session guards on accepted fixtures; unauthorized requests fail | Shared-user OS isolation, browser security certification |
| Company selection | Injected SEC directory + controller E2E | User must select/confirm matching CIK, symbol, MIC and USD; invalid CIK rejected | SEC candidate is an exchange-verified historical security |
| Source inspection | Injected 10-K passage provider | Source accession/URL and bounded excerpts displayed through the app boundary | Correct HTML parsing on all live filings or verified narrative entailment |
| AI orchestration | Real AI coordinator with fake bounded model, source validator, negative tests | Consent mandatory; unsupported IDs and malformed model outputs fail; model inputs do not contain a quote/key/history | Correct investment conclusions, actual OpenAI terms or real API compatibility |
| Follow-up | Two independent consented AI HTTP requests | No previous prompt or AI response forwarded implicitly | Truthfulness or usefulness of follow-up |
| Scenarios | `interactive_scenarios` and HTTP integrated tests | Python-core numeric computation from user-entered assumptions, explicit weights, no quote or model request | Suitable share class/split/EPS economics, statistical probability, future returns |
| History / replay | Real private `LocalSnapshotStore`, HTTP acceptance and CLI replay tests | Explicit create-only snapshot, hash-linked revisions, offline reopen/export and omission of unapproved price/AI input | Encrypted storage, externally trusted timestamps, replay of omitted historical prices |
| Python/UI packaging | Build and installed-wheel smoke | Package contains executable and browser assets | Cross-platform fresh-install experience |
| Static frontend | `node --check`, HTTP asset tests, event guard unit/static tests | JS parses and files are served | WCAG conformance, keyboard/screen-reader usability |
| Error recovery | Provider, model, source and store fail-closed tests | Known bad identities/data, malformed output, privacy/permissions errors are reported safely | Every real network/provider failure mode |

**Hard release stop:** Unattributed or fabricated facts presented as verified; live/delayed price mislabeling; invalid share-basis valuation represented as factual; saving restricted market data; secret leakage; unexpected model submission; unsupported claims of replaying omitted prices; credential exposure in Git, tests, exported data or CI logs.

## Complete synthetic acceptance journey

The executable `tests/test_v03_release_acceptance.py` starts a **real loopback HTTP server** with a real session/controller, a real AI coordinator/citation validator, deterministic financial core and private snapshot store. Only SEC-directory, filing, annual-fact and model **I/O** are injected with fictional fixtures. It checks:

1. The offline demo loads without accounts, costs or saved files.
2. Public SEC company discovery requires contact/session setup and selected issuer confirmation.
3. An eligible fictional 10-K excerpt can be inspected; a quote request fails without an authorized market-data key.
4. AI analysis requires a separately configured model and **explicit consent**. The response links only existing fixture source IDs. A follow-up sends neither prior answer nor chat history.
5. Manually entered hypothetical values are validated and computed by the existing Python method, with no model or quote request.
6. Research remains unsaved until the investor **explicitly** authors and approves a private decision. The saved manifest excludes API keys, AI text, full SEC documents, price, user-entered EPS/entry price and price-derived values.
7. The saved thesis reopens and exports **offline** after clearing provider credentials. Wrong origins, cookies, CSRF, issuer IDs and unsafe file paths fail closed.

Run locally:

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest -q
python -m build --sdist --wheel
investiq demo
investiq app --help
```

CI also checks `node --check`, wheel installation, help commands and packaged HTML/JS/CSS assets. Keep the normal draft-to-ready CI efficiency policy; do not create a new workflow per commit.

## Opt-in manual live-provider and usability acceptance (NOT performed by CI)

On a trusted local computer, with the actual holder's permission and credentials:

1. Verify the selected stock's legal issuer identity, current venue/MIC, currency and share class independently of SEC issuer-candidate discovery. Record candidate mismatches and reject ambiguous records.
2. Check the SEC User-Agent policy and make **one user-triggered** directory, recent 10-K and annual Companyfacts read. Compare filing date, accession, source link, parsed excerpt and missing data to the original SEC record. Don't claim retrieved excerpts prove business claims without reading their context.
3. If quote access is **actually licensed**, use an entitled Twelve Data key, compare real market event time, quote kind, delay/session, MIC and currency, and check invalid/stale data without evading fair-access limits. **No quote with UNKNOWN/DENIED snapshot rights enters stored research.**
4. With a private authorized OpenAI API key, confirm the selected model/Responses endpoint is available and that expected per-request data handling/usage costs are acceptable. Ask one ordinary and one adversarial source-grounding question; manually assess factual support and unsupported IDs. The request uses `store:false` and bounded tokens, which do **not** override provider policies.
5. Enter positive EPS/price *manually*, document currency/share-class/split basis and challenge bear/base/bull sensitivity; do not portray hypothetical price-only CAGR as a forecast.
6. Deliberately create a thesis, revise stage/risk/invalidation conditions, close and restart with the same private directory, reopen/export both vintages offline, and confirm absent restricted fields. Encrypt and back up the private folder; do not publish real notes.
7. Observe keyboard navigation, focus, label/error announcement, high zoom/mobile layout, screen-reader reading order, consent understanding and first-use usability with the claimed supported OS/browser. Record issues, not implied pass/fail.
8. Record the date, authorized provider plan and what was checked, test-company industry-neutral inputs, exact gaps, errors, model cost, time-to-useful answer, user corrections and whether this was actually preferable to a comparable existing research workflow. **Do not commit private observations or credentials.**

**Outcome statement:** An offline-green PR 7 establishes a **tested personal-alpha code path**. Live data, economic trustworthiness and real usability remain **unverified** until a dated, rights-approved manual evidence log exists. Do not promote to a public tagged v0.3 release or advertise production readiness on automated results alone.

## v0.4 handoff after this gate

Begin v0.4 only with clearly bounded sector-neutral economics/trends and comparable-peer definition work; do not expand data providers or make stock rankings until verified temporal/source identity, lawful coverage and user acceptance of the basic workflow are documented. New methods must be independently testable, evidence-linked and explicit about missing data.
