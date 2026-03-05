# Design: Apple Container Launcher

**Issue:** None (exploratory)
**Date:** 2026-03-04
**Branch:** feature/apple-container-launcher

## Summary

A `dev-container` shell function that launches an Apple Container with the
`nixos/nix` image, bind-mounts the project directory and a shared Nix store,
installs Claude Code, and drops the user into an interactive shell.

## Approach

**Image:** Stock `nixos/nix` from Docker Hub (Alpine-based, Nix pre-installed,
OCI-compatible). No custom image build required.

**Alternatives considered:**
- Custom Nix-built OCI image via `dockerTools.buildLayeredImage` — more
  declarative but more upfront work. Can iterate to this later.
- Full NixOS image — heavier, less well-maintained upstream, overkill for a
  dev shell.

## Architecture

### Bind Mounts

| Host Path | Container Path | Purpose |
|---|---|---|
| `<project-directory>` | `/workspace` | Project source code, editable from both sides |
| `~/.dev-containers/nix/` | `/nix` | Shared Nix store, persisted across containers |
| `~/.dev-containers/claude/` | `/root/.claude` | Claude Code config and credentials, persisted across containers |

> **Caution:** Do not delete `~/.dev-containers/nix/` while a container is
> running. The bind mount replaces the container's entire `/nix`, so removing
> the host directory breaks the container's Nix installation (including
> `nix-env` itself). Likewise, avoid deleting `~/.dev-containers/claude/`
> while running — Claude Code may fail or lose session state mid-operation.

### Networking

Apple Containers get their own IP address on a virtual network that's
directly routable from the host. No port publishing (`-p`) is needed —
services launched inside the container are accessible from the host at
`http://<container-ip>:<port>`.

The container IP is printed at startup. It can also be retrieved via:
- Inside: `hostname -i`
- Host: `container ls --format json | jq -r '.[] | select(.status == "running") | .networks[0].address'`

Apple Container also supports `-p host:container` port forwarding (same
syntax as Docker, but no range support), but direct IP access is simpler
since it requires no pre-configuration of ports.

### SSH

`--ssh` forwards the host SSH agent into the container so git clone/push
works without additional key configuration.

### Claude Code

Installed automatically on first container start via npm. The install check
uses a direct path test (`[ -x /nix/.npm-global/bin/claude ]`) rather than
`command -v` to avoid false negatives before PATH is configured. Cached in
the shared Nix store so subsequent containers skip installation.

Claude Code's config directory (`~/.claude`) is bind-mounted from the host,
so authentication and settings persist across containers. The host stores
API keys in the macOS Keychain, but inside the Linux container Claude Code
uses file-based credential storage. The first `claude` run triggers an auth
flow; subsequent containers reuse the saved credentials.

The PATH for `/nix/.npm-global/bin` is written to `~/.profile` so it
persists when `exec /bin/sh -l` replaces the setup script with a login
shell. A shell alias sets bypass permissions and injects container context:

```bash
alias claude='claude --dangerously-skip-permissions --append-system-prompt "You are running inside an Apple Container. The container IP is <IP>. When launching or displaying URLs for dev servers, use http://<IP>:<port> instead of localhost."'
```

The `--append-system-prompt` flag adds instructions to Claude's system
prompt without replacing the defaults. The container IP is interpolated at
startup so Claude always shows the correct URL for accessing dev servers
from the host.

Both the PATH export and alias are written to `~/.profile` on the container
filesystem (`/root/.profile` — not inside a bind mount). The
`# dev-container` marker guards against duplicate entries if a stopped
container is restarted. The alias only exists inside the container.

### Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `DEV_CONTAINER_NIX_CACHE` | `$HOME/.dev-containers/nix` | Override shared Nix store location |
| `DEV_CONTAINER_CLAUDE_CONFIG` | `$HOME/.dev-containers/claude` | Override Claude Code config directory |

## The Function

```bash
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

  local name_hash
  name_hash=$(printf '%s' "$project_dir" | shasum | cut -c1-12)
  local container_name="dev-${name_hash}"

  if container inspect "$container_name" &>/dev/null
  then
    echo "Error: container for '$project_dir' already exists as '$container_name'" >&2
    echo "  container rm $container_name" >&2
    return 1
  fi

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

      cd /workspace || { echo "Error: /workspace not available" >&2; exit 1; }
      # \$1 because outer single-quote → inner sh sees \$1 in double quotes → literal $1 for awk
      CONTAINER_IP=$(hostname -i 2>/dev/null | awk "{print \$1}")
      [ -n "$CONTAINER_IP" ] || echo "Warning: could not determine container IP" >&2

      # Write PATH and claude alias to ~/.profile for the login shell.
      # The heredoc (<<PROFILE) is parsed by the inner sh, not the outer shell,
      # because it appears inside a single-quoted sh -c string. $CONTAINER_IP
      # expands (inner sh variable), while \$PATH is literal (escaped for profile).
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

## Deliverables

1. Add the `dev-container` function to `USAGE.md` alongside `dev-init`
2. Document the env vars and what each mount does

## Known Limitations

- **Opaque container names** — `dev-<hash>` names are not human-readable.
  Use `container ls -a` to find container names, or note the name printed
  at startup.

## Not In Scope

- Custom OCI image building (can iterate later)
- Multi-container orchestration
- Persistent container state beyond the Nix store and Claude Code config
- Auto-launching Claude Code (user starts it manually)

## Requirements

- macOS 26 (Tahoe) with Apple Container installed
- Apple Silicon Mac
