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
# export DEV_CONTAINER_CLAUDE_CONFIG="$HOME/.dev-containers/claude"

dev-container() {
  local nix_cache="${DEV_CONTAINER_NIX_CACHE:-$HOME/.dev-containers/nix}"
  local claude_config="${DEV_CONTAINER_CLAUDE_CONFIG:-$HOME/.dev-containers/claude}"

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

  local container_name="dev-${project_dir##*/}"

  mkdir -p "$nix_cache" "$claude_config" || return 1

  container run \
    --name "$container_name" \
    -v "$project_dir:/workspace" \
    -v "$nix_cache:/nix" \
    -v "$claude_config:/root/.claude" \
    --ssh \
    nixos/nix \
    /bin/sh -c '
      # Install Claude Code if not already cached in shared Nix store
      [ -x /nix/.npm-global/bin/claude ] || {
        nix-env -iA nixpkgs.nodejs && npm i -g --prefix /nix/.npm-global @anthropic-ai/claude-code || {
          echo "Error: Claude Code installation failed" >&2
          exit 1
        }
      }
      export PATH="/nix/.npm-global/bin:$PATH"

      cd /workspace
      CONTAINER_IP=$(hostname -i 2>/dev/null | awk "{print \$1}")

      # Write PATH and claude alias to ~/.profile for the login shell
      grep -q "# dev-container" ~/.profile 2>/dev/null || cat >> ~/.profile <<PROFILE
# dev-container
export PATH="/nix/.npm-global/bin:\$PATH"
alias claude="claude --dangerously-skip-permissions --append-system-prompt \"You are running inside an Apple Container. The container IP is $CONTAINER_IP. When launching or displaying URLs for dev servers, use http://$CONTAINER_IP:<port> instead of localhost.\""
PROFILE
      echo "Dev container ready at ${CONTAINER_IP:-<unknown IP>}"
      echo "Services are accessible from the host at http://$CONTAINER_IP:<port>"
      echo "Run: claude"
      exec /bin/sh -l
    '
}
```

Then: `dev-container ~/Projects/my-app`

### What each step does

- **Argument validation** — Requires exactly one argument (a directory path) and verifies the directory exists.
- `--name "dev-${project_dir##*/}"` — Name the container `dev-<basename>` (e.g., `dev-my-app`) so it's identifiable in `container ls`.
- `mkdir -p "$nix_cache" "$claude_config"` — Ensure the shared Nix store and Claude config directories exist on the host.
- `-v "$project_dir:/workspace"` — Bind-mount the project directory into the container. Edits are visible on both sides.
- `-v "$nix_cache:/nix"` — Bind-mount a shared Nix store. Persisted across containers so packages are downloaded once. **Do not delete `~/.dev-containers/nix/` while a container is running** — it replaces the container's entire `/nix`, so removing it breaks the container's Nix installation.
- `-v "$claude_config:/root/.claude"` — Bind-mount Claude Code's config directory. Persists authentication and settings across containers so you only log in once.
- `--ssh` — Forward the host SSH agent so git clone/push works inside the container.
- `nixos/nix` — Stock OCI image with Nix pre-installed (Alpine-based).
- **Claude Code install** — Checks for the `claude` binary at the known install path (`/nix/.npm-global/bin/claude`). If missing, installs Node.js via Nix and Claude Code via npm. The npm prefix is set to `/nix/.npm-global` so it persists in the shared Nix store across containers.
- **PATH persistence** — Writes `export PATH="/nix/.npm-global/bin:$PATH"` to `~/.profile` so the login shell can find the `claude` binary after `exec /bin/sh -l` replaces the setup script.
- **claude alias** — Aliases `claude` to `claude --dangerously-skip-permissions` with `--append-system-prompt` injecting the container IP. This tells Claude to display dev server URLs using the container IP instead of localhost. Guarded to avoid duplicate entries.
- **Startup message** — Prints the container's IP address. Services launched inside the container (dev servers, etc.) are directly accessible from the host at `http://<container-ip>:<port>` — no port forwarding required.

### Networking

Apple Containers get their own IP address on a virtual network that's directly routable from the host. When Claude launches a dev server on any port, you can access it from your host browser at `http://<container-ip>:<port>`.

The container IP is printed at startup. To retrieve it later:

```bash
# From inside the container
hostname -i

# From the host
container ls --format json | jq -r '.[] | select(.status == "running") | .networks[0].address'
```

No `--publish` / `-p` port mapping is needed. Claude can use any port without pre-configuration.

### Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `DEV_CONTAINER_NIX_CACHE` | `$HOME/.dev-containers/nix` | Override the shared Nix store location on the host |
| `DEV_CONTAINER_CLAUDE_CONFIG` | `$HOME/.dev-containers/claude` | Override the Claude Code config directory on the host |

### Installation

Add the function to your shell profile — `~/.bashrc`, `~/.zshrc`, or a file sourced by your shell (e.g., `~/.local/etc/profile.d/`).
