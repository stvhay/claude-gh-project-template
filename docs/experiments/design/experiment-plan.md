# SPEC.md Template Experiments Implementation Plan

> **For Claude:** Execute this plan using subagent-driven-development (same session) or executing-plans (separate session / teammate).

**Goal:** Run 8 experiments validating SPEC.md format enhancements, structural enforcement, and RAG features. Produce results that specify implementation scope for the upstream template and ragling.

**Architecture:** Each experiment uses the H3 methodology: worktree-isolated subagents with controlled prompts, scored against an invariant rubric by a reviewer agent. Phase 1 experiments (A1-A4, B1-B2) are independent and parallelizable. Phase 2 (C1-C2) is contingent on Phase 1 results.

**Tech Stack:** Claude Code subagents (Haiku/Sonnet), git worktrees for isolation, existing ragling MCP tools for RAG conditions, reviewer agents for scoring.

**Acceptance Criteria -- what must be TRUE when this plan is done:**
- [ ] All Phase 1 experiments (A1, A2, A3, A4, B1, B2) have results documented in `docs/experiments/`
- [ ] Each experiment result states whether the null hypothesis is rejected, with evidence
- [ ] Each supported hypothesis has concrete implementation scope (template and/or ragling)
- [ ] Results summary posted as comment on issue #45

**Dependencies:** None -- all prior H3 infrastructure exists on branch `experiment/h3-pilot-45`.

---

### Task 1: Create Experiment Materials

**Context:** All experiments need SPEC.md variants, scoring rubrics, and prompt templates before any subagent runs. This task creates every material file so subsequent experiment tasks can reference them by path. The materials live in `docs/experiments/materials/` and are not committed -- they're experiment artifacts.

**Subsystem spec(s):** `src/ragling/SPEC.md` (Core -- source for SPEC variants)
**Key invariants from spec:** INV-3 (WAL mode), INV-4 (single-writer queue)
**Adjacent specs:** All 7 subsystem SPEC.md files (for full-dump condition concatenation)

**Files:**
- Create: `docs/experiments/materials/spec-baseline.md` (all 7 SPECs concatenated)
- Create: `docs/experiments/materials/spec-with-decision-framework.md` (A1 treatment)
- Create: `docs/experiments/materials/spec-with-checklist.md` (A2 treatment)
- Create: `docs/experiments/materials/spec-with-both.md` (A1+A2 combined treatment)
- Create: `docs/experiments/materials/spec-prose-invariants.md` (A3 prose condition)
- Create: `docs/experiments/materials/scoring-rubric-delete-source.md` (A1/A2/A3 rubric)
- Create: `docs/experiments/materials/scoring-rubric-stats.md` (B1/B2 rubric)
- Create: `docs/experiments/materials/enforcement-test.py` (B1 condition B/C test)
- Create: `docs/experiments/materials/prompts.md` (all experiment prompts)

**Depends on:** Independent

**Step 1: Create the materials directory**

Run: `mkdir -p docs/experiments/materials`

**Step 2: Concatenate all 7 SPEC.md files for baseline condition**

Concatenate these files in order, separated by `---`:
- `src/ragling/SPEC.md` (Core)
- `src/ragling/auth/SPEC.md`
- `src/ragling/document/SPEC.md`
- `src/ragling/indexers/SPEC.md`
- `src/ragling/parsers/SPEC.md`
- `src/ragling/search/SPEC.md`
- `src/ragling/watchers/SPEC.md`

Save to `docs/experiments/materials/spec-baseline.md`.

**Step 3: Create A1 treatment SPEC (Decision Framework)**

Copy `spec-baseline.md`. After the `## Invariants` section in the Core spec, insert:

```markdown
## Decision Framework

| Situation | Action | Invariant |
|---|---|---|
| Need to write to the index database | Submit `IndexJob` to `IndexingQueue` via `queue.submit()` or `queue.submit_and_wait()`; never call DB write functions directly from MCP tool handlers | INV-4 |
| Need a database connection | Call `get_connection()` + `init_db()`; never use raw `sqlite3.connect()` | INV-3 |
| Implementing a new MCP tool | Create `tools/<name>.py` with `register(mcp, ctx: ToolContext)` function; import and register in `tools/__init__.py` | -- |
| Tool needs to trigger indexing or deletion | Call `ctx.queue_getter()` to get the queue; if None, return `{"error": "No indexing queue available (read-only follower)"}` | INV-4 |
| Tool needs to delete a source | Submit `IndexJob` with `indexer_type=IndexerType.PRUNE` and `job_type="file_deleted"` to the queue; the IndexingQueue worker calls `delete_source()` | INV-4, Idx-INV-1 |
| Tool needs to read from the database | Use `get_connection()` + `init_db()` on a separate connection; read-only queries are safe on WAL connections | INV-3 |
```

Save to `docs/experiments/materials/spec-with-decision-framework.md`.

**Step 4: Create A2 treatment SPEC (Pre-Completion Checklist)**

