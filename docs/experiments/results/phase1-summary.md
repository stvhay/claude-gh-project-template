# Phase 1 Experiment Summary

**Date:** 2026-03-05
**Branch:** experiment/h3-pilot-45
**Issue:** #45

## Hypothesis Status

| Experiment | Hypothesis | Status | Key Evidence |
|---|---|---|---|
| A1 | Decision frameworks improve Haiku INV-4 compliance (H8) | SUPPORTED | Haiku INV-4: 0/3 baseline -> 3/3 treatment; binary effect on queue pattern usage |
| A2 | Pre-completion checklists reduce pattern violations (H9) | NOT SUPPORTED | Displacement effect: Sonnet error-handling regressed 3/3 -> 0/3; combined violations increased |
| A3 | Table format beats prose for invariant compliance (H10) | NOT SUPPORTED | Prose matched table exactly: 0 violations across all 6 Sonnet runs in both conditions |
| A4 | Enforcement classification predicts violations (H6 revised) | SUPPORTED | 93.8% retrodiction accuracy (166/177); structural vs reasoning split cleanly separates model tiers |
| B1 | CI enforcement beats documentation (H4) | NOT SUPPORTED | Docs-only achieved 100% (6/6); enforcement conditions scored 83% due to unrelated Haiku execution failures |
| B2 | Encounter order affects output pattern (H5) | NOT SUPPORTED | 9/9 PASS across all conditions; agents discover patterns through exploration regardless of pointers |

## Template Implementation Scope

Based on supported hypotheses (A1, A4), the upstream template changes are:

**From A1 (Decision Framework):**
- SPEC.md spec-template gains a Decision Framework section
- Convention: each reasoning-required invariant gets a situation-keyed entry (Situation / Action / Invariant table)
- Linked to invariant IDs for traceability

**From A4 (Enforcement Classification):**
- SPEC.md invariants table gains an "Enforcement" column with values `structural` or `reasoning-required`
- Template guidance: prioritize converting reasoning-required invariants to structural via API design
- Quality metric: ratio of structural to reasoning-required invariants

**NOT implementing (unsupported):**
- No Pre-Completion Checklist section (A2 -- displacement effect risk)
- No mandate for table format over prose (A3 -- tables remain convention for readability/RAG, not compliance)
- No structural enforcement test guidance (B1 -- strong patterns suffice)
- No Canonical Example field (B2 -- agents discover patterns independently)

## Ragling Feature Scope

**Parser changes (A1):**
- Add `decision_framework` to `_SECTION_MAP` in spec parser
- Re-index collections containing SPEC.md files after template update

**Parser changes (A4):**
- Extract `enforcement` metadata from invariants table (future -- not needed for initial template change)

**Phase 2 dependency (C1):**
- Add `section_type` parameter to `SearchFilters` (contingent on C1 experiment results)
- Expose section_type filter in `rag_search` and `rag_batch_search`

## What We Learned from Unsupported Hypotheses

**A2 -- Displacement effect:** Pre-completion checklists caused Sonnet to focus on explicitly listed items (queue routing, follower mode) at the expense of patterns it previously handled implicitly (error handling). Sonnet's error-handling regressed from 3/3 to 0/3. The checklist added cognitive load without benefit and actively displaced a previously reliable pattern. Takeaway: explicit checklists can harm models already at ceiling performance.

**A3 -- Model capability dominates format:** Sonnet extracted constraints equally well from a dense prose paragraph and a structured table. Both conditions produced 0 violations across all 7 scoring dimensions. Format choice for invariants should be driven by human readability and RAG chunking quality, not agent compliance concerns.

**B1 -- Pattern visibility dominates enforcement:** With 10 existing tool modules following an identical pattern, every agent discovered the correct pattern through code exploration alone. No agent ever attempted to put tools in the wrong location, so enforcement was never triggered. The CLAUDE.md subsystem map and existing code examples are a stronger signal than any enforcement test or hook. (Caveat: enforcement may matter in codebases with fewer examples or ambiguous patterns.)

**B2 -- Exploration beats directed reading:** Whether given no pointer, a SPEC.md pointer, or an explicit instruction to read a specific file first, Sonnet produced structurally identical output in all 9 runs. Agents discover codebase conventions through their own exploration, making encounter-order control unnecessary when conventions are consistent.

## Cross-Cutting Insights

1. **Strong codebase patterns > any documentation format change.** A3, B1, and B2 all converge on the same finding: when the codebase itself embodies clear, consistent patterns, documentation format variations have no measurable effect on agent behavior. Code structure is the dominant instruction signal.

2. **Decision frameworks work because they bridge reasoning gaps, not because of format.** A1 succeeded not because of table format (A3 showed format is irrelevant) but because it converted a reasoning-required invariant into a procedural recipe. The situation-keyed format ("Need DB writes? -> Submit IndexJob") gave Haiku a pattern to follow where the declarative invariant ("only IndexingQueue writes") required architectural reasoning it could not perform.

3. **The key lever is the structural vs reasoning-required distinction (A4).** The 93.8% retrodiction accuracy confirms that invariant violations are predictable from the enforcement classification. Structural invariants are universally respected (92.6% accuracy, 100% excluding task-framing artifacts). Reasoning-required invariants cleanly separate model tiers: Haiku fails them consistently, Sonnet/Opus pass them consistently.

4. **Less capable models benefit from procedural guidance (A1) but not checklists (A2).** The A1 decision framework improved Haiku from 0/3 to 3/3 on INV-4. The A2 checklist improved Haiku on only 1/3 runs while causing Sonnet regressions. The difference: decision frameworks are situation-specific ("when X, do Y") while checklists are generic verification items that can displace existing patterns.

5. **The path forward is converting reasoning-required invariants to structural ones.** A4's implementation guidance is the highest-leverage finding: if `ToolContext` provided `require_queue()` instead of requiring manual follower-mode checks, or if the `tools/` framework routed writes through `submit_write_job()` automatically, the invariants that trip Haiku would become structural and model-tier-independent.

## Phase 2 Go/No-Go

Decision criteria from the design doc:
- If A1 or A2 supported -> proceed with C1 (section-type filtering)
- If A2 and C1 both supported -> proceed with C2 (pre-completion aggregation)
- If neither A1 nor A2 supported -> Phase 2 not needed

**Result: C1 is GO.** A1 is supported, so the `decision_framework` section type exists and needs targeted retrieval. C1 will test whether section-type filtering in `rag_search` provides higher precision than generic search for retrieving decision framework sections.

**Result: C2 is NO-GO (blocked).** A2 is not supported, so pre-completion aggregation has no checklist sections to aggregate. C2 depends on both A2 and C1 being supported. Even if C1 succeeds, C2 cannot proceed without validated checklist content.

## Next Steps

1. **Implement template changes:** Add Decision Framework section and Enforcement column to the upstream spec-template (supported by A1 and A4)
2. **Implement ragling parser change:** Add `decision_framework` to `_SECTION_MAP` in spec parser (A1 deliverable)
3. **Run C1 experiment:** Test section-type filtering for `decision_framework` section retrieval precision
4. **Update ragling SPEC.md:** Add Decision Framework section and Enforcement column to ragling's own SPEC.md as reference implementation
5. **Consider API hardening:** Evaluate converting reasoning-required invariants to structural ones via `require_queue()` and `submit_write_job()` helpers (A4 insight -- separate issue)
