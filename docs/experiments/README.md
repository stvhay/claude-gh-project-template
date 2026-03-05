# SPEC.md Template Experiments

Controlled experiments validating SPEC.md template enhancements for agent code quality.
Conducted in [aihaysteve/local-rag](https://github.com/aihaysteve/local-rag) (issue [#45](https://github.com/aihaysteve/local-rag/issues/45)), branch `experiment/h3-pilot-45`.

## Summary

8 experiments, ~70 subagent runs across Claude Haiku 4.5 / Sonnet 4.5 / Opus 4.
H3 methodology: worktree-isolated subagents, controlled prompts, invariant scoring rubric, independent reviewer agents.

| Experiment | Hypothesis | Status |
|---|---|---|
| [A1](results/a1-decision-framework-results.md) | Decision frameworks improve Haiku invariant compliance | SUPPORTED |
| [A2](results/a2-pre-completion-checklist-results.md) | Pre-completion checklists reduce violations | NOT SUPPORTED |
| [A3](results/a3-tables-vs-prose-results.md) | Table format beats prose for compliance | NOT SUPPORTED |
| [A4](results/a4-enforcement-classification-results.md) | Enforcement classification predicts violations | SUPPORTED |
| [B1](results/b1-ci-enforcement-results.md) | CI enforcement beats documentation | NOT SUPPORTED |
| [B2](results/b2-encounter-order-results.md) | Encounter order affects output pattern | NOT SUPPORTED |
| [C1](results/c1-section-type-filtering-results.md) | Section-type filtering improves retrieval precision | SUPPORTED |

## Validated Template Changes

1. **Decision Framework section** (A1) — situation-keyed table bridging reasoning gaps
2. **Enforcement column** (A4) — structural vs reasoning-required classification

See [phase1-summary.md](results/phase1-summary.md) for full analysis and cross-cutting insights.

## Documents

- [Experiment Design](design/experiment-design.md) — hypotheses, methodology, success criteria
- [Experiment Plan](design/experiment-plan.md) — implementation tasks
- [Materials](materials/) — SPEC.md variants, scoring rubrics, prompts