Copy `spec-baseline.md`. After the `## Failure Modes` section in Core spec, insert:

```markdown
## Pre-Completion Checklist

Before claiming implementation is complete, verify each item:

| Check | How to Verify |
|---|---|
| Tool uses `@mcp.tool()` decorator | Decorator present and uncommented on the tool function |
| Tool catches exceptions and returns `{"error": ...}` | Try/except wraps main logic; except block returns error dict |
| Database connections closed in `finally` block | `conn.close()` in a finally block, not just at end of function |
| Write operations route through IndexingQueue | No direct INSERT/UPDATE/DELETE in tool code; writes submitted as IndexJob |
| Follower mode handled | `ctx.queue_getter()` called; if returns None, tool returns error |
| Tool file follows `register(mcp, ctx)` pattern | Function signature is `def register(mcp: FastMCP, ctx: ToolContext) -> None` |
| Tool registered in `__init__.py` | Module imported and `register()` called in `register_all_tools()` |
```

Save to `docs/experiments/materials/spec-with-checklist.md`.

**Step 5: Create A1+A2 combined treatment SPEC**

Copy `spec-baseline.md`. Insert both the Decision Framework (after Invariants) and Pre-Completion Checklist (after Failure Modes) sections.

Save to `docs/experiments/materials/spec-with-both.md`.

**Step 6: Create A3 prose condition SPEC**

Copy `spec-baseline.md`. Replace the Core `## Invariants` table with a prose paragraph containing the same information:

```markdown
## Invariants

The Config object is a frozen dataclass; any attempt to mutate it raises FrozenInstanceError, which prevents race conditions across threads. The load_config() function never raises on malformed input and returns a default Config instead, ensuring the server can start even with a broken config file. All SQLite databases must use WAL journal mode with retry on first access, because multiple MCP instances read concurrently and WAL avoids reader/writer blocking. Only the IndexingQueue worker thread is permitted to write to the per-group index database; the MCP rag_index tool requires a running queue and direct indexing has been removed, which eliminates write contention so no locking is needed in indexers. The DocStore keys documents by SHA-256 file hash combined with config_hash, ensuring identical content is never converted twice and avoiding redundant Docling conversions that can take minutes per document. The LeaderLock uses fcntl.flock() and the kernel releases the lock when the process dies, so there are no stale locks, no PID files, and no heartbeat mechanism needed. Embedding batch failures fall back to individual embedding with truncation retry, because one bad text in a batch must not block the entire batch.
```

Save to `docs/experiments/materials/spec-prose-invariants.md`.

**Step 7: Create scoring rubric for rag_delete_source experiments**

```markdown
# Scoring Rubric: rag_delete_source

Score each item PASS / FAIL / PARTIAL / N/A.

| ID | Check | PASS | FAIL | PARTIAL |
|---|---|---|---|---|
| Core-INV-4 | Single-writer: writes via queue only | Submits IndexJob to queue, returns immediately | Direct delete_source() or DELETE SQL from handler | Imports IndexJob, attempts queue, but falls back to direct write |
| Core-INV-3 | WAL mode via helpers | Uses get_connection()+init_db() | Raw sqlite3.connect() | -- |
| Idx-INV-1 | Atomic delete | Delegates to existing delete_source() | Hand-rolled DELETE statements | -- |
| MCP-pattern | Registration pattern | @mcp.tool() decorator, register(mcp, ctx) | Missing decorator, code in wrong file | Decorator commented out |
| Error-handling | Exception handling | Try/except returns {"error": ...} | Unhandled exceptions | Partial coverage |
| Conn-lifecycle | Connection cleanup | conn.close() in finally | No finally block | Close without finally |
| Follower-mode | Read-only follower | Checks _get_queue()/ctx.queue_getter(), errors if None | No queue check | Checks but doesn't error |

**Summary metrics:**
- Hard fails: count of FAIL
- Pattern violations: count of FAIL on MCP-pattern + Error-handling + Conn-lifecycle
- Invariant violations: count of FAIL on Core-INV-4 + Core-INV-3 + Idx-INV-1
```

Save to `docs/experiments/materials/scoring-rubric-delete-source.md`.

**Step 8: Create scoring rubric for rag_stats experiments**

```markdown
# Scoring Rubric: rag_stats

| ID | Check | PASS | FAIL |
|---|---|---|---|
| Location | Tool in tools/stats.py | File is tools/stats.py or tools/<name>.py | Code added to mcp_server.py or other location |
| Register | Uses register(mcp, ctx) | Function signature matches | Other pattern |
| Self-correct | If blocked by test/hook, did agent fix? | Moved code to correct location | Gave up, disabled test, or modified hook |
| MCP-pattern | @mcp.tool() decorator | Present and functional | Missing or commented |
| Structural-similarity | Follows canonical example structure | File structure matches tools/search.py | Significantly different structure |
```

Save to `docs/experiments/materials/scoring-rubric-stats.md`.

**Step 9: Create enforcement test for B1**

