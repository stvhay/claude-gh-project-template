# Vertical Slice Architecture: Foundations

## The Problem with Layers

Traditional layered architecture organizes code by technical concerns—controllers, services, repositories, models. To understand a single feature, developers must mentally assemble pieces scattered across multiple layers. Research shows this context switching costs 23 minutes per interruption [Mark et al.], and working memory holds approximately 7 items during program tracing [Crichton et al. 2021].

For AI agents, layered architecture creates a harder problem: agents must load multiple files across layers to understand one feature, exhausting their context window with cross-references rather than using tokens for reasoning.

## Why Vertical Slices Work

Vertical Slice Architecture organizes code by feature, not layer. Each feature lives in its own directory containing everything needed: handlers, validation, data access, types, and tests. A developer—or agent—loads one directory and understands the complete feature.

This pattern directly addresses cognitive load:
- **Locality:** Related code lives together, reducing context switches
- **Encapsulation:** Each slice owns its implementation details
- **Independence:** Slices can evolve without coordinating across layers

Jimmy Bogard formalized this as "minimize coupling between slices, and maximize coupling in a slice" [Bogard 2018]. A comparative study found VSA reduced complexity distribution and improved maintainability in enterprise .NET applications [IJAAIR 2025].

## Agent Benefits

For AI agents, vertical slices provide a critical advantage: a single directory load fits in the context window and contains everything needed to modify a feature safely. The agent reads one SPEC.md, understands the contracts, and works within that subsystem's boundaries—no hunting across layers, no resolving dependencies.

This maps directly to how agents work best: given a focused problem space with clear boundaries, they can reason effectively. Scatter that same feature across layers, and the agent must juggle references, increasing hallucination risk and context exhaustion.

## Key Principle

One directory = one context load = one coherent unit of functionality.

This isn't just about organization—it's about fitting human and agent working memory constraints. The same pattern that helps developers navigate code helps agents understand it.

## Implementation in This Template

See the Architecture section of [`CLAUDE.md`](../../CLAUDE.md#architecture) for how this template applies vertical slices:
- Feature-based directories for most projects
- Module-based for libraries, command-based for CLIs
- The principle stays the same: one directory = one agent context load

## Sources

- Bogard, J. (2018). "Vertical Slice Architecture." https://www.jimmybogard.com/vertical-slice-architecture/

- International Journal of Advanced Artificial Intelligence Research (2025). "Comparative Review of Clean Architecture and Vertical Slice Architecture Approaches for Enterprise .NET Applications." Vol. 2, Issue 11. https://aimjournals.com/index.php/ijaair/article/view/413

- Mark, G., Gonzalez, V. M., & Harris, J. "Attention Residue and Context Switching Costs in Software Development." University of California, Irvine. https://super-productivity.com/blog/context-switching-costs-for-developers/

- Crichton, W., et al. (2021). "The Role of Working Memory in Program Tracing." CHI 2021. https://dl.acm.org/doi/10.1145/3411764.3445257

- Gonçales, L., Farias, K., da Silva, B., & Fessler, J. (2021). "Measuring the cognitive load of software developers: An extended Systematic Mapping Study." Information and Software Technology. https://www.sciencedirect.com/science/article/abs/pii/S095058492100046X
