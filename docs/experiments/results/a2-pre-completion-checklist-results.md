# A2: Pre-Completion Checklist -- Results

**Hypothesis (H9):** Checklists reduce pattern violations across models.
**Null hypothesis:** No effect on pattern violations.

## Results

| Run | Model | Condition | INV-4 | INV-3 | Idx-INV-1 | MCP-pattern | Error | Conn | Follower | Total Violations |
|---|---|---|---|---|---|---|---|---|---|---|
| A1-H-Base-1 | Haiku | baseline | FAIL | FAIL | PASS | PASS | PASS | FAIL | FAIL | 4 |
| A1-H-Base-2 | Haiku | baseline | FAIL | PASS | PASS | PASS | PASS | PASS | FAIL | 2 |
| A1-H-Base-3 | Haiku | baseline | FAIL | PASS | PASS | PASS | PASS | PASS | FAIL | 2 |
| A2-H-Treat-1 | Haiku | treatment | FAIL | PASS | PASS | PASS | PASS | PASS | FAIL | 2 |
| A2-H-Treat-2 | Haiku | treatment | FAIL | PASS | PASS | PASS | PASS | PASS | FAIL | 2 |
| A2-H-Treat-3 | Haiku | treatment | PASS | PASS | PASS | PASS | PASS | PASS | PASS | 0 |
| A1-S-Base-1 | Sonnet | baseline | PASS | PASS | PASS | PASS | PASS | PASS | PASS | 0 |
| A1-S-Base-2 | Sonnet | baseline | PASS | PASS | PASS | PASS | PASS | PASS | PASS | 0 |
| A1-S-Base-3 | Sonnet | baseline | PASS | PASS | PASS | PASS | PASS | PASS | PASS | 0 |
| A2-S-Treat-1 | Sonnet | treatment | PASS | PASS | PASS | PASS | FAIL | PASS | PASS | 1 |
| A2-S-Treat-2 | Sonnet | treatment | PASS | PASS | PASS | PASS | FAIL | PASS | PASS | 1 |
| A2-S-Treat-3 | Sonnet | treatment | PASS | PASS | PASS | PASS | FAIL | PASS | PASS | 1 |

## Pattern Violation Analysis

Focus on: MCP-pattern, Error-handling, Conn-lifecycle

| Metric | Haiku Baseline | Haiku Treatment | Sonnet Baseline | Sonnet Treatment |
|---|---|---|---|---|
| MCP-pattern pass rate | 3/3 | 3/3 | 3/3 | 3/3 |
| Error-handling pass rate | 3/3 | 3/3 | 3/3 | 0/3 |
| Conn-lifecycle pass rate | 2/3 | 3/3 | 3/3 | 3/3 |
| Mean pattern violations | 0.33 | 0.00 | 0.00 | 1.00 |

### Full Invariant Analysis (all 7 checks)

| Metric | Haiku Baseline | Haiku Treatment | Sonnet Baseline | Sonnet Treatment |
|---|---|---|---|---|
| Mean total violations | 2.67 | 1.33 | 0.00 | 1.00 |
| INV-4 pass rate | 0/3 | 1/3 | 3/3 | 3/3 |
| Follower pass rate | 0/3 | 1/3 | 3/3 | 3/3 |

## Scoring Notes

### A2-H-Treat-1 and A2-H-Treat-2 (Haiku)
Both called `delete_source()` directly from the tool handler rather than submitting an IndexJob to the queue. Neither checked for follower mode. Pattern violations (MCP-pattern, Error, Conn) were all clean: try/except present, conn.close() in finally, decorator correct.

### A2-H-Treat-3 (Haiku)
The one Haiku run that fully followed the write pattern: submitted an IndexJob with `IndexerType.PRUNE` to the queue, checked follower mode, and had all pattern violations clean. Closely mirrors the `rag_index` tool structure with a separate `_rag_delete_source_via_queue()` helper.

### A2-S-Treat-1, A2-S-Treat-2, A2-S-Treat-3 (Sonnet)
All three Sonnet treatment runs correctly routed writes through the IndexingQueue with PRUNE jobs and checked follower mode. However, none wrapped their main logic in a try/except -- exceptions from `get_connection()`, SQL queries, or `submit_and_wait()` would propagate unhandled to the MCP framework rather than returning `{"error": ...}`. This is a regression from the baseline where all 3 Sonnet runs had proper error handling.

The checklist appears to have focused Sonnet's attention on the queue routing pattern (which it already followed) at the expense of error handling discipline. All three Sonnet runs used `submit_and_wait()` (blocking) rather than `submit()` (fire-and-forget), suggesting the checklist's "Write operations route through IndexingQueue" item encouraged a more thorough approach that inadvertently displaced the error-handling pattern.

## Hypothesis Status

**NOT SUPPORTED**

Success criterion: >= 50% reduction in combined pattern violations (MCP-pattern + Error-handling + Conn-lifecycle).

### Pattern Violations (MCP-pattern, Error, Conn only)

- **Haiku baseline:** 1 violation total (1 Conn fail across 3 runs) = 0.33 mean
- **Haiku treatment:** 0 violations total = 0.00 mean
- **Sonnet baseline:** 0 violations total = 0.00 mean
- **Sonnet treatment:** 3 violations total (3 Error fails) = 1.00 mean

The checklist improved Haiku's Conn-lifecycle compliance (2/3 -> 3/3) but introduced Error-handling regressions in Sonnet (3/3 -> 0/3). Combined pattern violations went from 1 (baseline total) to 3 (treatment total) -- an increase, not a decrease.

### Overall Violations (all 7 checks)

- **Haiku:** 8 baseline -> 4 treatment (50% reduction)
- **Sonnet:** 0 baseline -> 3 treatment (regression)
- **Combined:** 8 baseline -> 7 treatment (12.5% reduction, below 50% threshold)

The checklist helped Haiku with INV-4/follower compliance in 1 of 3 runs, but caused a consistent Sonnet regression on error handling. The net effect is neutral to slightly negative.

### Interpretation

The checklist may create a "displacement effect" where models focus on explicitly listed items (queue routing, follower mode) at the expense of patterns they previously handled implicitly (error handling). Sonnet's baseline already had 0 violations; the checklist added cognitive load without benefit and actively displaced a previously reliable pattern.

## Implementation Scope

Not applicable -- hypothesis not supported. The pre-completion checklist does not reliably reduce pattern violations and may introduce regressions in models that already comply.
