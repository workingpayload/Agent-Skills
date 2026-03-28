---
name: polyglotshift
description: Translate code accurately between programming languages, preserving logic and semantics while adopting target-language idioms, type systems, and standard libraries. Use when a user needs to port, convert, or rewrite code from one language to another.
---

# PolyglotShift

## Overview

PolyglotShift translates code between programming languages with semantic fidelity, idiomatic target-language style, and explicit annotation of every non-trivial mapping decision.

## Workflow

### 1. Identify Source & Target Languages

State both explicitly. If the user hasn't specified the target, ask. Confirm the target's major version (e.g., Python 3.11, TypeScript 5, Java 21, Rust 2021 edition) as standard library APIs differ.

### 2. Audit Type System Differences

Map source types to target equivalents before writing any code:

| Concept | Python | TypeScript | Java | Rust |
|---|---|---|---|---|
| Optional value | `Optional[T]` / `T \| None` | `T \| undefined` / `T \| null` | `Optional<T>` | `Option<T>` |
| Dynamic list | `list[T]` | `T[]` / `Array<T>` | `List<T>` | `Vec<T>` |
| Key-value map | `dict[K, V]` | `Record<K,V>` / `Map<K,V>` | `Map<K,V>` | `HashMap<K,V>` |
| Error handling | `raise` / `try/except` | `throw` / `try/catch` | `throw` / checked exceptions | `Result<T,E>` |
| Async | `async/await` + `asyncio` | `async/await` + `Promise` | `CompletableFuture` | `async/await` + `tokio` |

Flag any source types that have no direct equivalent — these require a design decision, not a mechanical substitution.

### 3. Map Idioms Explicitly

Do not transliterate — translate. Apply target-language conventions:

- **Python → TypeScript**: Replace list comprehensions with `.filter().map()`, `dataclass` with a `type` or `interface`, `__dunder__` methods with class methods or operator overloads where supported.
- **Python → Rust**: Replace `None` with `Option<T>`, `raise Exception` with `Err(...)`, GC-managed objects with owned structs + lifetimes. Flag heap allocations explicitly.
- **Java → Kotlin**: Replace verbose getters/setters with `data class`, `Optional` with `?` nullable types, `Stream` API with Kotlin collection extensions.
- **JavaScript → TypeScript**: Add explicit type annotations; replace `any` with proper generics; convert callback-style APIs to `async/await`.
- **SQL dialects**: Flag `ILIKE` (Postgres-only), `LIMIT`/`TOP` differences, and window function syntax variations.

### 4. Write the Translation

Structure the output as:

```
## Source ({source_lang})
<original code block>

## Target ({target_lang})
<translated code block, with inline comments on non-obvious mappings>

## Translation Notes
- <mapping 1: why X became Y>
- <mapping 2: semantic difference to be aware of>
- <any behavioral differences or caveats>
```

Inline comments should use the pattern `// [PolyglotShift] reason for this choice`.

### 5. Verify Semantic Equivalence

After translating, manually trace through at least one representative input/output path in both versions. Check:
- Loop bounds and off-by-one behavior.
- Error paths: does the translated code surface the same errors?
- Mutability: does the source mutate in place where the target version creates a new object?
- Integer overflow/underflow (especially Python's arbitrary-precision int → fixed-width Java/Rust int).

## Additional Mapping Patterns

**Prototype mutation / monkey patching:** Languages like JavaScript, Ruby, and Python allow modifying built-in prototypes or classes at runtime. This has no safe equivalent in statically typed targets. When translating monkey-patched code: (a) extract the patched behavior into a standalone utility function or wrapper class, (b) replace call sites with explicit calls to the wrapper, (c) document the original intent in a `// [PolyglotShift]` comment.

**`asyncio.gather` → Rust concurrent futures:**
```python
results = await asyncio.gather(fetch_a(), fetch_b(), fetch_c())
```
```rust
// tokio::join! for a fixed set of futures
let (a, b, c) = tokio::join!(fetch_a(), fetch_b(), fetch_c());
// FuturesUnordered for a dynamic collection
use futures::stream::{FuturesUnordered, StreamExt};
let mut tasks: FuturesUnordered<_> = urls.iter().map(|u| fetch(u)).collect();
while let Some(result) = tasks.next().await { ... }
```

**Java checked exceptions → Python:** Java's checked exceptions (declared in `throws`) enforce caller handling at compile time. Python has no equivalent. When translating: document every checked exception as a `Raises:` entry in the docstring, and consider wrapping callers in explicit `try/except` blocks corresponding to each checked exception type. Do not silently swallow them.

## Edge Cases

**1. Garbage-collected → memory-managed languages (e.g., Python/Java → Rust/C++).** Ownership and lifetime semantics have no direct equivalent. Identify every heap allocation in the source, decide whether the Rust translation should use `Box<T>`, `Rc<T>`, or `Arc<T>`, and document the decision. Do not silently clone everywhere — explain the trade-off.

**2. Dynamic typing → static typing with incomplete type information.** Source code using duck typing or `any`-typed inputs requires the translator to infer or ask for the intended type contracts. List every place where a type assumption was made and flag it for human review.

**3. Standard library gaps.** The source may use a library (e.g., Python's `itertools`, Java's `Guava`) with no direct target equivalent. In these cases: (a) identify the closest built-in, (b) link to a well-maintained equivalent library if one exists, (c) write a minimal inline implementation if neither exists. Never silently drop functionality.
