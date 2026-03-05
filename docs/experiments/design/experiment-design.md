# Design: SPEC.md Template and RAG Experiments

**Issue:** #45 -- Test whether RAG-powered SPEC.md retrieval improves agent efficiency
**Date:** 2026-03-05
**Branch:** experiment/h3-pilot-45

## Context

Issue #45 experiments produced six validated conclusions (C1-C6) about how agents interact with specifications and code structure. The zig-learner project independently validated instruction format patterns through measured self-improvement loops. The upstream template (claude-gh-project-template) documents the theoretical foundation: VSA, agent-oriented design, context optimization, and spec rationale.

This design proposes experiments to validate specific template and RAG changes before shipping them. Each experiment produces either (a) validated implementation scope for the upstream template and/or ragling, or (b) evidence to reject the hypothesis and avoid shipping unvalidated changes.

### Prior Art

| Source | Key Finding |
|---|---|
| H3 Pilots (24 runs) | Model capability dominates context format; RAG saves ~20% session cost |
| VSA Experiment | Code structure is instruction; facades attract wrong-location code |
| Formal-LLM (2024) | 50%+ improvement with formal specifications |
| Zig-learner (17 lessons) | Tables > prose; situation-keyed frameworks; pre-completion checklists |
| Context Optimization | Three-tier hot/warm/cold architecture; 50% context budget per subsystem |

## Experiment Groups

### Group A: SPEC.md Format Enhancements

These experiments test whether new SPEC.md sections improve agent code quality. Each uses the H3 methodology: worktree-isolated subagents, controlled prompts, invariant scoring rubric.

---

#### Experiment A1: Decision Framework Section

**Hypothesis (H8):** Adding a situation-keyed Decision Framework section to SPEC.md improves Haiku-class invariant compliance on tasks requiring architectural reasoning.

**Null hypothesis:** Decision frameworks have no effect on invariant compliance; Haiku's INV-4 failure rate remains at 0% regardless of format.

**Rationale:** C4 showed architectural invariants require reasoning that Haiku lacks. Declarative invariants ("only IndexingQueue writes") state what must hold but not what to do. Decision frameworks ("need DB writes? -> submit IndexJob to queue") provide the procedural recipe a pattern-dependent model can follow. The zig-learner's situation-keyed format was the highest-performing instruction format across 225 exercises.

**Independent variable:** SPEC.md format (2 conditions)
- **A (baseline):** Current SPEC.md with invariants table (declarative only)
- **B (treatment):** Current SPEC.md + Decision Framework section with situation-keyed entries

**Decision Framework format (treatment condition):**

```markdown
## Decision Framework

| Situation | Action | Invariant |
|---|---|---|
| Need to write to the index database | Submit `IndexJob` to `IndexingQueue`; never call DB write functions directly | INV-4 |
| Need a database connection | Call `get_connection()` + `init_db()`; never use raw `sqlite3.connect()` | INV-3 |
| Implementing a new MCP tool | Create `tools/<name>.py` with `register(mcp, ctx: ToolContext)` | -- |
| Tool needs to trigger indexing | Check `_get_queue()`; return error if None (follower mode) | INV-4 |
```

**Dependent variable:** INV-4 pass rate on rag_delete_source task (the H3 Pilot 2 task that Haiku universally failed).

**Task:** "Add a `rag_delete_source` MCP tool that removes a source and its documents/embeddings from a collection." Same task as H3 Pilot 2.

**Models:** Haiku (primary -- tests whether decision frameworks move it above the capability floor), Sonnet (control -- should remain at ceiling).

**Runs:** 3 per condition per model = 12 total.

**Scoring rubric:** Same as H3 Pilot 2 (INV-4, INV-3, Idx-INV-1, MCP-pattern, error handling, connection lifecycle, follower mode).

**Success criterion:** Haiku treatment condition achieves >= 2/3 INV-4 PASS (vs 0/3 baseline). Sonnet remains at ceiling in both conditions.

**If supported:** Template gains a Decision Framework section convention. SPEC.md spec-template adds the section. Ragling parser gains `decision_framework` section type.

**If not supported:** Decision frameworks do not bridge the capability gap for Haiku. Document the result. Consider whether structural enforcement (H4/Group B) is the only viable path for sub-threshold models.

