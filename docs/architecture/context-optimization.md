# Context Optimization: Three-Tier Architecture

## The Scaling Problem

Single-file configuration approaches (`.cursorrules`, monolithic `CLAUDE.md`) work for prototypes but fail at scale. Research shows that even models claiming 1M+ token windows experience severe performance degradation beyond 100K tokens—drops exceeding 50% [JetBrains 2025]. The smallest possible set of high-signal tokens maximizes agent effectiveness [Anthropic 2024].

A recent study on codified context demonstrated this empirically: a 108,000-line C# system couldn't be managed with single-file configuration and required structured three-tier architecture to maintain agent coherence across 283 development sessions [arXiv:2602.20478, 2026].

## Three-Tier Solution

This template implements a three-tier context architecture:

**Hot tier (CLAUDE.md):** Always-loaded constitution (~1-2K tokens)
- Project purpose and organizing principles
- Global standards and workflow
- Links to deeper documentation

**Warm tier (SPEC.md):** Subsystem-specific, loaded on-demand
- Agents walk up the directory tree from their working file
- Load nearest SPEC.md (like .gitignore resolution)
- Scoped to one subsystem: invariants, interfaces, dependencies

**Cold tier (MANIFEST.md + semantic retrieval):** Repository-wide index
- Lists all subsystems with summaries
- Enables discovery beyond immediate working directory
- Pairs with semantic retrieval for large codebases (see [local-rag](https://github.com/aihaysteve/local-rag))

## Routing Patterns

Agents load context progressively:
1. Start with hot tier (always loaded)
2. Walk directory tree upward to find warm tier (nearest SPEC.md)
3. Consult cold tier only when crossing subsystem boundaries
4. Load adjacent subsystems' Public Interface contracts, not full specs

This mirrors how developers navigate: start local, expand scope only when needed.

## Context Budgeting

Each subsystem targets ~50% of the agent's context window (SPEC.md + source files combined). This isn't arbitrary—it leaves room for:
- Tool outputs and intermediate reasoning
- Multiple subsystems in cross-cutting tasks
- Error messages and debugging information

When a subsystem exceeds this budget, decomposition is needed. The context constraint becomes an architectural forcing function: if an agent can't hold your subsystem in context, humans will struggle too.

The Codified Context research demonstrated this scales to enterprise systems: their 34-specification knowledge base with 19 specialized agents maintained consistency across long-running development work [arXiv:2602.20478, 2026].

## Implementation in This Template

See [`docs/specs/MANIFEST.md`](../specs/MANIFEST.md) for the cold-tier index and the Architecture section of [`CLAUDE.md`](../../CLAUDE.md#architecture) for complete tier descriptions.

## Sources

- Codified Context Research (2026). "Codified Context: Infrastructure for AI Agents in a Complex Codebase." arXiv:2602.20478. https://arxiv.org/abs/2602.20478

- JetBrains Research (2025). "Cutting Through the Noise: Smarter Context Management for LLM-Powered Agents." https://blog.jetbrains.com/research/2025/12/efficient-context-management/

- Anthropic Engineering (2024). "Effective context engineering for AI agents." https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

- Google Developers (2025). "Architecting efficient context-aware multi-agent framework for production." https://developers.googleblog.com/architecting-efficient-context-aware-multi-agent-framework-for-production/
