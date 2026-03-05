# SPEC.md Template Experiments

## Background

Controlled experiments validated SPEC.md template enhancements before shipping them. Eight experiments (~70 subagent runs across Haiku 4.5, Sonnet 4.5, and Opus 4) used H3 methodology: worktree-isolated subagents, controlled prompts, invariant scoring rubric, independent reviewer agents. Conducted in [aihaysteve/local-rag#45](https://github.com/aihaysteve/local-rag/issues/45).

## Results

| Experiment | Hypothesis | Status | Key Evidence |
|---|---|---|---|
| A1 | Decision frameworks improve Haiku invariant compliance | **SUPPORTED** | Haiku INV-4: 0/3 baseline → 3/3 treatment |
| A2 | Pre-completion checklists reduce pattern violations | NOT SUPPORTED | Displacement effect: Sonnet error-handling regressed 3/3 → 0/3 |
| A3 | Table format beats prose for invariant compliance | NOT SUPPORTED | Prose matched table exactly: 0 violations across all runs |
| A4 | Enforcement classification predicts violations | **SUPPORTED** | 93.8% retrodiction accuracy (166/177 invariant evaluations) |
| B1 | CI enforcement beats documentation alone | NOT SUPPORTED | Docs-only achieved 100%; enforcement added no benefit |
| B2 | Encounter order affects output pattern | NOT SUPPORTED | 9/9 PASS across all conditions |
| C1 | Section-type filtering improves retrieval precision | **SUPPORTED** | Targeted retrieval outperformed generic search |

## What Changed in the Template

Based on A1 and A4, PR [#18](https://github.com/stvhay/claude-gh-project-template/pull/18) added:

1. **Decision Framework section** — situation-keyed table (`Situation | Action | Invariant`) that converts reasoning-required invariants into procedural recipes agents can follow.
2. **Enforcement column** — `structural` or `reasoning-required` classification in the invariants table. Structural invariants are respected universally; reasoning-required invariants separate model tiers.
3. **Testing section** — convention for anchoring tests to spec items.

## Cross-Cutting Insights

> **Strong codebase patterns dominate documentation format.** A3, B1, and B2 converge: when the codebase embodies clear, consistent patterns, documentation format variations have no measurable effect on agent behavior. Code structure is the dominant instruction signal.

> **Decision frameworks bridge reasoning gaps, not format gaps.** A1 succeeded because it converted a reasoning-required invariant into a procedural recipe, not because of table format (A3 showed format is irrelevant for compliance).

> **The structural vs reasoning-required distinction is the key lever.** 93.8% retrodiction accuracy confirms invariant violations are predictable from enforcement classification. Structural invariants are universally respected. Reasoning-required invariants cleanly separate model tiers.

> **Less capable models benefit from procedural guidance but not checklists.** Decision frameworks (situation-specific: "when X, do Y") improved Haiku from 0/3 to 3/3. Checklists (generic verification) caused Sonnet regressions by displacing previously reliable implicit patterns.

> **The highest-leverage improvement is converting reasoning-required invariants to structural ones** via API design (e.g., `require_queue()` instead of manual follower-mode checks).

## Full Materials

Complete experiment design, scoring rubrics, SPEC.md variants, and per-experiment results are in [aihaysteve/local-rag](https://github.com/aihaysteve/local-rag), branch `experiment/h3-pilot-45`, issue [#45](https://github.com/aihaysteve/local-rag/issues/45).
