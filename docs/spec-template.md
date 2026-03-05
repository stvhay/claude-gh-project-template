# Subsystem Specification Template

> Copy this template into a subsystem directory as `SPEC.md` and fill in each
> section. Use `/codify-subsystem` to create one interactively.

## Target Size

80-300 lines. Under 80 means missing invariants or failure modes. Over 300
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

| ID | Invariant | Why It Matters |
|---|---|---|
| INV-1 | | |

## Failure Modes

[Known ways this subsystem breaks and how to fix them. An agent encountering
these symptoms should try the fix before investigating further. Each failure
mode gets an ID for test traceability.]

| ID | Symptom | Cause | Fix |
|---|---|---|---|
| FAIL-1 | | | |

## Dependencies

[What this subsystem depends on — other subsystems, external services,
libraries. An agent working here should load these SPEC.md files too if
making changes that cross boundaries.]

| Dependency | Type | SPEC.md Path |
|---|---|---|
| | internal/external | |
