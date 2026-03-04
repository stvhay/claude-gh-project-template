# Usage

## Quick Start: New Project

Add the `dev-init` function to your shell profile to bootstrap new projects from this template in one command.

### The function

```bash
# Set this to your fork URL, or leave unset for the default.
# export DEV_TEMPLATE_REPO="https://github.com/youruser/your-fork.git"

dev-init() {
  local repo="${DEV_TEMPLATE_REPO:-https://github.com/stvhay/claude-gh-project-template.git}"

  if [[ $# -ne 1 ]]
  then
    echo "Usage: dev-init <new-directory>" >&2
    return 1
  fi

  if [[ -d "$1" ]]
  then
    echo "Error: directory '$1' already exists" >&2
    return 1
  fi

  mkdir -p "$1" || return 1
  cd "$1" || return 1
  git clone "$repo" . || { cd - >/dev/null; return 1; }
  git remote remove origin || return 1
  direnv allow || return 1
  eval "$(direnv export "${SHELL##*/}")" || return 1
  claude "Initialize this project." || return 1
}
```

Then: `dev-init my-new-project`

### What each step does

- **Argument validation** — Requires exactly one argument (the directory name) and refuses to overwrite an existing directory.
- `mkdir -p "$1" && cd "$1"` — Create and enter the project directory.
- `git clone "$repo" .` — Clone the template (from `DEV_TEMPLATE_REPO` or the default) into the current directory.
- `git remote remove origin` — Detach from the template repo so you can add your own remote later.
- `direnv allow` — Activate the Nix dev shell (or Homebrew dependency checks).
- `eval "$(direnv export ...)"` — Load the environment into the current shell session.
- `claude "Initialize this project."` — Launch Claude Code to run the onboarding flow.

### Installation

Add the function to your shell profile — `~/.bashrc`, `~/.zshrc`, or a file sourced by your shell (e.g., `~/.local/etc/profile.d/`).

## What Happens After Initialization

Claude Code reads `CLAUDE.md` and walks you through three questions:

1. **Project name** — used in generated files
2. **Project purpose** — a 1-2 sentence description
3. **Language/framework** — e.g., Python, Node.js, Go, Rust (or skip to stay language-agnostic)

It then:
- Rewrites `CLAUDE.md` with your project configuration
- Creates `MEMORY.md` for session-specific context
- Updates `README.md` with your project details
- Sets up scaffolding directories (`src/`, `docs/plans/`)
- Adds language-specific `.gitignore` patterns and `flake.nix` dependencies (if applicable)

After that, you're ready to start building. Run `claude` to begin.
