# Agent-Oriented Design

## Optimizing for Agent Consumption

Traditional software architecture optimizes for human developers navigating with IDEs: jump-to-definition, find-all-references, symbol search. These tools let developers hop across layers and files instantly.

AI agents work differently. They can't "jump" without loading files into context. Cross-references cost tokens. Global searches return too many results. Research on repository-level code generation shows agents struggle with scattered dependencies and indirect coupling [RepoGraph 2024]. The Ann Arbor Architecture for agent-oriented programming formalizes this: systems should minimize context-switching overhead and maximize local coherence [arXiv:2502.09903, 2025].

## Self-Contained Principle

Agent-oriented design follows one rule: minimize coupling between subsystems, maximize coupling within subsystems. This is Bogard's VSA principle adapted specifically for agent constraints.

**Self-contained means:**
- A subsystem's SPEC.md + source files fit in ~50% of context
- Dependencies are explicit and minimal
- Public interfaces are documented in the spec
- An agent can understand and modify the subsystem without loading others

**This differs from traditional microservices or bounded contexts:** those optimize for deployment and team boundaries. Agent-oriented design optimizes for context window constraints.

## Progressive Disclosure

Agents should load what they need, when they need it:

1. **Local work:** Load only the nearest SPEC.md and local files
2. **Adjacent coordination:** Load Public Interface sections (not full specs)
3. **Cross-cutting tasks:** Split the work by subsystem boundary

Research on agentic AI systems identifies this as a core architectural pattern: agents with clear task boundaries and explicit interfaces outperform agents that must navigate complex interdependencies [arXiv:2601.12560, 2026].

## Agent Workflow Pattern

The template enforces this workflow:

1. **Load context:** Walk directory tree to find nearest SPEC.md
2. **Understand contracts:** Read invariants, interfaces, dependencies
3. **Modify safely:** Make changes within documented boundaries
4. **Verify correctness:** Run tests mapped to spec items (INV-N, FAIL-N)

This maps to how agents reason best: given explicit preconditions and postconditions, they generate correct transformations. The Formal-LLM framework demonstrated 44% accuracy improvement when constraining agent behavior with formal specifications [arXiv:2402.00798, 2024].

## Design Guidelines

When structuring a codebase for agents:
- **Prefer duplication over abstraction** when it keeps subsystems independent
- **Make dependencies explicit** in SPEC.md, don't rely on implicit coupling
- **Document the *why*** (invariants, design decisions), not just the *what* (code)
- **Split when context budget exceeded:** If SPEC.md + files > 50% of window, decompose

The goal: an agent should load one directory and have everything needed to work safely.

## Implementation in This Template

See the workflow in [`CONTRIBUTING.md`](../../CONTRIBUTING.md) for how this template's skills guide agents through the pattern.

## Sources

- RepoGraph Research (2024). "RepoGraph: Enhancing AI Software Engineering with Repository-level Code Graph." arXiv:2410.14684. https://arxiv.org/abs/2410.14684

- Ann Arbor Architecture (2025). "The Ann Arbor Architecture for Agent-Oriented Programming." arXiv:2502.09903. https://arxiv.org/abs/2502.09903

- Agentic AI Taxonomy (2026). "Agentic Artificial Intelligence (AI): Architectures, Taxonomies, and Evaluation of Large Language Model Agents." arXiv:2601.12560. https://arxiv.org/abs/2601.12560

- Formal-LLM Framework (2024). "Formal-LLM: Integrating Formal Language and Natural Language for Controllable LLM-based Agents." arXiv:2402.00798. https://arxiv.org/abs/2402.00798

- Anthropic Research (2024). "Building Effective Agents." https://www.anthropic.com/research/building-effective-agents
