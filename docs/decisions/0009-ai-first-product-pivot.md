# ADR 0009 — Personal-First AI Investment Research Through Open-Source v1.0

**Status:** Proposed (PR review; not accepted by repository merge) · **Date:** 2026-10-27
**Scope:** Future priorities and release sequencing, preserving prior v0.2 code/ADRs as factual history.
**References:** [Full Product Roadmap v3.0](../product/product-roadmap.md) · [Research History](../product/research-foundations.md) · [v0.3 PRD](../product/ai-research-experience.md) · [Validation](../product/validation-plan.md).

## Context

v2.0 engineered sound source/issuer contracts, compliant market-data access, deterministic research and deliberate history, but the v0.2 source release candidate still requires CLI/BYOK knowledge, provides only a narrow US annual research slice and has no model runtime or approachable UI. The first v3 draft put AI-first user experience at v0.3 but **underrepresented the extensive earlier research and the full desired personal-to-v1.0 open-source maturity path**.

Earlier investment work crossed broad AI infrastructure and physical AI universes (150 and 194 names / 23 segments), factor scoring, fundamental trends, true versus complementary peers, FCF/ROIC/debt quality, forward valuations and hypothetical entry-price return hurdles, multiple time horizons, thesis challenges, user portfolio themes and repeated corrections of questionable rankings. Such research dictates future functional requirements. A generic LLM chatbot or a single company research page does not address the full job.

## Decision proposed

1. InvestIQ is an **AI-first, open-source, local-first equity research workspace**, personally useful before packaged external adoption. The default next experience is a **thin, locally runnable research task UI**, not a mandatory SaaS or an indefinite "maybe app / maybe plugin" choice.
2. Define a **full, dependency-ordered v0.3→v1.0 roadmap**, with an independently usable job and release gate at each version. v0.3 is only the first personal AI research desk, not the finished product.
3. Research capabilities follow actual prior work: company/peers (v0.4), evidence-aware universe screening/scoring (v0.5), reverse underwriting/entry scenarios (v0.6), explicit history and monitoring (v0.7), private optional portfolio (v0.8), independent open-source onboarding (v0.9), stable complete supported workflow (v1.0).
4. AI coordinates well-bounded tools and grounded interpretation; permitted providers/deterministic financial modules remain the authoritative data and calculation sources. Scores are versioned, horizon-specific, transparent and confidence/coverage-aware.
5. Research storage is user-owned local/private by default; today's price comes from entitled on-demand providers. Nontechnical use must not demand shell, CIK/MIC, JSON or prompt engineering; external provider/model keys may be necessary and should have transparent guided setup; a no-key synthetic demo always works.
6. Assistant-native plugins/skills/MCP remain possible **additional** OSS distribution interfaces, subject to comparative validation, without indefinitely delaying the personal UI.
7. Preserve ADRs 0003–0008 and completed v0.2 CLI/release records unchanged. Do not treat personal historical spreadsheets, positions, prices or research rankings as public default datasets.

## Alternatives considered

- **Only ship a model-independent research API and skills:** insufficient for daily personal use; still forces prompts/code.
- **Build a large standalone SaaS immediately:** too expensive and ignores open-source/privacy/licensing requirements.
- **Focus solely on v0.3 chat then revisit:** omits prior scoring/underwriting/portfolio research and lacks definition of a stable usable v1.0.
- **Deploy a 194-company scorecard with prior worksheet values now:** risks fabricated/stale rankings and unlicensed data; build source/coverage/method governance first.

## Consequences and gates

Pros: preserves investment methodology context, creates usable personal stages, keeps technology choices proportionate and specifies eventual external OSS readiness. Costs: sustained source/fundamental integration, quality evaluations, UI/test/install/migration work and model provider economics.

Stop/narrow if the creator does not use the early product, material calculations/citations are unreliable, licensed data insufficient or other users cannot install a supported workflow. Product success is evidence-based, not proof of profitable returns. **Documentation PR does not implement these features, approve hosting, tag release or authorize a merge.**
