# Project Onboarding

> **This file contains one-time setup instructions.** After onboarding completes, this file will be replaced with your project's configuration. Do not edit it manually — just start a conversation with Claude Code and follow the prompts.

## Instructions for Claude Code

You are reading onboarding instructions for an uninitialized project template. Execute the following procedure exactly. If user resists onboarding they may be updating the template itself, in which case if there is any doubt their intent, confirm with them and repond appropriately.

### Step 1: Greet the user

Tell the user: "This project hasn't been initialized yet. I'll ask a few questions to set it up."

### Step 2: Collect project information

Ask the following questions **one at a time**. Wait for each answer before asking the next.

1. "What is the project name?"
2. "Describe the project's purpose in 1-2 sentences."
3. "Want me to set up for a specific language or framework? (e.g., Python, Node.js, Go, Rust) Or say 'skip' to stay language-agnostic."

### Step 3: Initialize the project

After collecting all answers, perform all of the following without further prompting:

#### 3a. Rewrite this file (CLAUDE.md)

Replace the entire contents of `CLAUDE.md` with the template below. Substitute `{PROJECT_NAME}` and `{PURPOSE}` with the user's answers. Copy everything else verbatim.

```
# {PROJECT_NAME}

## Purpose

{PURPOSE}

## First-Run Setup

On first use in a fresh clone, follow `docs/FIRST_RUN.md` to initialize project memory files.

## Environment

- **Dependencies**: Managed via `flake.nix`. Add packages to `buildInputs`.
- **Initialization**: `.envrc` sources `use flake` and runs scripts from `.envrc.d/` and `.envrc.local.d/`.
- If you add a dependency to `flake.nix`, ask the user to restart the session so `direnv` reloads.

## Architecture

> **Organizing principle:** Code is organized so any subsystem fits in a single
> agent context window. Self-contained units over shared abstractions.

### Directory Structure

**Default: Vertical slices (feature-based)**

Each feature or subsystem gets its own directory containing all its components:
handler, validation, data access, types, tests. An agent should be able to
understand a feature by reading one directory.

    features/
      feature-name/
        SPEC.md          # Subsystem specification (see below)
        handler.ext      # Entry point
        types.ext        # Feature-specific types
        store.ext        # Data access
        tests/
          test_handler.ext

**When vertical slices don't fit:**
- **Libraries/packages:** Organize by module. Each module gets a SPEC.md.
- **CLI tools:** Organize by command. Each command is a slice.
- **Data pipelines:** Organize by stage. Each stage is a slice.
- **The principle stays the same:** one directory = one context load for an agent.

### Subsystem Specifications (SPEC.md)

Every non-trivial directory gets a `SPEC.md` — a machine-readable specification
scoped to that subsystem. Agents load the nearest SPEC.md when working on files.

**When to create one:** When a directory has 3+ files or contains invariants an
agent could violate without knowing. Use `/codify-subsystem` to create one.

**Format:** See `docs/spec-template.md`.

**Routing:** Agents walk up the directory tree from the file being modified and
load the nearest SPEC.md. This mirrors how .gitignore resolution works.

### Subsystem Map

| Subsystem | Path | Purpose |
|---|---|---|
| *(populated as project grows — use `/codify-subsystem`)* | | |

For detailed specifications, read the SPEC.md in each subsystem directory.

### Context Budgeting

- Each subsystem should be understandable from its SPEC.md + source files
  loaded together in ~50% of a context window.
- If a subsystem exceeds this, split it into sub-features.
- Prefer duplication over deep cross-subsystem coupling — an agent working on
  Feature A should rarely need to load Feature B's code.

### Testing Convention

Tests are anchored to SPEC.md items. Each invariant (INV-N) gets a positive
test verifying the invariant holds. Each failure mode (FAIL-N) gets a negative
test verifying graceful handling. Test names include the spec item ID for
traceability (e.g., test_inv1_total_equals_sum, test_fail2_rejects_expired).

This helps agents write tests that verify *requirements*, not *implementations*.
See docs/spec-template.md for the coverage table format.

## Workflow

<!-- Describe the steps Claude Code should follow when working on this project. -->

## Writing Standards

- Structured with headers, bullet points, and blockquotes for key statements.
- No filler or padding. Dense, scannable, useful.

## Lessons Learned

<!-- Add project-specific lessons as they arise. -->

## Contributing

All changes follow the workflow in [CONTRIBUTING.md](CONTRIBUTING.md). File a GitHub issue, use the bundled skills to brainstorm, plan, execute, verify, and review, then open a PR with the plan and issue reference.
```

#### 3b. Create MEMORY.md

Create `MEMORY.md` in the project root with this content:

```
# Project Memory

Specific facts, edge cases, and session-specific context that doesn't belong
in CLAUDE.md (which covers general workflow and standards).
```

#### 3c. Configure auto-memory redirect

Find the auto-memory directory for this project under `~/.claude/projects/`. Look for the directory whose path matches this project's absolute path. Write the following to `~/.claude/projects/<match>/memory/MEMORY.md`, substituting the absolute path to this project's root:

```
# Auto Memory Redirect

Do not store project memory here. All project memory belongs in the project root:

    {ABSOLUTE_PATH_TO_PROJECT}/MEMORY.md

Use that file for specific facts, edge cases, and session context.
General workflow and standards go in CLAUDE.md.
```

#### 3d. Rewrite README.md

Replace the entire contents of `README.md` with the template below. Substitute `{PROJECT_NAME}` and `{PURPOSE}` with the user's answers. For `{PROJECT_NAME_SLUG}`, use a lowercase, hyphenated version of the project name (e.g., "My Cool App" becomes "my-cool-app").

```
# {PROJECT_NAME}

{PURPOSE}

## Setup

### Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
- [direnv](https://direnv.net/)
- [Nix](https://nixos.org/download/) with flakes enabled

### Getting started

\```bash
git clone <repo-url>
cd {PROJECT_NAME_SLUG}
direnv allow
claude
\```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
```

#### 3e. Create scaffolding directories

- Create `docs/plans/.gitkeep` (the directory is gitignored but needs to exist for plans to land).
- Create `src/.gitkeep` as the default source directory.

#### 3f. Language/framework setup (if not skipped)

If the user chose a language or framework in Step 2, apply the following. Use judgment for languages not listed — follow the same pattern.

**Append to `.gitignore`** — Add a section with language-specific patterns:

| Language | Patterns to add |
|---|---|
| Python | `__pycache__/`, `*.pyc`, `*.pyo`, `.venv/`, `*.egg-info/`, `dist/`, `build/` |
| Node.js | `node_modules/`, `dist/`, `.env`, `.env.local` |
| Go | `bin/`, `*.exe` |
| Rust | `target/` |
| TypeScript | `node_modules/`, `dist/`, `.env`, `.env.local`, `*.tsbuildinfo` |

Format the new section as:

```
# {Language}
{patterns, one per line}
```

**Update `flake.nix`** — Add appropriate packages to `buildInputs`:

| Language | Packages |
|---|---|
| Python | `python3`, `ruff` |
| Node.js | `nodejs` |
| Go | `go`, `gopls` |
| Rust | `rustc`, `cargo`, `rust-analyzer` |
| TypeScript | `nodejs`, `nodePackages.typescript` |

**Adjust source directory** — If the language has a different convention (e.g., Go uses `cmd/` and `internal/`), rename or restructure accordingly. Otherwise `src/` is fine.

### Step 4: Confirm completion

Tell the user what was done. List each action taken (files rewritten, created, modified). Then suggest: "Describe your development workflow so I can fill in the Workflow section of CLAUDE.md."