```python
"""Structural enforcement tests for tools/ package.

These tests verify that MCP tools follow the register() pattern
and are not added directly to mcp_server.py.
"""
import ast
import importlib
from pathlib import Path


def test_no_mcp_tool_decorator_in_mcp_server():
    """mcp_server.py must not contain @mcp.tool() decorators."""
    server_path = Path("src/ragling/mcp_server.py")
    content = server_path.read_text()
    tree = ast.parse(content)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    func = decorator.func
                    if isinstance(func, ast.Attribute) and func.attr == "tool":
                        raise AssertionError(
                            f"Found @mcp.tool() decorator on {node.name} in mcp_server.py. "
                            f"Tools must be in src/ragling/tools/<name>.py with register(mcp, ctx) pattern."
                        )


def test_all_tool_modules_export_register():
    """Every .py file in tools/ (except __init__.py, context.py, helpers.py) must export register()."""
    tools_dir = Path("src/ragling/tools")
    skip = {"__init__.py", "context.py", "helpers.py"}
    for py_file in sorted(tools_dir.glob("*.py")):
        if py_file.name in skip:
            continue
        module_name = f"ragling.tools.{py_file.stem}"
        mod = importlib.import_module(module_name)
        assert hasattr(mod, "register"), (
            f"{module_name} does not export register(). "
            f"All tool modules must define: def register(mcp: FastMCP, ctx: ToolContext) -> None"
        )


def test_mcp_server_has_no_tool_functions():
    """mcp_server.py should only define create_server(), no other public functions."""
    server_path = Path("src/ragling/mcp_server.py")
    content = server_path.read_text()
    tree = ast.parse(content)
    public_functions = [
        node.name for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    ]
    assert public_functions == ["create_server"], (
        f"mcp_server.py defines public functions {public_functions}. "
        f"Only create_server() should be defined here. Tools go in tools/<name>.py."
    )
```

Save to `docs/experiments/materials/enforcement-test.py`.

**Step 10: Create all experiment prompts**

Write a file containing the exact prompt text for each experiment condition. Each prompt includes:
- The task description
- The SPEC.md context injection (reference to which material file to prepend)
- Instructions about file access and SPEC.md reading
- The model to use

```markdown
# Experiment Prompts

## Task: rag_delete_source (used by A1, A2, A3)

> Add a `rag_delete_source` MCP tool that removes a source and its
> documents/embeddings from a collection.
>
> Requirements:
> - Accept collection name and source URI as parameters
> - Verify the source exists before attempting deletion
> - Handle errors gracefully and return descriptive error messages
> - Follow existing tool patterns (read tools/index.py and
>   src/ragling/indexing_queue.py for the write pattern)
>
> Do NOT read any SPEC.md files directly. Use only the specification
> context provided below.
>
> Write your implementation to src/ragling/tools/delete_source.py
> and register it in tools/__init__.py.

### Condition injection

Prepend the relevant spec material file content before the task text:
- A1-baseline / A2-baseline / A3-table: `spec-baseline.md`
- A1-treatment: `spec-with-decision-framework.md`
- A2-treatment: `spec-with-checklist.md`
- A3-prose: `spec-prose-invariants.md`

## Task: rag_stats (used by B1, B2)

> Add a `rag_stats` MCP tool that returns per-collection indexing
> statistics including source count, chunk count, and last indexed
> timestamp.
>
> Requirements:
> - Return statistics for all visible collections
> - Include aggregate totals
> - Handle empty database gracefully
> - Follow existing tool patterns

### Condition injection

- B1-A / B2-A (uncontrolled): No spec context. No file reading restrictions.
- B1-B (docs + test): No spec context. Copy enforcement-test.py to
  tests/test_enforcement.py in the worktree before launching.
- B1-C (docs + test + hook): Same as B1-B plus add pre-commit hook
  that runs the enforcement test.
- B2-B (SPEC pointer): Prepend "Canonical example: read tools/search.py
  first for the registration pattern." before the task.
- B2-C (explicit instruction): Prepend "Read tools/search.py first for
  the registration pattern, then implement your tool." before the task.
```

Save to `docs/experiments/materials/prompts.md`.

**Step 11: Verify all materials**

Run: `ls -la docs/experiments/materials/`

Expected: 10 files (spec-baseline.md, spec-with-decision-framework.md, spec-with-checklist.md, spec-with-both.md, spec-prose-invariants.md, scoring-rubric-delete-source.md, scoring-rubric-stats.md, enforcement-test.py, prompts.md).

**Step 12: Commit**

```bash
git add docs/experiments/materials/
git commit -m "experiment: create materials for SPEC.md template experiments

Spec variants: baseline, decision-framework, checklist, combined,
prose-invariants. Scoring rubrics for delete-source and stats tasks.
Enforcement test for B1. Prompt templates for all conditions.

Ref: #45"
```

---

### Task 2: Run Experiment A1 -- Decision Framework

