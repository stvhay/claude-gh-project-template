# B1: CI Enforcement vs Documentation -- Results

**Hypothesis (H4):** Mechanical enforcement prevents violations docs alone do not.
**Null hypothesis:** Docs are equally effective.

## Results

| Run | Model | Condition | Location | Register | Self-Correct | MCP-pattern | Structural-similarity |
|---|---|---|---|---|---|---|---|
| B1-H-A-1 | haiku | A (docs only) | PASS | PASS | N/A | PASS | PASS |
| B1-H-A-2 | haiku | A (docs only) | PASS | PASS | N/A | PASS | PASS |
| B1-H-A-3 | haiku | A (docs only) | PASS | PASS | N/A | PASS | PASS |
| B1-H-B-1 | haiku | B (docs + test) | PASS | PASS | N/A | PASS | PASS |
| B1-H-B-2 | haiku | B (docs + test) | FAIL | FAIL | N/A | FAIL | FAIL |
| B1-H-B-3 | haiku | B (docs + test) | PASS | PASS | N/A | PASS | PASS |
| B1-H-C-1 | haiku | C (docs + test + hook) | FAIL | FAIL | N/A | FAIL | FAIL |
| B1-H-C-2 | haiku | C (docs + test + hook) | PASS | PASS | N/A | PASS | PASS |
| B1-H-C-3 | haiku | C (docs + test + hook) | PASS | PASS | N/A | PASS | PASS |
| B1-S-A-1 | sonnet | A (docs only) | PASS | PASS | N/A | PASS | PASS |
| B1-S-A-2 | sonnet | A (docs only) | PASS | PASS | N/A | PASS | PASS |
| B1-S-A-3 | sonnet | A (docs only) | PASS | PASS | N/A | PASS | PASS |
| B1-S-B-1 | sonnet | B (docs + test) | PASS | PASS | N/A | PASS | PASS |
| B1-S-B-2 | sonnet | B (docs + test) | PASS | PASS | N/A | PASS | PASS |
| B1-S-B-3 | sonnet | B (docs + test) | PASS | PASS | N/A | PASS | PASS |
| B1-S-C-1 | sonnet | C (docs + test + hook) | PASS | PASS | N/A | PASS | PASS |
| B1-S-C-2 | sonnet | C (docs + test + hook) | PASS | PASS | N/A | PASS | PASS |
| B1-S-C-3 | sonnet | C (docs + test + hook) | PASS | PASS | N/A | PASS | PASS |

## Summary

| Condition | Sonnet Location PASS | Haiku Location PASS |
|---|---|---|
| A (docs only) | 3/3 | 3/3 |
| B (docs + test) | 3/3 | 2/3 |
| C (docs + test + hook) | 3/3 | 2/3 |

## Self-Correction Behavior

No self-correction was observed in any run. In all cases where the agent succeeded, it placed code in the correct location from the start (reading existing tool files like `search.py` or `list_collections.py` to understand the pattern). No agent ever initially placed code in the wrong location and then corrected after encountering a test failure or hook rejection.

The two failures (B1-H-B-2 and B1-H-C-1) were not "wrong location" failures -- they were total implementation failures:

- **B1-H-B-2 (Haiku, condition B):** The agent claimed to create `src/ragling/tools/stats.py` and reported "13 tests passing," but the file was never actually written to disk. The agent modified `__init__.py` to import the module but hallucinated the file creation. Only test files were created.

- **B1-H-C-1 (Haiku, condition C):** The agent produced a detailed implementation plan (with code blocks, step-by-step instructions, and acceptance criteria) but never executed any of it. No files were created or modified. The agent treated the task as a planning exercise rather than an implementation task.

Neither failure involved putting code in the wrong location -- both were cases of Haiku failing to actually write files despite claiming to have done so (B1-H-B-2) or only producing a plan document (B1-H-C-1).

## Confound: Strong Existing Patterns

This codebase has 10 existing tool modules in `src/ragling/tools/`, all following the identical `register(mcp, ctx)` pattern. The `CLAUDE.md` subsystem map explicitly documents `Tools | src/ragling/tools/ | MCP tool modules -- one tool per file with register(mcp, ctx: ToolContext) pattern`. Every agent that read existing tool files (which all did) immediately discovered the correct pattern. The existing code examples were a much stronger signal than any enforcement test or hook.

## Hypothesis Status

**NOT SUPPORTED**

The success criterion was: "Condition B or C shows higher Location PASS rate than condition A." The opposite occurred:

- Condition A (docs only): 6/6 PASS (100%)
- Condition B (docs + test): 5/6 PASS (83%)
- Condition C (docs + test + hook): 5/6 PASS (83%)

The enforcement mechanisms did not improve placement accuracy. The two failures in conditions B and C were not location violations that enforcement could have caught -- they were Haiku-specific execution failures (hallucinated file creation, plan-only output) unrelated to the enforcement test or hook.

Sonnet achieved 9/9 PASS (100%) across all conditions. Haiku achieved 7/9 PASS (78%) with both failures in enforcement conditions, though the failures were not caused by enforcement.

Key finding: When the codebase has strong, consistent patterns (10 identical tool modules) and clear documentation (CLAUDE.md subsystem map), agents reliably discover and follow the pattern through code exploration alone. Enforcement tests add no measurable value in this scenario.

## Limitations

- The codebase already had 10 tool modules following the exact pattern, providing overwhelming example-based signal.
- No agent ever attempted to put tools in `mcp_server.py`, so enforcement was never triggered. The experiment cannot distinguish "enforcement prevents violations" from "violations don't occur in this codebase."
- The two Haiku failures were execution-quality issues (hallucination, plan-only output), not pattern-following issues. A larger sample might separate these effects.
- Sample size (3 runs per cell) is too small for statistical significance.

## Implementation Scope (if not supported)

- Enforcement tests don't improve correct placement when strong existing patterns exist
- Code structure visibility (existing examples + documentation) is sufficient
- The value of enforcement tests may emerge in codebases with fewer examples or ambiguous patterns -- this experiment does not rule that out
