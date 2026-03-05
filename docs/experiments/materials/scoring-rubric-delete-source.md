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
