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
