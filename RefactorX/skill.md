---
name: refactorx
description: Refactor code safely using Fowler's catalog of patterns (Extract Method, Replace Conditional with Polymorphism, etc.), strangler fig for legacy systems, and cyclomatic complexity reduction. Use when a user wants to clean up code, reduce technical debt, modernize a legacy system, or improve maintainability.
---

# RefactorX

## Overview

RefactorX applies Martin Fowler's refactoring catalog in small, verifiable, atomic steps — never changing behavior, always improving structure.

## Workflow

### 1. Verify Test Coverage First (Non-Negotiable)

Refactoring without tests is rewriting. Before touching any code:
- Check for existing tests: unit, integration, or E2E.
- Run them and confirm they pass: `pytest`, `npm test`, `go test ./...`, `mvn test`.
- If coverage is below ~60% on the target code, write characterization tests first (tests that document current behavior, not desired behavior).
- If the user insists on refactoring untested code, explicitly flag the risk and document every behavioral assumption made.

### 2. Measure Complexity Baselines

Quantify the problem before fixing it:
- **Cyclomatic complexity**: `radon cc -s` (Python), `eslint` with `complexity` rule (JS/TS), `lizard` (polyglot), or `gocyclo` (Go). Flag functions with complexity > 10 as priority targets.
- **Function length**: > 40 lines is a smell; > 80 lines is a strong refactor candidate.
- **Dependency depth**: deeply nested imports or circular dependencies signal poor module boundaries.

### 3. Choose the Right Refactoring Pattern

Reference Fowler's *Refactoring* (2nd ed.) catalog by symptom:

| Symptom | Pattern | Action |
|---|---|---|
| Long method | **Extract Method** | Pull cohesive block into a named private function |
| Long parameter list | **Introduce Parameter Object** | Group related params into a struct/dataclass/record |
| Duplicate code | **Extract Method** + **Pull Up Method** | Create shared abstraction |
| Complex conditional | **Replace Conditional with Polymorphism** or **Replace Nested Conditional with Guard Clauses** | Guard clauses for preconditions; polymorphism for type-based branching |
| Large class | **Extract Class** | Separate responsibilities into distinct classes |
| Feature envy | **Move Method** | Move method to the class whose data it uses most |
| Primitive obsession | **Replace Primitive with Object** | Wrap domain values (Money, Email, UserId) in value objects |
| Speculative generality | **Collapse Hierarchy** / **Remove Dead Code** | Delete unused abstractions |

### 4. Apply the Strangler Fig Pattern for Legacy Systems

For large legacy codebases that cannot be rewritten wholesale:
1. Identify a single vertical slice of functionality (one endpoint, one module, one use case).
2. Create a new implementation alongside the old one.
3. Route a small percentage of traffic/calls to the new implementation.
4. Verify correctness via comparison testing (run both, assert same output).
5. Gradually shift all traffic to the new implementation.
6. Delete the old code.

Never attempt a "big bang" rewrite. Each strangler step should be independently deployable.

### 5. Make Atomic Changes

Each refactoring step must be:
- **A single logical change** (rename, extract, move — not all three at once).
- **Behavior-preserving**: run the test suite after each step and commit only if green.
- **Independently committable**: each commit should have a descriptive message referencing the pattern used, e.g., `refactor: extract UserValidator from UserService (Extract Class)`.

Avoid mixing refactoring commits with feature additions or bug fixes.

### 6. Deliver the Output

Provide:
1. Complexity baseline (before metrics: cyclomatic complexity, line counts).
2. Refactoring plan: ordered list of atomic steps with the pattern name for each.
3. Refactored code with inline comments explaining what changed and why.
4. Complexity after metrics showing the improvement.
5. Any test additions needed to make the refactoring safe.

## Edge Cases

**4. Thread-safety implications when refactoring concurrent code.** When extracting methods or introducing shared state in multi-threaded code, audit for new data races. Extracting a block that reads and writes shared mutable state into a separate method does not automatically make it thread-safe. Check whether the original code relied on holding a lock for the duration of the block — extracting it may break the lock scope. Use tools: `ThreadSanitizer` (Go, C/C++), `mypy --warn-unreachable` + `threading` annotations (Python), or Java's `@GuardedBy` annotations to surface lock disciplines.

**5. Public API renaming and backward compatibility.** Renaming a public symbol (function, class, module) is a breaking change. Apply the deprecation wrapper pattern: keep the old name, delegate to the new one, and emit a deprecation warning (`warnings.warn(..., DeprecationWarning, stacklevel=2)` in Python; `@Deprecated` in Java; `/** @deprecated */` JSDoc in TypeScript). Bump the semver minor version for deprecation, major version for removal. Document the removal timeline in the changelog and migration guide.

**1. Refactoring changes observable behavior due to subtle side effects.** Functions that appear pure may mutate shared state, depend on global variables, or have side effects through ORM/cache interactions. Before extracting, verify that the extracted code has no hidden dependencies. Use characterization tests to lock in the exact output including side effects.

**2. Legacy code with framework magic (e.g., Django signals, Rails callbacks, Spring AOP).** Lifecycle hooks and aspect-oriented code can make behavior non-obvious. Map all hooks attached to the classes being refactored before moving or renaming them. Missing a `before_save` callback or `@aspect` can silently break business logic.

**3. Cyclomatic complexity reduction leads to over-abstraction.** Splitting a 15-condition function into 15 tiny single-condition classes can make code harder to follow, not easier. Apply the Single Responsibility Principle at a meaningful granularity — group related conditions into 2–4 cohesive abstractions, not one class per condition. Prefer readability over metric compliance.
