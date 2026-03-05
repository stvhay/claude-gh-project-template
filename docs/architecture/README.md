# Architecture Theory

This directory documents the theoretical foundations behind this template's design decisions.

## Why Theory Matters

Understanding *why* these patterns work helps you adapt them to your project's needs and make informed architectural decisions. These documents explain the academic research and practical experience that shaped this template's approach to organizing code for AI agents.

## Reading Guide

**Suggested order:**

1. [VSA Foundations](vsa-foundations.md) — Why vertical slices reduce cognitive load
2. [Agent-Oriented Design](agent-oriented-design.md) — Designing codebases for AI consumption
3. [Context Optimization](context-optimization.md) — Three-tier architecture and context budgeting
4. [SPEC.md Rationale](spec-rationale.md) — Why machine-readable specifications

**Quick summaries:**

| Document | Focus |
|---|---|
| [vsa-foundations.md](vsa-foundations.md) | Why feature-based organization beats layered architecture for both humans and agents |
| [spec-rationale.md](spec-rationale.md) | How machine-readable specifications help agents maintain correctness |
| [context-optimization.md](context-optimization.md) | Why single-file configs don't scale and how three-tier architecture solves it |
| [agent-oriented-design.md](agent-oriented-design.md) | Self-contained components and progressive disclosure for agent workflows |

## Key Academic Papers

**Codified Context for AI Agents:**
- **"Codified Context: Infrastructure for AI Agents in a Complex Codebase"** (2026) — arXiv:2602.20478
  - Three-tier architecture (hot/warm/cold memory) for 108,000-line systems
  - https://arxiv.org/abs/2602.20478

**Vertical Slice Architecture:**
- **Jimmy Bogard (2018)** — "Vertical Slice Architecture"
  - Foundational practitioner work introducing the pattern
  - https://www.jimmybogard.com/vertical-slice-architecture/

**Agentic AI Systems:**
- **"Agentic Artificial Intelligence: Architectures, Taxonomies, and Evaluation"** (2026) — arXiv:2601.12560
  - Unified taxonomy for understanding agent components
  - https://arxiv.org/abs/2601.12560

**Cognitive Load Research:**
- **Gonçales et al. (2021)** — "Measuring the cognitive load of software developers"
  - Systematic mapping study of 63 papers on developer cognitive load
  - https://www.sciencedirect.com/science/article/abs/pii/S095058492100046X

**Context Engineering:**
- **Anthropic (2024)** — "Effective context engineering for AI agents"
  - Best practices for context management and agent interfaces
  - https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

See individual theory documents for complete citations and additional sources.
