# InvestIQ Engineering Alignment Audit — v0.1.1 Baseline

> **Audit date:** 2026-10-27  
> **Audited branch/commit:** `main` at `b71b6fd858c35a5ef823496aeb2608f66bba1e9b` (before the proposed baseline hardening changes).  
> **Standards:** [Engineering Blueprint v1.0](engineering-blueprint.md), [Architecture](../architecture/overview.md), [Product Roadmap v2.0](../product/product-roadmap.md), [ADR 0003](../decisions/0003-connected-data-and-research-history.md).  
> **Purpose:** determine whether the existing project is ready to begin **v0.2 PR 1 — provider-neutral market-data contracts**, **not** to audit/deploy future modules prematurely.

## Audit decision

**Core architecture: aligned. Baseline release checks: passing. One present-day financial correctness gap: fix before PR 1.**

A clean architecture is not the same as every future engineering capability being implemented. The project is a small **released offline library**; evaluating it as if a frontend or distributed, multi-user market-data service already existed would be misleading. Most missing v0.2 features are legitimate non-applicable targets.

The targeted pre-v0.2 correction is to prevent the integrated P/E valuation workflow from treating EPS denominated in another currency as comparable with the trading-currency hypothetical entry price without an explicit FX conversion. This PR contains a focused fix and regression tests, retaining the current wire schema and package structure.

### Audit evidence and verification boundary

- Examined current `src/investiq_core/` modules, tests, packaging, `.github/workflows/ci.yml`, repo tree, roadmap/blueprint/ADR, contributor/security guidance and five model-neutral skill definitions.
- Latest audited `main` CI run `40479851269` passed Ruff, pytest (**94 tests**), wheel/sdist build and installed-wheel CLI smoke.
- `pyproject.toml` uses Python 3.11+, setuptools packaging, zero mandatory runtime dependencies and Ruff/pytest/build development tools.
- No branch-diff performance profiling, line/branch coverage measurement, mypy/pyright analysis, penetration test, external provider integration test, AI semantic evaluation or manual end-user usability study was run for this audit. **Do not interpret their absence as a passed test.**
- The proposed fix must independently pass CI and reviewed PR gates before closure is claimed.

## 1. Alignment matrix

| Review dimension | Baseline finding | Status | Required action before v0.2 PR 1? |
| --- | --- | --- | --- |
| Domain architecture | Evidence, valuation, research and thesis depend only on stdlib/domain; `workflow.py` orchestrates; CLI is thin. No vendor/DB/UI coupling. | **Aligned** | No re-layering, renaming or placeholder ports |
| Product scope | Offline synthetic workflow honestly labeled; no claims of deployed provider data or frontend. | **Aligned** | Keep v0.2 planned vs implemented explicit |
| Financial model correctness | Checks finite/positive input, scenario weights and as-of evidence; **cross-currency EPS can enter price/EPS calculation without conversion**. | **Fix now (S-01)** | **Yes** |
| Data provenance and historical records | Source publication/retrieval/availability/recorded dates, Decimal serialization, supersession, thesis hashes and public/recorded cutoffs. | **Aligned for v0.1** | Extend—not replace—for v0.2 market sessions/issuer and entitlements |
| Code structure/naming | Cohesive modules, stable public symbols, no operational `phase_*` file sprawl or speculative services. | **Aligned** | Preserve modular-monolith simplicity |
| Typing/static analysis | Source APIs use annotations, but `pyright`/`mypy` is not a configured CI gate and several JSON boundaries legitimately use `Any`. | **Incremental gap (S-03)** | Not a blocker before contract design; choose/baseline checker in v0.2 PR 1 |
| Formatting/quality tools | Ruff lint is active; `ruff format --check` is not. | **Incremental gap (S-03)** | Add after small baseline normalization early v0.2 |
| Testing | Six test modules, successful 94-test CI run, negative evidence/valuation/revision tests, CLI smoke. No numerical coverage report or provider contracts. | **Aligned for shipped functionality; improve with v0.2** | Add currency regression now; provider tests when adapter exists |
| Packaging/release/CI | Wheel/sdist verified, installed CLI tested, latest main CI green, cancellation enabled for superseded PR runs. | **Aligned** | Preserve current gates; avoid redundant CI churn |
| Security/privacy | Public synthetic fixtures, explicit license restrictions, no current network/API keys or multi-user data store. Security guide exists. | **Proportionate** | Add provider secrets, threat model and source-use tests with first real adapter |
| AI readiness | Five `SKILL.md` files and structured evidence-cited `ResearchReport`; semantic truth verification is explicitly not claimed. | **Aligned at contract level** | Golden factuality/prompt-injection evaluations with actual AI features |
| Frontend/UI/UX | No frontend. CLI example and docs are present; future UX principles defined. | **Not applicable yet** | Do not scaffold a frontend |
| Performance/observability | Pure local arithmetic and simple CLI; no remote latency or cloud workloads. | **Not applicable yet** | Instrument provider requests and cache behavior when connected data arrives |
| Generated-file hygiene | Quickstart creates root `demo.json`, which was not in `.gitignore`. | **Minor fix (S-02)** | Include as part of same focused baseline change |