**Context:** Tests whether a situation-keyed Decision Framework section in SPEC.md improves Haiku's INV-4 compliance on a write task. The rag_delete_source task was chosen because Haiku universally failed INV-4 (0/6) in H3 pilots regardless of context format. If decision frameworks bridge the capability gap, Haiku should achieve >= 2/3 PASS on INV-4 in the treatment condition.

Two conditions (baseline, treatment) x two models (Haiku, Sonnet) x 3 runs = 12 runs total. Baseline runs are shared with A2.

**Subsystem spec(s):** `src/ragling/SPEC.md` (Core)
**Key invariants from spec:** INV-4 (single-writer), INV-3 (WAL mode)
**Adjacent specs:** `src/ragling/indexers/SPEC.md` (INV-1 atomic delete)

**Files:**
- Read: `docs/experiments/materials/spec-baseline.md` (condition A context)
- Read: `docs/experiments/materials/spec-with-decision-framework.md` (condition B context)
- Read: `docs/experiments/materials/scoring-rubric-delete-source.md` (rubric)
- Read: `docs/experiments/materials/prompts.md` (task prompt)
- Create: `docs/experiments/a1-decision-framework-results.md` (results)

**Depends on:** Task 1

**Step 1: Run baseline condition (Haiku) -- 3 runs**

For each run (A1-H-Base-Run1, A1-H-Base-Run2, A1-H-Base-Run3):

1. Create an isolated worktree:
   ```bash
   git worktree add .claude/worktrees/a1-h-base-runN -b experiment/a1-h-base-runN
   ```

2. Launch a Haiku subagent in the worktree with the task prompt from `prompts.md` (rag_delete_source task). Prepend the content of `spec-baseline.md` before the task text. Use `--model claude-haiku-4-5-20251001`.

3. When the subagent completes, save its output (the implementation file) and note total tokens used and tool call count.

4. Launch a reviewer agent (Sonnet) with:
   - The scoring rubric from `scoring-rubric-delete-source.md`
   - The implementation file produced by the subagent
   - Instructions: "Score this implementation against the rubric. Return a table with each check ID, the score (PASS/FAIL/PARTIAL/N/A), and a one-line justification."

5. Record the scores in a results table.

6. Clean up: `git worktree remove .claude/worktrees/a1-h-base-runN`

**Step 2: Run treatment condition (Haiku) -- 3 runs**

Same as Step 1, but prepend `spec-with-decision-framework.md` instead of `spec-baseline.md`. Use run names A1-H-Treat-Run1 through A1-H-Treat-Run3.

**Step 3: Run baseline condition (Sonnet) -- 3 runs**

Same as Step 1, but use `--model claude-sonnet-4-6`. Run names A1-S-Base-Run1 through A1-S-Base-Run3. These are the control -- Sonnet should remain at ceiling.

**Step 4: Run treatment condition (Sonnet) -- 3 runs**

Same as Step 3, but prepend `spec-with-decision-framework.md`. Run names A1-S-Treat-Run1 through A1-S-Treat-Run3.

**Step 5: Compile results**

Create `docs/experiments/a1-decision-framework-results.md` with:

```markdown
# A1: Decision Framework Section -- Results

**Hypothesis (H8):** Decision frameworks improve Haiku INV-4 compliance.
**Null hypothesis:** No effect on compliance.

## Results

| Run | Model | Condition | INV-4 | INV-3 | Idx-INV-1 | MCP-pattern | Error | Conn | Follower | Violations |
|---|---|---|---|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

## Summary

| Metric | Haiku Baseline | Haiku Treatment | Sonnet Baseline | Sonnet Treatment |
|---|---|---|---|---|
| INV-4 pass rate | /3 | /3 | /3 | /3 |
| Mean violations | | | | |
| Total tokens | | | | |

## Hypothesis Status

**[SUPPORTED / NOT SUPPORTED]**

[Analysis: does treatment move Haiku above 0/3 baseline on INV-4?
Does Sonnet remain at ceiling? What explains the result?]

## Implementation Scope (if supported)

- Template: SPEC.md spec-template gains Decision Framework section
- Ragling: parser adds `decision_framework` to `_SECTION_MAP`

## Implementation Scope (if not supported)

- Decision frameworks do not bridge the Haiku capability gap
- Structural enforcement (B1) may be the only viable path
```

**Step 6: Commit**

```bash
git add docs/experiments/a1-decision-framework-results.md
git commit -m "experiment: A1 decision framework results -- [SUPPORTED/NOT SUPPORTED]

Ref: #45"
```

---

### Task 3: Run Experiment A2 -- Pre-Completion Checklist

**Context:** Tests whether a pre-completion checklist in SPEC.md reduces pattern violations (MCP-pattern, error handling, connection lifecycle). H3 pilots showed pattern violations in 4/24 runs across all models. The checklist provides explicit self-review triggers. Shares baseline runs with A1 to reduce total run count.

Two conditions x two models x 3 runs = 12 total, minus 6 shared baselines = 6 new runs.

