# SPEC.md: Machine-Readable Specifications

## The Invisible Invariant Problem

Code shows *what* a system does, not *why* it does it that way. Invariants—things that must always be true—often exist only in developers' heads or scattered across comments. When an agent modifies code, it can easily violate these invisible constraints without realizing the breakage.

Research on LLM-based code generation shows agents achieve only 19% success on real-world GitHub issues [AutoCodeRover 2024] and 53% on manually-annotated repository tasks [DevEval 2024]. A major failure mode: violating unstated invariants because the code doesn't encode its own correctness conditions.

## Why Machine-Readable Specs

SPEC.md files make invariants explicit and verifiable. Each subsystem declares:
- **Invariants (INV-N):** Conditions that must always hold
- **Failure modes (FAIL-N):** Known ways the system breaks and how to fix them
- **Public interface:** Contracts other subsystems depend on
- **Dependencies:** What this subsystem requires

Before modifying code, an agent reads the nearest SPEC.md (walking up the directory tree like .gitignore resolution), understands the contracts, and verifies proposed changes won't violate invariants.

This approach builds on design-by-contract principles but optimizes for agent consumption: structured markdown with explicit IDs (INV-1, FAIL-2) that map directly to tests. The Formal-LLM framework demonstrated that constraining LLM behavior with formal specifications significantly improves correctness [arXiv:2402.00798, 2024].

## Test-Driven Architecture

Each SPEC.md item maps to a test:
- INV-1 → `test_inv1_description()  # Tests INV-1`
- FAIL-2 → `test_fail2_description()  # Tests FAIL-2`

Inline comments on test function definitions create bidirectional traceability: given a spec item, find its test; given a failing test, find the violated invariant. This stays in sync naturally because the comment lives next to the code it describes.

The SWE-agent research showed that better agent-computer interfaces significantly improve task completion rates [Yang et al. 2024]. SPEC.md provides that interface for subsystem-level understanding.

## Size as a Decomposition Signal

SPEC.md files target 80-300 lines. Under 80 suggests missing invariants; over 300 signals the subsystem should split. This isn't arbitrary—it maps to the context budget principle: each subsystem should fit in ~50% of an agent's context window (SPEC.md + source files).

When a spec grows too large, it's telling you the subsystem has too many responsibilities. Split it along natural boundaries, each with its own focused spec.

## Implementation in This Template

See [`docs/spec-template.md`](../spec-template.md) for the format and [`/codify-subsystem`](../../.claude/skills/codify-subsystem/SKILL.md) skill for interactive creation.

## Sources

- Zhan, Q., et al. (2024). "Formal-LLM: Integrating Formal Language and Natural Language for Controllable LLM-based Agents." arXiv:2402.00798. https://arxiv.org/abs/2402.00798

- Yang, J., Jimenez, C., et al. (2024). "SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering." NeurIPS 2024. arXiv:2405.15793. https://arxiv.org/abs/2405.15793

- Zhang, Y., et al. (2024). "AutoCodeRover: Autonomous Program Improvement." arXiv:2404.05427. https://arxiv.org/abs/2404.05427

- Li, J., et al. (2024). "DevEval: A Manually-Annotated Code Generation Benchmark Aligned with Real-World Code Repositories." ACL 2024 Findings. arXiv:2405.19856. https://arxiv.org/abs/2405.19856

- Meyer, B. (1992). "Design by Contract." Advances in Object-Oriented Software Engineering. Prentice Hall.
