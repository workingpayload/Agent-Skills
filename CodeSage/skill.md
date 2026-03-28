---
name: codesage
description: Performs structured code reviews with severity-tiered findings covering security, correctness, performance, and maintainability. Uses language-specific linters and static analysis tools. Use when a user submits code for review, asks for feedback on a PR, or needs an audit of a module or function.
---

# CodeSage

## Domain Scope

Code review across languages (Python, TypeScript/JavaScript, Java, Go, Rust, C/C++), covering: correctness bugs, security vulnerabilities, performance anti-patterns, API design, test coverage gaps, and maintainability issues. Output is structured by severity tier.

---

## Severity Tiers

Every finding must be tagged with a severity:

| Tier | Label | Meaning | Action required |
|------|-------|---------|-----------------|
| 1 | **CRITICAL** | Security vulnerability, data loss risk, or crash-causing bug | Block merge; must fix |
| 2 | **HIGH** | Logic error, incorrect behavior under edge cases, significant performance issue | Block merge; must fix |
| 3 | **MEDIUM** | Code smell, missing error handling, test gap, suboptimal approach | Fix before merge preferred |
| 4 | **LOW** | Style, naming, minor readability, non-idiomatic code | Fix or acknowledge |
| 5 | **NOTE** | Suggestion, alternative approach, educational context | No action required |

---

## Workflow

### 1. Identify Language and Context
- Detect language from file extension and syntax.
- Note: framework (React, Spring, FastAPI), runtime (Node, JVM, Python 3.11+), and test framework.
- Check if this is new code, a modification, or a refactor.

### 2. Static Analysis Pass (Automated Tools)
Run mentally (or recommend the user run):

**Python**: `ruff check` (style + basic errors), `mypy --strict` (type errors), `bandit -r .` (security), `pylint` (additional checks).

**TypeScript/JavaScript**: `eslint --max-warnings 0` with `@typescript-eslint/recommended`, `eslint-plugin-security`, `eslint-plugin-unicorn`. `tsc --noEmit` for type checking.

**Java**: SpotBugs + FindSecurityBugs plugin, Checkstyle, SonarQube rules. PMD for code quality.

**Go**: `go vet ./...`, `staticcheck ./...`, `gosec ./...`, `golangci-lint run`.

**Rust**: `cargo clippy -- -D warnings`, `cargo audit`, `cargo geiger` (unsafe usage audit).

**C/C++**: `clang-tidy`, `cppcheck`, AddressSanitizer/UBSan in tests.

### 3. Security Review Checklist
Check for OWASP Top 10 patterns, including:

**OWASP A02 — Cryptographic Failures**: Flag any custom or hand-rolled cryptography implementation as CRITICAL — no exceptions. Recommend library-only crypto (`cryptography` in Python, `libsodium`, `WebCrypto API`). Common red flags: custom XOR/ROT ciphers, MD5/SHA-1 for security, ECB mode, hardcoded IVs/keys, non-constant-time secret comparisons.

**Feature Flag Removal Review**: When a feature flag is being removed (flag permanently on), verify all guarded code paths are cleaned up:
- [ ] Flag check condition and its `else` branch both removed (not just the `if`).
- [ ] Dead code path (the disabled branch) deleted, not just unreachable.
- [ ] Flag definition removed from config/constants and feature flag service.
- [ ] Tests for the old disabled path removed; tests for the enabled path remain without the flag setup.

**LLM-Generated Code Review**: Apply elevated scrutiny to code known or suspected to be AI-generated:
- Verify all referenced APIs, methods, and library functions actually exist — LLMs hallucinate plausible-sounding but non-existent APIs.
- Increase semantic testing requirement: generated code often passes syntactic checks but has subtle logic errors in edge cases. Add property-based tests or fuzz the inputs.
- Check for over-confident error handling (`except Exception: pass` patterns are common in generated code).
- Do not assume generated code follows your codebase's security conventions — recheck the full security checklist.

Check for additional OWASP Top 10 patterns:

- [ ] **Injection**: SQL queries built with string concatenation instead of parameterized queries / ORM. Command injection via `shell=True` (Python), `exec()`/`eval()` with user input.
- [ ] **Broken auth**: Hardcoded credentials, tokens in source code, weak random (use `secrets` module, not `random`).
- [ ] **Sensitive data exposure**: PII/secrets logged, HTTP instead of HTTPS, sensitive fields not excluded from serialization.
- [ ] **Insecure deserialization**: `pickle.loads()` / `yaml.load()` (use `yaml.safe_load()`) on untrusted input.
- [ ] **XSS**: `innerHTML`, `dangerouslySetInnerHTML` with unsanitized user content.
- [ ] **Path traversal**: file paths constructed from user input without validation (`os.path.join` does not protect against absolute paths in user input).
- [ ] **SSRF**: HTTP requests to URLs from user input without allowlist validation.
- [ ] **Dependency vulnerabilities**: check `npm audit`, `pip-audit`, `cargo audit`, `trivy`.

### 4. Correctness Review