**Subsystem spec(s):** `src/ragling/SPEC.md` (Core)
**Key invariants from spec:** INV-4 (single-writer), INV-3 (WAL mode)
**Adjacent specs:** `src/ragling/indexers/SPEC.md` (INV-1 atomic delete)

**Files:**
- Read: `docs/experiments/a1-decision-framework-results.md` (for shared baseline scores)
- Read: `docs/experiments/materials/spec-with-checklist.md` (treatment context)
- Read: `docs/experiments/materials/scoring-rubric-delete-source.md` (rubric)
- Read: `docs/experiments/materials/prompts.md` (task prompt)
- Create: `docs/experiments/a2-pre-completion-checklist-results.md`

**Depends on:** Task 1, Task 2 (for shared baseline runs)

**Step 1: Reuse A1 baseline runs**

Copy the baseline condition scores from A1 results (both Haiku and Sonnet baselines). These serve as the A2 baseline -- same SPEC, same task, same models.

**Step 2: Run treatment condition (Haiku) -- 3 runs**

For each run (A2-H-Treat-Run1 through A2-H-Treat-Run3):

1. Create worktree: `git worktree add .claude/worktrees/a2-h-treat-runN -b experiment/a2-h-treat-runN`
2. Launch Haiku subagent with `spec-with-checklist.md` prepended before task prompt.
3. Score with reviewer agent using `scoring-rubric-delete-source.md`.
4. Record scores.
5. Clean up worktree.

**Step 3: Run treatment condition (Sonnet) -- 3 runs**

Same as Step 2, but with Sonnet. Run names A2-S-Treat-Run1 through A2-S-Treat-Run3.

**Step 4: Compile results**

Create `docs/experiments/a2-pre-completion-checklist-results.md` with same structure as A1, but focused on pattern violation metrics:

```markdown
# A2: Pre-Completion Checklist -- Results

**Hypothesis (H9):** Checklists reduce pattern violations across models.
**Null hypothesis:** No effect on pattern violations.

## Results

[Table with all runs including shared baselines]

## Pattern Violation Analysis

| Metric | Baseline | Treatment | Delta |
|---|---|---|---|
| Haiku mean pattern violations | | | |
| Sonnet mean pattern violations | | | |
| Combined mean pattern violations | | | |

## Hypothesis Status

**[SUPPORTED / NOT SUPPORTED]**

[Analysis: >= 50% reduction in pattern violations?]

## Implementation Scope (if supported)

- Template: SPEC.md spec-template gains Pre-Completion Checklist section
- Ragling: parser adds `pre_completion_checklist` to `_SECTION_MAP`
- Ragling: `rag_search_task` gains `task_type="pre_completion"` (contingent on C1)
```

**Step 5: Commit**

```bash
git add docs/experiments/a2-pre-completion-checklist-results.md
git commit -m "experiment: A2 pre-completion checklist results -- [SUPPORTED/NOT SUPPORTED]

Ref: #45"
```

---

### Task 4: Run Experiment A3 -- Tables vs Prose

**Context:** Tests whether table-formatted invariants produce higher compliance than prose-formatted invariants. Zig-learner's meta-log tracked this: tables outperformed prose for reference material. Ragling already uses tables; this validates the convention before mandating it in the template. Sonnet-only (6 runs) since format effects would only show above the capability floor.

**Subsystem spec(s):** `src/ragling/SPEC.md` (Core)
**Key invariants from spec:** INV-4 (single-writer), INV-3 (WAL mode)
**Adjacent specs:** `src/ragling/indexers/SPEC.md`

**Files:**
- Read: `docs/experiments/materials/spec-baseline.md` (table condition)
- Read: `docs/experiments/materials/spec-prose-invariants.md` (prose condition)
- Read: `docs/experiments/materials/scoring-rubric-delete-source.md`
- Read: `docs/experiments/materials/prompts.md`
- Create: `docs/experiments/a3-tables-vs-prose-results.md`

**Depends on:** Task 1

**Step 1: Run table condition (Sonnet) -- 3 runs**

Can reuse A1 Sonnet baseline runs if available. Otherwise, for each run (A3-S-Table-Run1 through A3-S-Table-Run3):

1. Create worktree, launch Sonnet subagent with `spec-baseline.md` prepended.
2. Score with reviewer agent.
3. Record scores.

**Step 2: Run prose condition (Sonnet) -- 3 runs**

For each run (A3-S-Prose-Run1 through A3-S-Prose-Run3):

1. Create worktree: `git worktree add .claude/worktrees/a3-s-prose-runN -b experiment/a3-s-prose-runN`
2. Launch Sonnet subagent with `spec-prose-invariants.md` prepended before task prompt.
3. Score with reviewer agent using `scoring-rubric-delete-source.md`.
4. Record scores.
5. Clean up worktree.

**Step 3: Compile results**

Create `docs/experiments/a3-tables-vs-prose-results.md`:

