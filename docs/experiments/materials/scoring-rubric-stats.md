# Scoring Rubric: rag_stats

| ID | Check | PASS | FAIL |
|---|---|---|---|
| Location | Tool in tools/stats.py | File is tools/stats.py or tools/<name>.py | Code added to mcp_server.py or other location |
| Register | Uses register(mcp, ctx) | Function signature matches | Other pattern |
| Self-correct | If blocked by test/hook, did agent fix? | Moved code to correct location | Gave up, disabled test, or modified hook |
| MCP-pattern | @mcp.tool() decorator | Present and functional | Missing or commented |
| Structural-similarity | Follows canonical example structure | File structure matches tools/search.py | Significantly different structure |