- **Off-by-one errors**: loop bounds, slice indices, pagination.
- **Null/undefined handling**: unchecked nullable access. In TypeScript: `strictNullChecks` enabled?
- **Error handling**: errors silently swallowed (`except: pass`, `.catch(() => {})`, unchecked `err` in Go). Every error must be handled, logged, or explicitly propagated.
- **Concurrency**: shared mutable state accessed without synchronization. Thread-safe collections used where needed.
- **Resource leaks**: file handles, DB connections, HTTP response bodies not closed in `finally`/`defer`/`using`.
- **Integer overflow**: especially in size calculations, array indexing, financial math (use `Decimal`, not `float`, for money).
- **Floating-point equality**: `if (x === 0.1 + 0.2)` is wrong; use epsilon comparison or integer arithmetic.

### 5. Performance Review

- **N+1 queries**: loop that issues a DB query per iteration. Fix with eager loading (`JOIN`, `prefetch_related`, DataLoader).
- **Missing database indexes**: `WHERE`, `ORDER BY`, `JOIN` columns without indexes. Check `EXPLAIN ANALYZE`.
- **Unbounded queries**: no `LIMIT` on user-triggered queries. Risk: full table scan under load.
- **Unnecessary serialization**: converting to/from JSON inside a hot loop.
- **Algorithm complexity**: O(n²) where O(n log n) or O(n) is achievable (see AlgoMaster skill).
- **Memory allocation in loops**: creating large objects, closures, or buffers inside tight loops.
- **Blocking I/O in async context**: `time.sleep()` in an async function (Python), `fs.readFileSync()` in Node.js event handler.

### 6. Maintainability Review

- **Function length**: functions > 40 lines are candidates for extraction. Single Responsibility Principle.
- **Cyclomatic complexity**: branches > 10 in a single function — extract sub-functions.
- **Magic numbers/strings**: unexplained literal values — extract to named constants.
- **Test coverage**: are happy path, error path, and edge cases covered? Missing tests for the code under review.
- **Documentation**: exported functions/classes must have docstrings. Complex algorithms need inline explanation.
- **Dead code**: unreachable branches, unused variables/imports (linters catch these).

### 7. Language-Specific Idioms

**Python**: use comprehensions over explicit loops for simple transforms; `pathlib` over `os.path`; `dataclasses` or `pydantic` over raw dicts for structured data; `contextlib.contextmanager` for resource management.

**TypeScript**: prefer `const` over `let`; use `unknown` over `any`; use discriminated unions over optional fields; prefer `Array.prototype.map/filter/reduce` over imperative loops.

**Go**: handle errors explicitly, do not use `_` for error return unless the error is truly impossible; prefer `errors.Is`/`errors.As` over string comparison; use `context.Context` for cancellation propagation.

**Rust**: prefer `Option`/`Result` over panics in library code; use `?` operator for error propagation; avoid `clone()` in hot paths; use iterators over manual indexing.

---

## Output Format

Structure the review output as:

```
## Code Review: <filename or PR title>

### Summary
<2-3 sentences: overall quality, main concerns, recommendation (approve / approve with changes / request changes)>

### Findings

#### [CRITICAL] SQL injection via string concatenation — line 47
**File**: `src/repositories/user_repo.py:47`
**Issue**: `query = f"SELECT * FROM users WHERE id = {user_id}"` — user-controlled input concatenated directly into SQL.
**Impact**: Attacker can exfiltrate entire database, bypass auth, or drop tables.
**Fix**:
```python
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

#### [HIGH] Error silently swallowed — line 83
...

#### [MEDIUM] Missing index on query filter — line 12 of migration
...

### Test Coverage Gaps
- No test for `user_id` being negative
- No test for empty result set from `list_users()`

### Positive Notes
- Good use of `contextlib.suppress` in cleanup handler
- Consistent error message format across all endpoints
```

---

## Edge Cases

1. **Reviewing auto-generated code** (e.g., from Prisma, gRPC protobuf, OpenAPI codegen): Do not flag generated files for style or structure issues — they are not human-maintained. Focus review on: (a) the generator configuration and schema (the real source), (b) any hand-written code that extends or wraps the generated code, (c) whether generated code is committed or regenerated in CI (prefer CI regeneration to avoid drift).

2. **Security findings with false positive risk**: A finding like "user input passed to a function" is not automatically a security bug — it depends on whether the function performs sanitization internally. Before escalating to CRITICAL, trace the data flow from source to sink and confirm there is no sanitization in the call chain. Use data flow analysis tools (Semgrep with taint mode, CodeQL) to reduce false positives. Always include a concrete exploit scenario to justify CRITICAL/HIGH security findings.

3. **Reviewing performance-sensitive code without profiling data**: Avoid premature optimization flags. Only flag a performance issue if: (a) the algorithmic complexity is provably worse (O(n²) where O(n) exists), (b) the pattern is a known anti-pattern (N+1 queries, blocking I/O), or (c) there is profiling data showing this is a hot path. For speculative performance concerns, use NOTE tier: "This loop allocates a new object per iteration — worth profiling if this becomes a hot path."
