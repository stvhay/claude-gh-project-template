# Subsystem Specification Template

> Copy this template into a subsystem directory as `SPEC.md` and fill in each
> section. Use `/codify-subsystem` to create one interactively.

## Target Size

80-350 lines. Under 80 means missing invariants or failure modes. Over 350
means the subsystem should be split.

---

# [Subsystem Name]

## Purpose

[One paragraph: what this subsystem does and why it exists. Include the
problem it solves and the key design decision that shaped it.]

## Core Mechanism

[2-3 sentences on the key design decisions that shaped this subsystem — *why*
it works this way, not *what* it does (the code already shows that). Include
the mental model an agent needs to modify this code correctly.]

**Key files:**
- `path/to/entry-point.py` — [role]
- `path/to/core-logic.py` — [role]

## Public Interface

[What other subsystems depend on. Exports, APIs, events, shared types.
An agent modifying this subsystem must not break these contracts.]

| Export | Used By | Contract |
|---|---|---|
| | | |

## Invariants

[Things that must ALWAYS be true. These are the correctness pillars — an agent
that violates any of these has introduced a bug. Each invariant gets an ID for
test traceability.]

| ID | Invariant | Enforcement | Why It Matters |
|---|---|---|---|
| INV-1 | | structural / reasoning-required | |

**Enforcement classification:**
- **structural** — enforced by type system, API design, or code structure; pattern-matchable and universally respected
- **reasoning-required** — needs architectural understanding; model-tier dependent

Prioritize converting reasoning-required invariants to structural via API design.

## Failure Modes

[Known ways this subsystem breaks and how to fix them. An agent encountering
these symptoms should try the fix before investigating further. Each failure
mode gets an ID for test traceability.]

| ID | Symptom | Cause | Fix |
|---|---|---|---|
| FAIL-1 | | | |

## Decision Framework

[Situation-keyed recipes for reasoning-required invariants. Converts declarative
rules into procedural guidance for agents that can follow patterns but cannot
infer architectural constraints. One entry per reasoning-required invariant.]

| Situation | Action | Invariant |
|---|---|---|
| | | INV-N |

## Testing

**Traceability:** Test names encode the spec item ID (`test_invN_description`,
`test_failN_description`). Items verified by other means should be noted here
(e.g., "INV-1, INV-5: enforced by `tsc --noEmit`", "FAIL-2: operational —
not unit-testable"). See CLAUDE.md Testing Convention.

## Dependencies

[What this subsystem depends on — other subsystems, external services,
libraries. An agent working here should load these SPEC.md files too if
making changes that cross boundaries.]

| Dependency | Type | SPEC.md Path |
|---|---|---|
| | internal/external | |