---

#### Experiment A2: Pre-Completion Checklist Section

**Hypothesis (H9):** A pre-completion checklist in SPEC.md reduces pattern violations (MCP-pattern, error handling, connection lifecycle) across all models.

**Null hypothesis:** Pre-completion checklists have no effect on pattern violation rates.

**Rationale:** H3 pilots showed pattern violations (wrong decorator, missing error handling) occurred in 4/24 runs across all models. These are not invariant violations -- they're implementation quality issues. The zig-learner's pre-completion checklist ("function >40 lines? String if-else chain?") reduced quality issues by prompting self-review. The SWE-agent research showed better agent interfaces improve completion rates.

**Independent variable:** SPEC.md format (2 conditions)
- **A (baseline):** Current SPEC.md
- **B (treatment):** Current SPEC.md + Pre-Completion Checklist section

**Pre-Completion Checklist format (treatment condition):**

```markdown
## Pre-Completion Checklist

Before claiming implementation is complete, verify:

| Check | How to Verify |
|---|---|
| Tool uses `@mcp.tool()` decorator | Decorator present and uncommented |
| Tool catches exceptions and returns `{"error": ...}` | Try/except wraps main logic |
| Database connections closed in `finally` block | `conn.close()` in finally |
| Write operations route through IndexingQueue | No direct INSERT/UPDATE/DELETE |
| Follower mode handled | `_get_queue()` checked; error if None |
| Tool file follows `register(mcp, ctx)` pattern | Function signature matches |
```

**Dependent variable:** Pattern violation count per run (MCP-pattern, error handling, connection lifecycle items from the H3 rubric).

**Task:** Same rag_delete_source task as A1. Can share the baseline condition runs with A1 to reduce total experiment size.

**Models:** Haiku, Sonnet (3 runs each per condition = 12 total, or 6 if sharing A1 baseline).

**Scoring rubric:** Pattern-violation items only (MCP-pattern, error handling, connection lifecycle). Invariant items scored but not primary.

**Success criterion:** Treatment condition reduces mean pattern violations by >= 50% across models (e.g., from 0.33/run to <= 0.17/run for Sonnet).

**If supported:** Template gains a Pre-Completion Checklist section convention. Ragling parser gains `pre_completion_checklist` section type. `rag_search_task` gains `task_type="pre_completion"` that aggregates checklist items + invariants for touched subsystems.

**If not supported:** Checklists in SPEC.md don't affect agent self-review behavior. Consider whether the checklist belongs in skill instructions (always-loaded hot tier) rather than in SPEC.md (warm tier that may not be loaded at completion time).

---

#### Experiment A3: Tables vs Prose for Invariants

**Hypothesis (H10):** Table-formatted invariants produce higher compliance than prose-formatted invariants.

**Null hypothesis:** Format has no effect; agents extract constraints equally from tables and prose.

**Rationale:** Zig-learner meta-log explicitly tracked format effectiveness: "L03 added inline comments, L04 wrote a prose paragraph, L05 added one-liners, L06 added structured tables. The agent is learning that tables > prose for reference material." Ragling's specs already use tables, but the template should validate this convention before mandating it.

**Independent variable:** Invariants format (2 conditions)
- **A (table):** Current table format with ID, Invariant, Why It Matters columns
- **B (prose):** Same invariants rewritten as a narrative paragraph (same information, different structure)

**Dependent variable:** INV-4 pass rate + overall invariant compliance.

**Task:** Same rag_delete_source task.

**Models:** Sonnet only (3 runs per condition = 6 total). Sonnet is the target because it's at the capability ceiling -- format effects would be visible only if they change how Sonnet processes the information, not whether it can reason about it.

**Scoring rubric:** Full H3 rubric.

**Success criterion:** Table condition maintains 3/3 INV-4 PASS. Prose condition shows >= 1 INV-4 FAIL, or measurably higher pattern violation rate.

**If supported:** Template mandates table format for invariants and interfaces. Document the evidence.

**If not supported:** Format is not a significant variable for Sonnet-class models. Tables may still be preferred for human readability and RAG chunk quality, but the mandate is aesthetic, not performance-based. Document as convention rather than requirement.

---

#### Experiment A4: Enforcement Classification on Invariants

