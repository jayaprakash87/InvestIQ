# Portable InvestIQ Research Skills

Five independent **model-agnostic** research skills. Each `SKILL.md` file provides instructions that an AI assistant, human researcher, or orchestrator can apply using its own tools.

These are **research procedures**, not credentialed investment advice, trading agents or verified predictors. The source-of-truth for financial calculations is the tested `investiq_core` library, not model-generated arithmetic.

**Current status (v0.2):** These five SKILL.md files do **not** run a model, orchestrate tools or automatically research stocks. They require an external assistant/human to supply evidence and run the procedure. The [proposed v0.3 product](../docs/product/ai-research-experience.md) would add a **bounded, source-grounded model orchestrator** and nontechnical user interface, subject to [semantic/financial model evaluation](../docs/engineering/engineering-blueprint.md#8-ai-first-orchestration-and-release-evaluations). Until implemented and tested, do not market the skills as a deployed AI research agent.

## Available skills
| Skill | Use |
| --- | --- |
| [business-analysis](business-analysis/SKILL.md) | Map business economics and moat |
| [financial-analysis](financial-analysis/SKILL.md) | Analyze reported fundamentals and changes |
| [valuation-analysis](valuation-analysis/SKILL.md) | Test assumptions and price scenarios |
| [peer-comparison](peer-comparison/SKILL.md) | Compare matched and mismatched business models |
| [thesis-challenge](thesis-challenge/SKILL.md) | Identify ways a thesis could fail |

## Open workflow
1. Choose a skill and define subject instruments, question, and an **as-of** timestamp.
2. Supply attributed `FinancialObservation` records plus separately labelled `ResearchAssumption` records. No assumptions masquerading as facts.
3. Follow the selected skill instructions to draft findings. Return `ResearchReport` JSON, citing exact input IDs. Unknown information becomes an explicit `data_gap`.
4. Parse `ResearchReport.from_record(...)`; run `validate_research_report(...)`; attach the original evidence for auditing.
5. Perform independent numerical and semantic source review. **Structural validation alone cannot verify that prose faithfully describes the cited data.**

No external provider, specific LLM, account, portfolio, UI or runtime is required. To adopt in a compatible skill-capable assistant, use the relevant `SKILL.md`; runtime invocation and tool availability depend on the host.

## Validation
Run `python -m pip install -e ".[dev]"` and `pytest -q`.
`tests/test_research.py` verifies schema, grounding category, historical cutoffs, and negative cases using synthetic information. These tests are **not** an LLM benchmark. Future skill evaluations should separately test how different models behave with missing, contradictory, and outdated evidence.

See [skill research contract](../docs/methodology/research-report-contract.md).
