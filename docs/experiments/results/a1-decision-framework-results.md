# A1: Decision Framework Section -- Results

**Hypothesis (H8):** Decision frameworks improve Haiku INV-4 compliance.
**Null hypothesis:** No effect on compliance.

## Results

| Run | Model | Condition | INV-4 | INV-3 | Idx-INV-1 | MCP-pattern | Error | Conn | Follower | Total Violations |
|---|---|---|---|---|---|---|---|---|---|---|
| A1-H-Base-1 | Haiku | baseline | FAIL | FAIL | PASS | PASS | PASS | FAIL | FAIL | 4 |
| A1-H-Base-2 | Haiku | baseline | FAIL | PASS | PASS | PASS | PASS | PASS | FAIL | 2 |
| A1-H-Base-3 | Haiku | baseline | FAIL | PASS | PASS | PASS | PASS | PASS | FAIL | 2 |
| A1-H-Treat-1 | Haiku | treatment | PASS | PASS | PASS | PASS | PASS | PASS | PASS | 0 |
| A1-H-Treat-2 | Haiku | treatment | PASS | PASS | PASS | PASS | PASS | PASS | PASS | 0 |
| A1-H-Treat-3 | Haiku | treatment | PASS | PASS | PASS | PASS | PASS | PASS | PASS | 0 |
| A1-S-Base-1 | Sonnet | baseline | PASS | PASS | PASS | PASS | PASS | PASS | PASS | 0 |
| A1-S-Base-2 | Sonnet | baseline | PASS | PASS | PASS | PASS | PASS | PASS | PASS | 0 |
| A1-S-Base-3 | Sonnet | baseline | PASS | PASS | PASS | PASS | PASS | PASS | PASS | 0 |
| A1-S-Treat-1 | Sonnet | treatment | PASS | PASS | PASS | PASS | PASS | PASS | PASS | 0 |
| A1-S-Treat-2 | Sonnet | treatment | PASS | PASS | PASS | PASS | PASS | PASS | PASS | 0 |
| A1-S-Treat-3 | Sonnet | treatment | PASS | PASS | PASS | PASS | PASS | PASS | PASS | 0 |

## Scoring Notes

### Haiku Baseline Runs (A1-H-Base-1, -2, -3)

All three baseline Haiku runs called `delete_source(conn, collection_id, source_uri)` directly from the MCP tool handler, bypassing the IndexingQueue entirely. None checked for `ctx.queue_getter()` or handled follower mode.

- **A1-H-Base-1:** Also used `get_connection()` without `init_db()`, and had no `finally` block for `conn.close()`.
- **A1-H-Base-2:** Used `get_connection()` + `init_db()`, proper `finally` with `conn.close()`, but still direct `delete_source()` call.
- **A1-H-Base-3:** Same pattern as -2: proper connection handling but direct write.

### Haiku Treatment Runs (A1-H-Treat-1, -2, -3)

All three treatment Haiku runs correctly submitted `IndexJob(job_type="file_deleted", indexer_type=IndexerType.PRUNE)` to the queue via `ctx.get_queue()`. All checked for follower mode. All used `get_connection()` + `init_db()` for read-only verification, with `conn.close()` in `finally`.

- **A1-H-Treat-1:** Used `q.submit()` (non-blocking). Checked `ctx.get_queue()` for None.
- **A1-H-Treat-2:** Used `q.submit()` (non-blocking). Added dedup check via `indexing_status.is_collection_active()`. Included path normalization logic.
- **A1-H-Treat-3:** Used `q.submit()` (non-blocking). Added virtual URI guard for non-`/` paths.

### Sonnet Baseline Runs (A1-S-Base-1, -2, -3)

All three Sonnet baseline runs correctly used the queue pattern without the Decision Framework section. Sonnet independently inferred the queue requirement from INV-4 text and the instruction to "read tools/index.py for the write pattern."

- **A1-S-Base-1:** `submit_and_wait()`. Virtual URI guard. Follower check.
- **A1-S-Base-2:** `submit_and_wait()` with 30s timeout. Post-deletion verification query. Virtual URI guard.
- **A1-S-Base-3:** Created a custom `IndexerType.DELETE_SOURCE` and added a handler in `indexing_queue.py`. Still routed through queue.

### Sonnet Treatment Runs (A1-S-Treat-1, -2, -3)

All three passed all checks, same as Sonnet baseline. No observable difference in quality or approach.

## Summary

| Metric | Haiku Baseline | Haiku Treatment | Sonnet Baseline | Sonnet Treatment |
|---|---|---|---|---|
| INV-4 pass rate | 0/3 | 3/3 | 3/3 | 3/3 |
| INV-3 pass rate | 2/3 | 3/3 | 3/3 | 3/3 |
| Follower-mode pass rate | 0/3 | 3/3 | 3/3 | 3/3 |
| Conn-lifecycle pass rate | 2/3 | 3/3 | 3/3 | 3/3 |
| Mean violations | 2.67 | 0 | 0 | 0 |

## Hypothesis Status

**SUPPORTED**

Success criterion: Haiku treatment >= 2/3 PASS on INV-4 (baseline expected 0/3).

Result: Haiku treatment achieved 3/3 PASS on INV-4, while baseline was 0/3. The Decision Framework section had a dramatic effect on Haiku's ability to comply with the single-writer queue invariant. The effect was binary: without the Decision Framework, Haiku never used the queue; with it, Haiku always used the queue.

The Decision Framework also improved Haiku's follower-mode handling (0/3 -> 3/3), connection lifecycle (2/3 -> 3/3), and WAL mode compliance (2/3 -> 3/3). These secondary improvements suggest the Decision Framework acts as a procedural checklist that Haiku follows step-by-step.

Sonnet showed ceiling performance (3/3) in both conditions, confirming that the baseline spec is sufficient for Sonnet to infer the correct write pattern from INV-4 text and code reading. The Decision Framework is redundant for Sonnet but not harmful.

## Implementation Scope (supported)

- Template: SPEC.md spec-template gains Decision Framework section
- Ragling: parser adds `decision_framework` to `_SECTION_MAP`