**Hypothesis (revised H6):** Classifying invariants by enforcement mechanism (structural vs reasoning-required) helps teams identify which invariants to structurally enforce and predicts where less capable agents will fail.

**Null hypothesis:** Enforcement classification has no predictive or prescriptive value.

**Rationale:** C1/C4/C5 showed a clean split: structurally-enforced invariants (INV-3: WAL mode via `get_connection()`) are never violated; reasoning-required invariants (INV-4: single-writer queue) are violated by models below the capability threshold. Classifying this property makes the split explicit and actionable.

**This is an observational experiment, not an intervention.** It tests whether the classification scheme correctly predicts existing H3 data and generalizes to new invariants.

**Method:**
1. Classify all invariants from the H3 scoring rubric as "structural" or "reasoning-required"
2. Retrodict: does the classification correctly predict which invariants Haiku failed (reasoning-required) vs passed (structural) across all 24 H3 runs?
3. Extend: identify 2-3 new invariants in ragling not tested in H3. Classify them. Run Haiku on a task that touches them. Check if the classification predicts the outcome.

**Success criterion:** Classification correctly retrodicts >= 90% of H3 outcomes (which invariants each model passed/failed). New invariant predictions are correct for >= 2/3 cases.

**If supported:** Template gains an "Enforcement" column in the invariants table (Structural / Reasoning-required). This becomes a quality signal: high ratio of "reasoning-required" invariants means the codebase is fragile for less capable agents. Teams should prioritize converting reasoning-required invariants to structural ones.

**If not supported:** The structural/reasoning split is not predictive -- invariant violations are more idiosyncratic than the model suggests. Drop the classification.

---

### Group B: Structural Enforcement

These experiments test whether mechanical enforcement (CI, hooks, tests) outperforms documentation for maintaining code patterns.

---

#### Experiment B1: CI Enforcement vs Documentation

**Hypothesis (H4):** Mechanical enforcement (tests that reject wrong-location code) prevents pattern violations that SPEC.md documentation alone does not.

**Null hypothesis:** SPEC.md documentation is equally effective as mechanical enforcement at preventing pattern violations.

**Rationale:** C3 showed agents treat code as instruction and override docs. C6 showed alternative paths defeat preferred paths. The VSA experiment showed Sonnet ignoring SPEC.md guidance to put tools in `tools/` and instead modifying the facade. Mechanical enforcement (a test that fails if `@mcp.tool()` appears in `mcp_server.py`) removes the alternative path entirely -- not by documenting it, but by making it fail.

**Independent variable:** Enforcement mechanism (3 conditions)
- **A (docs only):** SPEC.md says "tools go in tools/"; no mechanical enforcement
- **B (docs + test):** Same SPEC.md + a test that asserts no `@mcp.tool()` in `mcp_server.py` and every `tools/*.py` exports `register`
- **C (docs + test + pre-commit hook):** Same as B + pre-commit hook that runs the test

**Dependent variable:** Whether the agent puts the new tool in the correct location (`tools/<name>.py` with `register()` pattern).

**Task:** "Add a `rag_stats` MCP tool that returns per-collection indexing statistics." Same as H3 Pilot 1. This is the task where Sonnet put code in `mcp_server.py` despite SPEC.md guidance.

**Models:** Sonnet (primary -- the model that violated the pattern), Haiku (secondary -- already followed the pattern in decomposed codebase).

**Runs:** 3 per condition per model = 18 total.

**Scoring rubric:**
- Tool location: correct file (`tools/stats.py`) = PASS, wrong file = FAIL
- Register pattern: `register(mcp, ctx)` function = PASS, other pattern = FAIL
- If test/hook blocks the agent: did it self-correct? PASS if corrected, FAIL if gave up

**Success criterion:** Condition B or C achieves 3/3 correct location for Sonnet (vs baseline where Sonnet put code in facade 2/2 times in prior experiment). Haiku maintains correct location across all conditions.

**If supported:** Template recommends structural enforcement tests alongside SPEC.md. Provide example test patterns. Ragling ships the enforcement tests for its own tools/ package as a reference implementation.

**If not supported:** Sonnet works around mechanical enforcement (e.g., disables the test, modifies the hook). Document the failure mode. Consider whether the enforcement needs to be in CI (not bypassable by the agent) rather than local tests.