## 2. Findings, evidence and disposition

### S-01 — Currency-unsafe P/E input path (material; pre-v0.2 blocker)

**Files:** `src/investiq_core/workflow.py`, `tests/test_workflow.py`, `docs/methodology/valuation.md`.

`FinancialObservation` correctly permits a company to report EPS in a currency different from the listing currency. The bundled research evaluator checks diluted EPS unit and instrument identity, but did not ensure that EPS currency matches the hypothetical entry price currency. A USD-listed issuer with reported EUR EPS could yield an apparently legitimate P/E/scenario result without a referenced FX conversion.

**Resolution in this PR:** treat the current price input as trading-currency denominated (the existing documented valuation assumption); optionally record `hypothetical_entry_price_currency` in bundles; reject cross-currency EPS/price until an explicit, attributed conversion layer exists. Return `valuation_currency` for output clarity. Older v0.1 bundles without the optional field remain compatible. Add negative tests for mismatched EPS and explicitly mislabeled price; add compatibility test.

**Boundary:** do not prohibit non-trading-currency observations at the evidence layer; they are valid research facts. Reject only the unsupported *valuation combination*. Do not silently add a made-up spot FX rate.

### S-02 — Generated example unintentionally tracked (minor)

**Files:** `.gitignore`, README quickstart.

Root `demo.json` is generated when running the documented CLI. It was not ignored, creating accidental untracked output in an otherwise clean repo. The example is synthetic, so this is hygiene rather than sensitive-data exposure.

**Resolution in this PR:** ignore the root generated `demo.json`. Private real research data still belongs outside the public repository and requires separate rules.

### S-03 — Developer tooling not yet enforced (adoption task, not a release failure)

**Files:** `pyproject.toml`, `.github/workflows/ci.yml`, Blueprint section 5.

Keep existing Ruff, pytest, wheel and CLI gates. In v0.2 PR 1, select **one** type checker (mypy or pyright), document an incremental strictness baseline for new contracts, and plan formatting/coverage visibility after measuring their impact. An early provider PR must add synthetic provider contract tests, with a separate opt-in live test using entitled credentials.

**Do not** add a meaningless 100%-coverage threshold, run two competing type checkers, or fail the whole project over preexisting acceptable dynamic JSON boundaries.

### S-04 — Domain features intentionally absent (not a defect)

Market-data adapters, `CurrentResearchView`, source-entitlement/freshness models, durable snapshot service, distributed cache, API, UI, auth and AI evaluation runner are **future-release scope**. Building them as part of “workspace alignment” would improperly advance v0.2 PR 1 and create speculative scaffolding. Track them under the roadmap's six outcome-based PRs.

## 3. Architecture import/dependency inspection

Observed dependency direction is appropriate:

```text
valuation.py       -> stdlib
evidence.py        -> stdlib
research.py        -> evidence.py + stdlib
thesis.py          -> evidence.py + stdlib
workflow.py        -> evidence.py + research.py + thesis.py + valuation.py
cli.py             -> workflow.py + stdlib
__main__.py        -> cli.py
```

No direct web/data provider calls, brokerage libraries, cloud database abstractions or LLM API calls are present in this domain-core dependency chain. Adding empty `services/`, `repositories/`, `frontend/` or `backend/` packages now would **reduce** coherence without delivering a new use case.

## 4. Pre-v0.2 entry gate

**Ready to start v0.2 PR 1 when:**

- [ ] S-01 is corrected with negative and backward-compatibility tests; methodology is accurate.
- [ ] S-02 hygiene is corrected.
- [ ] The targeted hardening PR has successful Ruff/pytest/wheel/installed CLI checks and completed review with no material unresolved findings.
- [ ] `main` reflects the corrected baseline; no open competing refactor/release PRs.
- [ ] v0.2 PR 1 follows the Blueprint: typed provider-neutral quote/issuer/entitlement/time contracts and tests, *without* implementation of speculative adapters, databases or web UI.

After this baseline gate, **do not create a separate long “architecture cleanup” phase**. Introduce type checking and provider contract testing inside the actual connected-research outcomes. User-visible correctness matters more than aesthetic restructuring.

## 5. Recommendation

**Keep the existing module layout. Resolve S-01/S-02 in one focused baseline PR, review it, and then proceed to the first provider-neutral domain contract PR.** No full repository rewrite, frontend or backend service is justified by this audit.

This report evaluates publicly accessible source/CI evidence at the stated commit; it is not an independent financial audit, legal data-license opinion or penetration test.
