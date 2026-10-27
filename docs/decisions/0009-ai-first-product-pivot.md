# ADR 0009 — AI-first investor research and distribution validation pivot

**Status:** Proposed — requires product review before merge · **Date:** 2026-10-27
**Decision scope:** Future product releases and v0.3+ user-facing prioritization only.
**References:** [Product Roadmap v3.0](../product/product-roadmap.md), [v0.3 PRD](../product/ai-research-experience.md), [Validation Plan](../product/validation-plan.md), [Engineering Blueprint](../engineering/engineering-blueprint.md).

## Context

Roadmap v2.0 prioritized provider-neutral research, financial correctness, immutable history, progressively wider financial analysis and a GUI only at v0.5; model execution and AI UX were optional. v0.2 implementation produced a credible CLI research foundation, but no integrated AI agent or nontechnical user experience.

General LLMs and existing financial research tools already answer financial questions, offer AI analysis, compare companies and maintain watchlists. A library of calculations, model-agnostic research instructions or a basic chatbot is **not** proven differentiation. Requiring a user to learn APIs or engineer prompts defeats the intended consumer job.

## Proposed decision

1. Make v0.3 a **bounded AI-first Research Experience** with a usable conversation/task UI, clear sourced output, thesis challenge and explicit research control; not just a fundamentals/peer backend expansion.
2. Reprioritize v0.4 structured investor context and thesis continuity; v0.5 discovery and intelligence; v0.6 optional portfolio context; v0.7+ conditional quant.
3. Evaluate **standalone vs assistant-native** distribution with user trials. Do not presume a full web SaaS is required.
4. Maintain independent deterministic financial core; tools own financial facts/calculations; models own bounded interpretation and reasoning. Add semantic AI evaluation, privacy and consent.
5. Retain all enforceable data-rights, source freshness, point-in-time, reproducible snapshot and provider entitlement decisions in ADRs 0003–0008. Do not reinterpret historical v0.2 release records.

## Consequences and unknowns

**Benefits:** First useful answer sooner; a testable differentiation hypothesis; prevents further platform-first scope expansion.

**Costs/risks:** Model errors, unlicensed hosted financial displays, inference cost, personal research privacy, onboarding/identity complexities, UX and semantic-evaluation work. A lightweight integration may win over a custom web app.

**Gates:** Underlying provider permissions, rigorous claim-to-source evaluation, usable first-session workflow, real user comparison and repeat-use evidence. No development authorization, alpha claim or public hosted entitlement arises merely from this ADR.

**Rejected:** postpone UI to v0.5; market five AI skills as an autonomous agent; add a generic multi-agent stack; build SaaS accounts or continuous data infrastructure before validating the research workflow.