```markdown
# A3: Tables vs Prose for Invariants -- Results

**Hypothesis (H10):** Table format produces higher invariant compliance than prose.
**Null hypothesis:** Format has no effect.

## Results

| Run | Condition | INV-4 | INV-3 | Idx-INV-1 | MCP-pattern | Error | Conn | Follower | Violations |
|---|---|---|---|---|---|---|---|---|---|
| ... | Table | ... | ... | ... | ... | ... | ... | ... | ... |
| ... | Prose | ... | ... | ... | ... | ... | ... | ... | ... |

## Hypothesis Status

**[SUPPORTED / NOT SUPPORTED]**

[Does prose condition show >= 1 INV-4 FAIL or higher pattern violations?]

## Implementation Scope

- If supported: template mandates table format for invariants and interfaces
- If not supported: tables are convention (readability/RAG), not performance requirement
```

**Step 4: Commit**

```bash
git add docs/experiments/a3-tables-vs-prose-results.md
git commit -m "experiment: A3 tables vs prose results -- [SUPPORTED/NOT SUPPORTED]

Ref: #45"
```

---

### Task 5: Run Experiment A4 -- Enforcement Classification (Observational)

**Context:** Tests whether classifying invariants as "structural" vs "reasoning-required" correctly predicts which invariants models fail. This is observational -- no new subagent runs for the retrodiction phase. Uses existing H3 data (24 runs across Haiku/Sonnet/Opus). Extension phase runs Haiku on 2-3 new invariants to test out-of-sample prediction.

**Subsystem spec(s):** All 7 subsystem SPEC.md files
**Key invariants from spec:** All invariants scored in H3 pilots

**Files:**
- Read: `docs/experiments/h3-pilot-design.md` (H3 scoring data)
- Read: `docs/experiments/h3-pilot-findings.md` (H3 results)
- Create: `docs/experiments/a4-enforcement-classification-results.md`

**Depends on:** Independent

**Step 1: Classify all H3-scored invariants**

Create the classification table:

| Invariant | Enforcement | Rationale |
|---|---|---|
| Core-INV-3 (WAL mode) | Structural | `get_connection()` sets WAL; no alternative path to raw sqlite3 |
| Core-INV-4 (single-writer) | Reasoning-required | Agent must understand queue architecture; direct writes compile and run |
| Idx-INV-1 (atomic delete) | Structural | `delete_source()` exists as a callable function; agents use it naturally |
| MCP-pattern (@mcp.tool) | Structural | Decorator is visible in every tool file; pattern-matchable |
| Error-handling | Reasoning-required | Agent must decide to add try/except; not enforced by framework |
| Conn-lifecycle | Structural | Pattern visible in every tool file (try/finally with conn.close()) |
| Follower-mode | Reasoning-required | Agent must understand leader/follower architecture |

**Step 2: Retrodict H3 outcomes**

For each of the 24 H3 runs, predict:
- Structural invariants: PASS regardless of model
- Reasoning-required invariants: PASS for Sonnet/Opus, FAIL for Haiku

Compare predictions to actual H3 results from `h3-pilot-design.md`.

Calculate: retrodiction accuracy = correct predictions / total predictions.

**Step 3: Extension -- identify new invariants**

Find 2-3 invariants in ragling not tested in H3. Classify them. Design a minimal task that touches them. Run Haiku 3 times. Check if classification predicts outcomes.

Candidate invariants:
- INV-9 (embedding batch fallback) -- Structural (fallback is in `get_embeddings()`)
- INV-2 (load_config never raises) -- Structural (function handles internally)
- INV-5 (DocStore content-addressed cache) -- Reasoning-required (agent must understand content-addressing)

Task for extension: "Add an MCP tool that re-indexes a single document by path, updating its embeddings if the content has changed."

Run 3 Haiku instances. Score against the new invariants. Check predictions.

**Step 4: Compile results**

Create `docs/experiments/a4-enforcement-classification-results.md`:

```markdown
# A4: Enforcement Classification -- Results

**Hypothesis (revised H6):** Structural/reasoning classification predicts invariant violations.
**Null hypothesis:** Classification has no predictive value.

## Classification

[Table from Step 1]

## Retrodiction (H3 data, n=24 runs)

| Prediction | Correct | Incorrect | Accuracy |
|---|---|---|---|
| Structural -> PASS | /N | /N | % |
| Reasoning (Haiku) -> FAIL | /N | /N | % |
| Reasoning (Sonnet/Opus) -> PASS | /N | /N | % |
| **Total** | /N | /N | **%** |

## Extension (new invariants, n=3 Haiku runs)

[Results table]

## Hypothesis Status

**[SUPPORTED / NOT SUPPORTED]**

[>= 90% retrodiction accuracy? >= 2/3 extension predictions correct?]

## Implementation Scope (if supported)

- Template: invariants table gains "Enforcement" column
- Guidance: prioritize converting reasoning-required to structural
```

**Step 5: Commit**

```bash
git add docs/experiments/a4-enforcement-classification-results.md
git commit -m "experiment: A4 enforcement classification results -- [SUPPORTED/NOT SUPPORTED]

Ref: #45"
```

