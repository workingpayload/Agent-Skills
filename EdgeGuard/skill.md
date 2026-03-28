---
name: edgeguard
description: Systematically finds edge cases using boundary value analysis, equivalence partitioning, property-based testing (Hypothesis/fast-check), fuzzing, and mutation testing. Use when a user asks to find edge cases, stress-test logic, or make tests more robust.
---

# EdgeGuard

## Overview

Go beyond happy-path tests to find the inputs that break things. Use structured techniques — not intuition — to systematically enumerate edge cases, then verify them with property-based tests, fuzz tests, and mutation testing.

## Workflow

### 1. Boundary Value Analysis (BVA)

For every numeric, string-length, or date input, test at:
- The exact minimum allowed value
- Minimum - 1 (just below valid range)
- Minimum + 1 (just above minimum)
- A nominal value in the middle
- Maximum - 1
- The exact maximum allowed value
- Maximum + 1 (just above valid range)

```python
# Function: def set_age(age: int) — valid range 0..150
# BVA test cases:
test_cases = [-1, 0, 1, 75, 149, 150, 151]
```

For string lengths: empty string `""`, one character, max length, max length + 1.
For collections: empty list, single element, two elements, at or near the size limit.

### 2. Equivalence Partitioning

Divide inputs into classes where the code behaves identically, then test one value from each class. For an HTTP status-code classifier: one test each for `[100-199]`, `[200-299]`, `[300-399]`, `[400-499]`, `[500-599]`, `[<100]`, `[>599]`, non-integer. Test one value per partition: `101, 200, 301, 404, 503, 99, 600, "abc"`.

### 3. Property-Based Testing

Write tests that assert invariants hold for thousands of randomly generated inputs, not just hand-picked ones.

**Python with Hypothesis:**
```python
from hypothesis import given, strategies as st, assume

@given(st.lists(st.integers()))
def test_sort_preserves_length(lst):
    assert len(sorted(lst)) == len(lst)

@given(st.integers(min_value=0), st.integers(min_value=0))
def test_add_is_commutative(a, b):
    assert add(a, b) == add(b, a)

@given(st.text(min_size=1, max_size=100))
def test_slugify_is_idempotent(text):
    assume(text.strip())  # skip pure-whitespace
    slug = slugify(text)
    assert slugify(slug) == slug

```

**TypeScript/JavaScript with fast-check:**
```typescript
import fc from 'fast-check';
test('reverse is involution', () => {
  fc.assert(fc.property(fc.array(fc.integer()), (arr) => {
    expect(reverse(reverse(arr))).toEqual(arr);
  }));
});
```

### 4. Fuzz Testing

Feed random, malformed, or adversarial input to find crashes and panics.

**Python with Atheris:**
```python
import atheris
import sys

def TestOneInput(data):
    fdp = atheris.FuzzedDataProvider(data)
    text = fdp.ConsumeUnicodeNoSurrogates(100)
    try:
        parse_user_input(text)
    except ValueError:
        pass  # expected — not a bug
    # Any other exception is a bug and will be reported

atheris.Setup(sys.argv, TestOneInput)
atheris.Fuzz()
```

**Go:**
```go
func FuzzParseConfig(f *testing.F) {
    f.Add([]byte(`{"key":"value"}`))
    f.Fuzz(func(t *testing.T, data []byte) {
        _, err := ParseConfig(data)
        if err != nil {
            return // expected
        }
    })
}
```
Run: `go test -fuzz=FuzzParseConfig -fuzztime=60s`

### 5. Mutation Testing

Verify that your tests catch real bugs by deliberately introducing mutations and checking if tests fail.

**Python with mutmut:**
```bash
mutmut run --paths-to-mutate=src/
mutmut results       # shows surviving mutants (= tests that missed a bug)
mutmut show 23       # shows the specific mutation that survived
```

**JavaScript with Stryker:**
```bash
npx stryker run
# Opens HTML report showing which mutants survived
```

A surviving mutant means: "I changed the code in a plausible way and no test caught it." Write a test that kills each surviving mutant.

Target: mutation score >= 80%.

**Mutation testing cost management**: Full mutation runs are slow. Scope to changed files only: `mutmut run --paths-to-mutate=src/changed_module.py`. Schedule full runs nightly in CI, not on every PR. Use `--parallel` (Stryker) or `mutmut run --no-progress` with `xdist` workers to parallelize execution.

### 6. High-Value Edge Cases by Type

| Type | Key cases |
|------|-----------|
| Strings | `""`, `" "`, null bytes `"\0"`, Unicode surrogates, >1MB, SQL injection, path traversal `../../` |
| Numbers | `0`, `-0`, `NaN`, `Infinity`, `MAX_SAFE_INTEGER+1`, very small floats near zero |
| Collections | empty, single element, all-identical, sorted asc/desc, null elements |
| Dates | Feb 29, DST spring-forward (2:30 AM), year 2038 (32-bit Unix overflow), midnight |
| Concurrency | simultaneous access, duplicate requests (idempotency), partial failure mid-transaction |

## Output Format

For each function or module analyzed, provide:

1. **BVA table**: input → expected output/behavior
2. **Equivalence classes**: list each partition and which value tests it
3. **Property tests**: `@given` or `fc.property` test file
4. **Edge case checklist**: domain-specific list of cases tried

## Edge Cases of the Technique Itself

**Hypothesis CI reproducibility**: Hypothesis stores found examples in `.hypothesis/`. Commit this directory so CI reproduces failures deterministically. Pin the seed for scheduled runs: `pytest --hypothesis-seed=0`. Without a fixed seed, flaky Hypothesis failures are hard to reproduce locally.

**Fuzz testing cleanup**: Fuzz corpora and crash inputs accumulate in temp directories. Use `tmp_path` (pytest) or `TMPDIR` pointed at a ramdisk to avoid disk fill on long runs. Always set `fuzztime` limits in CI: `go test -fuzz=. -fuzztime=60s`. Clean up artifacts in post-run CI steps.

**Hypothesis finding a counterexample unexpectedly**: When Hypothesis fails, it shrinks the input to the minimal reproducing case. Read the `@example` decorator it prints — add it as a regression test so this specific case always runs.

**Mutation testing on I/O-heavy code**: Mutmut/Stryker work best on pure logic. For code with database calls or HTTP, use the mutation score only on the business logic layer, not on infrastructure adapters.

**Infinite loops from property tests**: If the code under test can loop indefinitely given certain inputs, wrap it with a timeout (`@settings(deadline=timedelta(milliseconds=500))` in Hypothesis) rather than letting CI hang.
