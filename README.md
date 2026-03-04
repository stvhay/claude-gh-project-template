# Project Template

A GitHub project template with [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills for structured contribution workflows.

This template provides a ready-to-use project skeleton with brainstorming, planning, execution, verification, and code review skills bundled in `.claude/skills/`. Every contribution follows a repeatable process: issue, brainstorm, plan, execute, verify, review, merge.

## Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (Anthropic's CLI agent)
- [direnv](https://direnv.net/) (hooks into your shell to auto-load the environment)

Plus one of:
- [Nix](https://nixos.org/download/) with flakes enabled, **or**
- [Homebrew](https://brew.sh/) (macOS)

## Setup (Nix)

```bash
git clone <your-repo-url>
cd <your-repo>
direnv allow    # loads the Nix dev shell
```

## Setup (Homebrew)

```bash
git clone <your-repo-url>
cd <your-repo>
direnv allow    # verifies dependencies are present
```

## Start

```bash
claude
```

Then follow the workflow defined in `CLAUDE.md`.

For quick-start aliases and usage examples, see [USAGE.md](USAGE.md).

## What's Included

| Path | Purpose |
|---|---|
| `CLAUDE.md` | Onboarding flow (rewrites itself on first run) |
| `CONTRIBUTING.md` | Skill-driven contribution workflow |
| `.claude/skills/` | Bundled skills (brainstorming, planning, verification, etc.) |
| `.github/` | PR template and issue templates |
| `flake.nix` | Nix dev environment (add your dependencies here) |
| `.envrc` / `.envrc.d/` | direnv setup with extensible init scripts |
| `docs/FIRST_RUN.md` | Project memory initialization |


## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution workflow.

## License

[MIT](LICENSE)
