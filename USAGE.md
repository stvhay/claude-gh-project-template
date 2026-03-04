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

## Running in an Apple Container

Add the `dev-container` function to your shell profile to launch projects inside an isolated [Apple Container](https://github.com/apple/container).

### Prerequisites

- macOS 26 (Tahoe) or later
- Apple Silicon Mac
- [Apple Container](https://github.com/apple/container) installed

### The function

```bash
# Override the shared Nix store location, or leave unset for the default.
# export DEV_CONTAINER_NIX_CACHE="$HOME/.dev-containers/nix"

dev-container() {
  local nix_cache="${DEV_CONTAINER_NIX_CACHE:-$HOME/.dev-containers/nix}"

  if [[ $# -ne 1 ]]
  then
    echo "Usage: dev-container <project-directory>" >&2
    return 1
  fi

  local project_dir
  project_dir="$(cd "$1" 2>/dev/null && pwd)" || {
    echo "Error: directory '$1' does not exist" >&2
    return 1
  }

  mkdir -p "$nix_cache"

  container run \
    -v "$project_dir:/workspace" \
    -v "$nix_cache:/nix" \
    --ssh \
    nixos/nix \
    /bin/sh -c '
      # Install Claude Code if not already cached in shared Nix store
      command -v claude >/dev/null 2>&1 || nix-env -iA nixpkgs.nodejs && npm i -g @anthropic-ai/claude-code

      # Alias claude to bypass permissions (container is isolated)
      echo "alias claude=\"claude --dangerously-skip-permissions\"" >> ~/.profile

      cd /workspace
      echo "Dev container ready. Run: claude"
      exec /bin/sh -l
    '
}
```

Then: `dev-container ~/Projects/my-app`

### What each step does

- **Argument validation** — Requires exactly one argument (a directory path) and verifies the directory exists.
- `mkdir -p "$nix_cache"` — Ensure the shared Nix store directory exists on the host.
- `-v "$project_dir:/workspace"` — Bind-mount the project directory into the container. Edits are visible on both sides.
- `-v "$nix_cache:/nix"` — Bind-mount a shared Nix store. Persisted across containers so packages are downloaded once.
- `--ssh` — Forward the host SSH agent so git clone/push works inside the container.
- `nixos/nix` — Stock OCI image with Nix pre-installed (Alpine-based).
- **Claude Code install** — Installs Node.js via Nix and Claude Code via npm on first run. Skipped on subsequent runs (cached in shared Nix store).
- **claude alias** — Aliases `claude` to `claude --dangerously-skip-permissions` since the container is an isolated environment.

### Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `DEV_CONTAINER_NIX_CACHE` | `$HOME/.dev-containers/nix` | Override the shared Nix store location on the host |

### Installation

Add the function to your shell profile — `~/.bashrc`, `~/.zshrc`, or a file sourced by your shell (e.g., `~/.local/etc/profile.d/`).