---

### Task 6: Run Experiment B1 -- CI Enforcement vs Documentation

**Context:** Tests whether mechanical enforcement (tests that reject wrong-location code) prevents pattern violations that docs alone do not. The VSA experiment showed Sonnet ignoring SPEC.md and putting tools in `mcp_server.py` 2/2 times. This experiment adds a test (condition B) or test+hook (condition C) that fails when tools are in the wrong location, and checks whether Sonnet self-corrects.

Three conditions x two models x 3 runs = 18 total.

**Subsystem spec(s):** `src/ragling/SPEC.md` (Core), `src/ragling/tools/` package
**Key invariants from spec:** Tools follow register(mcp, ctx) pattern
**Adjacent specs:** None

**Files:**
- Read: `docs/experiments/materials/enforcement-test.py` (B/C condition test)
- Read: `docs/experiments/materials/scoring-rubric-stats.md`
- Read: `docs/experiments/materials/prompts.md`
- Create: `docs/experiments/b1-ci-enforcement-results.md`

**Depends on:** Task 1

**Step 1: Run condition A (docs only) -- 3 runs per model**

For each run (B1-{H,S}-DocsOnly-Run{1,2,3}):

1. Create worktree.
2. Ensure SPEC.md and CLAUDE.md describe the tools/ pattern (already true on this branch).
3. Launch subagent with rag_stats task prompt. No enforcement test present.
4. Score: did the agent create `tools/stats.py` with `register()`, or did it modify `mcp_server.py`?
5. Record location, register pattern, MCP-pattern scores.

**Step 2: Run condition B (docs + test) -- 3 runs per model**

For each run (B1-{H,S}-DocsTest-Run{1,2,3}):

1. Create worktree.
2. Copy `docs/experiments/materials/enforcement-test.py` to `tests/test_enforcement.py` in the worktree.
3. Launch subagent with rag_stats task prompt. The test is discoverable but not mentioned in the prompt.
4. Score: location, register pattern, and if the test blocked the agent, did it self-correct?

**Step 3: Run condition C (docs + test + hook) -- 3 runs per model**

For each run (B1-{H,S}-DocsTestHook-Run{1,2,3}):

1. Create worktree.
2. Copy enforcement test to `tests/test_enforcement.py`.
3. Add a pre-commit hook to `.git/hooks/pre-commit` in the worktree:
   ```bash
   #!/bin/bash
   cd "$(git rev-parse --show-toplevel)"
   python -m pytest tests/test_enforcement.py -q --tb=short
   ```
   Make it executable: `chmod +x .git/hooks/pre-commit`
4. Launch subagent with rag_stats task prompt.
5. Score: location, register pattern, self-correction behavior.

**Step 4: Compile results**

Create `docs/experiments/b1-ci-enforcement-results.md`:

```markdown
# B1: CI Enforcement vs Documentation -- Results

**Hypothesis (H4):** Mechanical enforcement prevents violations docs alone do not.
**Null hypothesis:** Docs are equally effective.

## Results

| Run | Model | Condition | Location | Register | Self-Correct | MCP-pattern |
|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | ... |

## Summary

| Condition | Sonnet Location PASS | Haiku Location PASS |
|---|---|---|
| A (docs only) | /3 | /3 |
| B (docs + test) | /3 | /3 |
| C (docs + test + hook) | /3 | /3 |

## Self-Correction Behavior

[If the test/hook blocked the agent: what did it do?
- Moved code to correct location?
- Disabled the test?
- Modified the hook?
- Gave up?]

## Hypothesis Status

**[SUPPORTED / NOT SUPPORTED]**

## Implementation Scope (if supported)

- Template: CONTRIBUTING.md gains structural enforcement test guidance
- Template: ships example enforcement test patterns
- Ragling: enforcement tests for tools/ package as reference
```

**Step 5: Commit**

```bash
git add docs/experiments/b1-ci-enforcement-results.md
git commit -m "experiment: B1 CI enforcement results -- [SUPPORTED/NOT SUPPORTED]

Ref: #45"
```

---

### Task 7: Run Experiment B2 -- Encounter Order Control

**Context:** Tests whether the first file an agent reads determines its output pattern. The VSA experiment showed Sonnet reading `mcp_server.py` first and pattern-matching on it. If directed to read `tools/search.py` first, it should produce tool-shaped code. Three conditions x Sonnet only x 3 runs = 9 total. Can share condition A runs with B1.

**Subsystem spec(s):** `src/ragling/SPEC.md`, `src/ragling/tools/` package
**Key invariants from spec:** Tools follow register(mcp, ctx) pattern

**Files:**
- Read: `docs/experiments/materials/scoring-rubric-stats.md`
- Read: `docs/experiments/materials/prompts.md`
- Read: `src/ragling/tools/search.py` (canonical example)
- Create: `docs/experiments/b2-encounter-order-results.md`

**Depends on:** Task 1 (can share B1 condition A runs if B1 runs first)

**Step 1: Run condition A (uncontrolled) -- 3 Sonnet runs**

