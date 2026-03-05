# B2: Encounter Order Control -- Results

**Hypothesis (H5):** First file encountered determines output pattern.
**Null hypothesis:** Encounter order has no effect.

## Results

| Run | Condition | Location | Register | MCP-pattern | Structural-similarity | Read search.py? |
|---|---|---|---|---|---|---|
| B1-S-A-1 | A (uncontrolled) | PASS | PASS | PASS | PASS | [unknown] |
| B1-S-A-2 | A (uncontrolled) | PASS | PASS | PASS | PASS | [unknown] |
| B1-S-A-3 | A (uncontrolled) | PASS | PASS | PASS | PASS | [unknown] |
| B2-S-B-1 | B (SPEC pointer) | PASS | PASS | PASS | PASS | [unknown — `-p` mode only shows summary] |
| B2-S-B-2 | B (SPEC pointer) | PASS | PASS | PASS | PASS | [unknown — `-p` mode only shows summary] |
| B2-S-B-3 | B (SPEC pointer) | PASS | PASS | PASS | PASS | [unknown — `-p` mode only shows summary] |
| B2-S-C-1 | C (explicit instruction) | PASS | PASS | PASS | PASS | [unknown — `-p` mode only shows summary] |
| B2-S-C-2 | C (explicit instruction) | PASS | PASS | PASS | PASS | [unknown — `-p` mode only shows summary] |
| B2-S-C-3 | C (explicit instruction) | PASS | PASS | PASS | PASS | [unknown — `-p` mode only shows summary] |

## Summary

| Condition | Location PASS | Register PASS | MCP-pattern PASS | Structural-similarity PASS |
|---|---|---|---|---|
| A (uncontrolled) | 3/3 | 3/3 | 3/3 | 3/3 |
| B (SPEC pointer) | 3/3 | 3/3 | 3/3 | 3/3 |
| C (explicit instruction) | 3/3 | 3/3 | 3/3 | 3/3 |

## Encounter Order Analysis

**Observability limitation:** The `claude -p` (pipe mode) used for automated runs only outputs a final summary. Individual tool calls (file reads) are not visible in the output. Therefore, we cannot determine from the captured output whether any agent read `tools/search.py` specifically, or what files it read first.

**Structural observations across runs:**

- **B2-S-B-1/B-2/C-1/C-2:** Used a single SQL query with correlated subqueries (the more sophisticated approach). Identical structure across conditions B and C.
- **B2-S-B-3:** Extracted a `_compute_stats()` helper function — slightly more modular but otherwise same pattern.
- **B2-S-C-3:** Used individual per-collection SQL queries in a loop — matches the pattern of the *original* `stats.py` that was on the branch (which was deleted before the run). This is notable as the most structurally different output, and it appeared under condition C (explicit instruction to read search.py), not under the uncontrolled condition.

**All 6 runs produced nearly identical output.** The file structure, import pattern, `register(mcp, ctx)` signature, `@mcp.tool()` decorator, `_get_visible_collections` usage, and `conn.close()` in `finally` block were consistent across every run regardless of condition.

**SPEC pointer (condition B) vs explicit instruction (condition C):** No observable difference in output quality or structure. Both conditions produced the same pattern as condition A (uncontrolled).

## Hypothesis Status

**NOT SUPPORTED**

The hypothesis that first file encountered determines output pattern cannot be validated because:

1. **Ceiling effect:** All conditions (A, B, C) achieved 9/9 PASS across all criteria. There is no variance to attribute to encounter order.
2. **Strong codebase signals:** The `CLAUDE.md` subsystem map, `tools/__init__.py` registration pattern, and the existing tool files (`tools/search.py`, `tools/convert.py`, etc.) provide redundant signals about the correct pattern. Any single file is sufficient.
3. **Observability gap:** The `-p` mode output does not reveal which files the agent read or in what order, so we cannot correlate encounter order with output even if there were variance.

The codebase conventions are strong enough that Sonnet discovers the correct pattern regardless of whether:
- No pointer exists (condition A)
- A SPEC.md pointer directs to a canonical example (condition B)
- An explicit instruction tells it to read a specific file first (condition C)

## Implementation Scope (not supported)

- Encounter order does not matter when codebase patterns are strong
- Agents discover patterns through exploration regardless of pointers
- The `CLAUDE.md` subsystem map and `tools/__init__.py` provide sufficient pattern information without any additional pointers
- SPEC.md "Canonical Example" fields are unnecessary overhead for well-structured codebases with clear conventions