---

#### Experiment B2: Encounter Order Control

**Hypothesis (H5):** The first relevant file an agent reads determines the pattern it produces. Controlling encounter order (via SPEC.md pointers or CLAUDE.md) improves pattern adherence.

**Null hypothesis:** Encounter order has no measurable effect; agents produce the same patterns regardless of which file they read first.

**Rationale:** C3 showed code structure is instruction. The VSA experiment showed Sonnet reading `mcp_server.py` (the facade) first and pattern-matching on it, despite `tools/` modules existing. If agents read a well-structured 100-line tool file first instead of the 106-line facade, they should produce tool-shaped code.

**Independent variable:** Encounter order (3 conditions)
- **A (uncontrolled):** No guidance on which file to read first. Agent discovers files via its own exploration.
- **B (SPEC.md pointer):** SPEC.md contains "Canonical example: `tools/search.py`" -- agent is directed to read this first.
- **C (explicit instruction):** Task prompt says "Read `tools/search.py` first for the registration pattern, then implement your tool."

**Dependent variable:** Tool location correctness + structural similarity to the canonical example.

**Task:** Same rag_stats task as B1. Can share condition A runs.

**Models:** Sonnet (3 runs per condition = 9 total).

**Scoring rubric:** Same as B1 (location, register pattern) + structural similarity score (does the output follow the same file structure as search.py?).