Reuse B1 Sonnet docs-only runs if available. Otherwise, run identically to B1 condition A with Sonnet.

**Step 2: Run condition B (SPEC.md pointer) -- 3 Sonnet runs**

For each run (B2-S-SpecPtr-Run{1,2,3}):

1. Create worktree.
2. In the worktree, add to the top of `src/ragling/SPEC.md` under Core Mechanism:
   ```
   **Canonical example:** `tools/search.py` demonstrates the standard tool registration pattern.
   ```
3. Launch Sonnet subagent with rag_stats task prompt (no explicit file reading instruction).
4. Score with rubric.

**Step 3: Run condition C (explicit instruction) -- 3 Sonnet runs**

For each run (B2-S-Explicit-Run{1,2,3}):

1. Create worktree (no SPEC.md modification).
2. Launch Sonnet subagent with modified task prompt that prepends:
   "Read `src/ragling/tools/search.py` first for the registration pattern, then implement your tool."
3. Score with rubric.

**Step 4: Compile results**

Create `docs/experiments/b2-encounter-order-results.md`:

```markdown
# B2: Encounter Order Control -- Results

**Hypothesis (H5):** First file encountered determines output pattern.
**Null hypothesis:** Encounter order has no effect.

## Results

| Run | Condition | Location | Register | Structural Similarity |
|---|---|---|---|---|
| ... | A (uncontrolled) | ... | ... | ... |
| ... | B (SPEC pointer) | ... | ... | ... |
| ... | C (explicit instruction) | ... | ... | ... |

## Summary

| Condition | Location PASS | Register PASS |
|---|---|---|
| A (uncontrolled) | /3 | /3 |
| B (SPEC pointer) | /3 | /3 |
| C (explicit instruction) | /3 | /3 |

## Hypothesis Status

**[SUPPORTED / NOT SUPPORTED]**

## Implementation Scope (if supported)

- Template: SPEC.md gains "Canonical Example" field
- Template: subagent-spawning skills include canonical example path
- Ragling: rag_search_task gains task_type="example"
```

**Step 5: Commit**

```bash
git add docs/experiments/b2-encounter-order-results.md
git commit -m "experiment: B2 encounter order results -- [SUPPORTED/NOT SUPPORTED]

Ref: #45"
```

---

### Task 8: Compile Results and Determine Scope

**Context:** After all Phase 1 experiments complete, compile results into a summary that maps each hypothesis to its outcome and the concrete implementation scope it unlocks (or doesn't). Post as a comment on issue #45. Determine whether Phase 2 (C1, C2) should proceed based on A1/A2 results.

**Files:**
- Read: `docs/experiments/a1-decision-framework-results.md`
- Read: `docs/experiments/a2-pre-completion-checklist-results.md`
- Read: `docs/experiments/a3-tables-vs-prose-results.md`
- Read: `docs/experiments/a4-enforcement-classification-results.md`
- Read: `docs/experiments/b1-ci-enforcement-results.md`
- Read: `docs/experiments/b2-encounter-order-results.md`
- Create: `docs/experiments/phase1-summary.md`

**Depends on:** Tasks 2, 3, 4, 5, 6, 7

**Step 1: Compile hypothesis status table**

```markdown
# Phase 1 Experiment Summary

| Experiment | Hypothesis | Status | Key Evidence |
|---|---|---|---|
| A1 | Decision frameworks improve Haiku INV-4 | [SUPPORTED/NOT] | [one-line summary] |
| A2 | Checklists reduce pattern violations | [SUPPORTED/NOT] | [one-line summary] |
| A3 | Tables beat prose for invariant compliance | [SUPPORTED/NOT] | [one-line summary] |
| A4 | Enforcement classification is predictive | [SUPPORTED/NOT] | [one-line summary] |
| B1 | CI enforcement beats documentation | [SUPPORTED/NOT] | [one-line summary] |
| B2 | Encounter order affects output pattern | [SUPPORTED/NOT] | [one-line summary] |
```

**Step 2: Determine template implementation scope**

For each supported hypothesis, list the specific template changes from the design doc's "Deliverables by Outcome" section.

**Step 3: Determine ragling feature scope**

For each supported hypothesis, list the specific ragling changes.

**Step 4: Determine Phase 2 go/no-go**

- If A1 or A2 supported: proceed with C1 (section-type filtering)
- If A2 and C1 both supported: proceed with C2 (pre-completion aggregation)
- If neither A1 nor A2 supported: Phase 2 is not needed

**Step 5: Post summary to issue #45**

```bash
gh issue comment 45 --body "$(cat docs/experiments/phase1-summary.md)" --repo aihaysteve/local-rag
```

**Step 6: Commit**

```bash
git add docs/experiments/phase1-summary.md
git commit -m "experiment: Phase 1 summary -- [N/6 hypotheses supported]

Template scope: [brief list]
Ragling scope: [brief list]
Phase 2: [GO/NO-GO]

Ref: #45"
```
