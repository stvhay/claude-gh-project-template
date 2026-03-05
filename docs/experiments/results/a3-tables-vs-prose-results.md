# A3: Tables vs Prose for Invariants -- Results

**Hypothesis (H10):** Table format produces higher invariant compliance than prose.
**Null hypothesis:** Format has no effect.

## Results

| Run | Condition | INV-4 | INV-3 | Idx-INV-1 | MCP-pattern | Error | Conn | Follower | Total Violations |
|---|---|---|---|---|---|---|---|---|---|
| A1-S-Base-1 | Table | PASS | PASS | PASS | PASS | PASS | PASS | PASS | 0 |
| A1-S-Base-2 | Table | PASS | PASS | PASS | PASS | PASS | PASS | PASS | 0 |
| A1-S-Base-3 | Table | PASS | PASS | PASS | PASS | PASS | PASS | PASS | 0 |
| A3-S-Prose-1 | Prose | PASS | PASS | PASS | PASS | PASS | PASS | PASS | 0 |
| A3-S-Prose-2 | Prose | PASS | PASS | PASS | PASS | PASS | PASS | PASS | 0 |
| A3-S-Prose-3 | Prose | PASS | PASS | PASS | PASS | PASS | PASS | PASS | 0 |

## Summary

| Metric | Table (Sonnet) | Prose (Sonnet) |
|---|---|---|
| INV-4 pass rate | 3/3 | 3/3 |
| Mean violations | 0 | 0 |

## Run Details

### A3-S-Prose-1
- Submitted IndexJob with `IndexerType.PRUNE` via `submit_and_wait` (INV-4 PASS)
- Used `get_connection()` + `init_db()` for read check (INV-3 PASS)
- Delegated deletion to queue worker which calls `delete_source()` in base.py (Idx-INV-1 PASS)
- `register(mcp, ctx)` with `@mcp.tool()` decorator (MCP-pattern PASS)
- Try/except with descriptive `{"error": ...}` returns (Error PASS)
- `conn.close()` in `finally` block (Conn PASS)
- Checks `ctx.get_queue()` then `ctx.queue_getter is not None`, returns error (Follower PASS)

### A3-S-Prose-2
- Submitted IndexJob with `IndexerType.PRUNE` via `submit_and_wait` (INV-4 PASS)
- Used `get_connection()` + `init_db()` for read check (INV-3 PASS)
- Delegated deletion to queue worker (Idx-INV-1 PASS)
- `register(mcp, ctx)` with `@mcp.tool()` decorator (MCP-pattern PASS)
- Try/except with descriptive `{"error": ...}` returns (Error PASS)
- `conn.close()` in `finally` block (Conn PASS)
- Checks queue, checks queue_getter, returns error (Follower PASS)
- Added virtual URI rejection (`calibre://`, `git://` prefixes)

### A3-S-Prose-3
- Submitted IndexJob with `IndexerType.PRUNE` via `submit_and_wait` (INV-4 PASS)
- Used `get_connection()` + `init_db()` for read check (INV-3 PASS)
- Delegated deletion to queue worker (Idx-INV-1 PASS)
- `register(mcp, ctx)` with `@mcp.tool()` decorator (MCP-pattern PASS)
- Try/except with descriptive `{"error": ...}` returns (Error PASS)
- `conn.close()` in `finally` block (Conn PASS)
- Checks queue, checks queue_getter, returns error (Follower PASS)
- Added virtual URI rejection (`calibre://`, `git://`, `email://`, `rss://` prefixes)
- Extracted deletion logic into `_delete_via_queue()` helper

## Hypothesis Status

**NOT SUPPORTED**

Prose condition showed 0 INV-4 failures and 0 total violations, matching the table condition exactly (0/0). The prose paragraph formulation of Core invariants produced identical compliance to the table formulation across all 7 scored dimensions and all 3 runs.

## Implementation Scope

- Tables are convention (readability/RAG retrieval), not a performance requirement for invariant compliance
- Both formats conveyed the single-writer invariant (INV-4) and WAL mode requirement (INV-3) equally well
- The prose version was a single dense paragraph; Sonnet extracted the relevant constraints correctly in all cases
- Format choice for invariants can be driven by readability and RAG chunking considerations rather than compliance concerns