**Success criterion:** Condition B or C achieves 3/3 correct location (vs Sonnet's 0/2 baseline on uncontrolled encounter).

**If supported:** Template adds "Canonical Example" field to SPEC.md. Skills that spawn subagents include the canonical example path in the prompt. Ragling gains a `task_type="example"` in `rag_search_task` that retrieves the canonical example for a subsystem.

**If not supported:** Encounter order is not the mechanism -- Sonnet's architectural confidence overrides even explicit file pointers. Document the result. Structural enforcement (B1) may be the only path.

---

### Group C: RAG Feature Validation

These experiments test whether ragling feature additions improve retrieval quality for the new SPEC.md sections.

---

#### Experiment C1: Section-Type Filtering

**Hypothesis (H11):** Section-type filtering in `rag_search` enables targeted retrieval of decision frameworks and checklists with higher precision than generic search.

**Null hypothesis:** Generic search retrieves decision framework and checklist sections as effectively as filtered search.

**Rationale:** The current `rag_search_task` uses `source_type="spec"` and `subsystem` filters but cannot filter by section type. If SPEC.md gains Decision Framework and Pre-Completion Checklist sections, agents need to retrieve them specifically. The H1 experiments showed that query reformulation helps target the invariants section -- but filtering by section_type would be more reliable than keyword tricks.

**This experiment depends on A1 or A2 being supported.** If neither new section type is validated, there's nothing to filter for.

**Method:**
1. Add `decision_framework` and `pre_completion_checklist` to the spec parser's `_SECTION_MAP`
2. Add `section_type` parameter to `SearchFilters` (follows the existing `subsystem` filter pattern)
3. Index a SPEC.md containing both new sections
4. Compare retrieval precision: generic query vs section_type-filtered query for 10 test queries

**Metrics:**
- Precision: % of returned results that are the target section type
- Recall: % of target sections retrieved
- Token cost: total tokens in results

**Success criterion:** Section-type filtering achieves >= 90% precision (vs generic search precision for the target section type). Recall >= 80%.

**If supported:** Ship section_type filter in ragling. `rag_search_task` gains section_type-aware query routing: `task_type="pre_completion"` filters for checklist + invariant sections.

**If not supported:** Generic search is sufficient -- the new sections are distinctive enough to be retrieved by keyword. Ship the parser changes (for metadata) but skip the filter.

---

#### Experiment C2: Pre-Completion Aggregation

**Hypothesis:** A `task_type="pre_completion"` mode in `rag_search_task` that aggregates checklist items + invariants for touched subsystems reduces the number of agent round-trips needed for verification.

**Null hypothesis:** Agents retrieve verification context equally efficiently with generic search.

**This experiment depends on A2 and C1 being supported.**

**Method:**
1. Implement `task_type="pre_completion"` in `rag_search_task`: given file paths, detect subsystems, retrieve checklist + invariant sections for each
2. Compare: agent using `pre_completion` mode vs agent using manual `rag_search` calls for the same verification task
3. Measure: number of search calls, total tokens, time to verification

**Success criterion:** Pre-completion mode requires 1 search call vs >= 3 manual calls for equivalent coverage.

**If supported:** Ship the feature. Template skills (`/verification-before-completion`) gain a `rag_search_task(task_type="pre_completion")` call.

**If not supported:** The aggregation adds no value over manual search. Keep section_type filtering but skip the orchestration wrapper.

---

## Experiment Dependencies

```
A1 (Decision Framework) -----> C1 (Section-Type Filtering) ----> C2 (Pre-Completion Aggregation)
A2 (Pre-Completion Checklist) ---^
A3 (Tables vs Prose)           [independent]
A4 (Enforcement Classification) [independent, observational]
B1 (CI Enforcement)            [independent]
B2 (Encounter Order)           [independent]
```

**Recommended execution order:**
1. **Phase 1 (parallel):** A1, A2, A3, A4, B1, B2 -- all independent, can run concurrently
2. **Phase 2 (contingent):** C1 -- only if A1 or A2 supported
3. **Phase 3 (contingent):** C2 -- only if A2 and C1 supported

**Shared infrastructure across experiments:**
- Worktree isolation (existing from H3)
- Invariant scoring rubric (existing from H3)
- rag_delete_source task prompt (existing from H3 Pilot 2)
- rag_stats task prompt (existing from H3 Pilot 1)

**Run budget:** ~57 subagent runs maximum (if all experiments execute). Phase 1 alone is ~51 runs. Sharing baseline conditions between A1/A2 reduces to ~45.

## Deliverables by Outcome

### If A1 supported (decision frameworks help Haiku)

**Template scope:**
- SPEC.md spec-template gains Decision Framework section
- Convention: each reasoning-required invariant gets a situation-keyed entry
- Linked to invariant IDs for traceability

**Ragling scope:**
- Parser: add `decision_framework` to `_SECTION_MAP`
- Re-index collections containing SPEC.md files

### If A2 supported (checklists reduce pattern violations)

**Template scope:**
- SPEC.md spec-template gains Pre-Completion Checklist section
- Convention: subsystem-specific verification items

**Ragling scope:**
- Parser: add `pre_completion_checklist` to `_SECTION_MAP`
- `rag_search_task`: add `task_type="pre_completion"` (contingent on C1/C2)

### If A3 supported (tables beat prose)

**Template scope:**
- SPEC.md convention: tables mandated for invariants, interfaces, dependencies, decision frameworks
- Document evidence in template's spec-rationale.md

**Ragling scope:** None -- format convention only.

### If A4 supported (enforcement classification is predictive)

**Template scope:**
- SPEC.md invariants table gains "Enforcement" column (Structural / Reasoning-required)
- Template guidance: prioritize converting reasoning-required to structural
- Quality metric: ratio of structural to reasoning-required invariants

**Ragling scope:**
- Parser: extract `enforcement` metadata from invariants table (future -- not needed for initial template change)

### If B1 supported (CI enforcement works)

**Template scope:**
- CONTRIBUTING.md gains structural enforcement test guidance
- Template ships example enforcement test patterns
- Convention: each subsystem SPEC.md documents which invariants have mechanical enforcement

**Ragling scope:**
- Ship enforcement tests for tools/ package as reference implementation

### If B2 supported (encounter order matters)

**Template scope:**
- SPEC.md gains "Canonical Example" field
- Skills that spawn subagents include canonical example path in prompt

**Ragling scope:**
- `rag_search_task`: add `task_type="example"` that retrieves canonical example for a subsystem
- Parser: extract canonical example path from SPEC.md metadata

### If C1 supported (section-type filtering works)

**Ragling scope:**
- `SearchFilters` gains `section_type` parameter
- `rag_search`, `rag_batch_search` expose section_type filter
- `rag_search_task` uses section_type for targeted retrieval

### If C2 supported (pre-completion aggregation reduces round-trips)

**Ragling scope:**
- `rag_search_task` `task_type="pre_completion"` ships
- Template skills gain pre-completion RAG call pattern
