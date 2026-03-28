---
name: coveragemax
description: Identifies untested code paths and generates targeted unit tests to reach 80%+ coverage using pytest-cov, Jest, Istanbul/nyc, or JaCoCo. Use when a user asks to improve test coverage, add missing tests, or analyze coverage reports.
---

# CoverageMax

## Overview

Analyze existing coverage reports, identify uncovered branches and lines, then generate well-structured tests using the AAA (Arrange-Act-Assert) pattern. Target: 80% line coverage and 75% branch coverage as a minimum bar.

## Workflow

### 1. Detect the Stack and Run Coverage

**Python (pytest-cov):**
```bash
pytest --cov=src --cov-report=term-missing --cov-report=html:coverage_html
```
Read the `term-missing` output — the rightmost column lists uncovered line ranges.

**JavaScript/TypeScript (Jest):**
```bash
jest --coverage --coverageReporters=text --coverageReporters=lcov
```
Check `coverage/lcov-report/index.html` or the terminal table.

**JavaScript (Istanbul/nyc standalone):**
```bash
nyc --reporter=text --reporter=lcov npm test
```

**Java (JaCoCo via Maven):**
```bash
mvn test jacoco:report
```
Open `target/site/jacoco/index.html`. Focus on "Missed Branches" column.

**Go:**
```bash
go test ./... -coverprofile=coverage.out && go tool cover -html=coverage.out
```

**Rust (cargo-tarpaulin):**
```bash
cargo tarpaulin --out Html --output-dir coverage/
```

**Exclusion config**: Exclude generated code, migrations, and vendor files rather than artificially inflating scores.
- Python: `pytest --cov-omit="src/migrations/*,src/generated/*"` or list paths under `[tool:coverage] omit =` in `.coveragerc`
- Jest: `coveragePathIgnorePatterns: ["/migrations/", "/generated/"]` in `jest.config.js`
- Go: tag generated files with `//go:build ignore` or pass `-coverpkg` to scope coverage explicitly

### 2. Triage Coverage Gaps

Priority order for what to test first:
1. **Uncovered branches** in business logic (conditionals, early returns, switch cases)
2. **Error/exception paths** (catch blocks, null guards, validation failures)
3. **Uncovered lines** in pure functions
4. Skip: generated code, migrations, `__init__.py` re-exports, trivial getters/setters

Flag files with 0% coverage — these likely indicate missing test files entirely.

### 3. Write Tests Using AAA Pattern

Every test must have three clearly separated sections:

```python
def test_calculate_discount_applies_vip_rate():
    # Arrange
    user = User(tier="vip", cart_total=100.0)
    pricing = PricingService(vip_rate=0.20)

    # Act
    result = pricing.calculate_discount(user)

    # Assert
    assert result == 20.0
```

```typescript
it('returns 401 when token is expired', async () => {
  // Arrange
  const expiredToken = generateToken({ exp: Date.now() - 1000 });

  // Act
  const response = await request(app).get('/api/profile')
    .set('Authorization', `Bearer ${expiredToken}`);

  // Assert
  expect(response.status).toBe(401);
  expect(response.body.error).toBe('TOKEN_EXPIRED');
});
```

### 4. Cover Branch Conditions Systematically

For each `if/else`, ternary, `||`, `&&`, or `switch`, write one test per branch:
- Truthy path
- Falsy path
- Boundary value (off-by-one, empty string, zero, null)

Use parameterized tests to reduce boilerplate:

```python
@pytest.mark.parametrize("value,expected", [
    (0, False),
    (1, True),
    (-1, False),
    (None, False),
])
def test_is_positive(value, expected):
    assert is_positive(value) == expected
```

```typescript
test.each([
  [0, false],
  [1, true],
  [-1, false],
])('isPositive(%i) returns %s', (value, expected) => {
  expect(isPositive(value)).toBe(expected);
});
```

### 5. Mock External Dependencies

Never let tests hit real databases, HTTP endpoints, or file systems.

**Python:** `unittest.mock.patch`, `pytest-mock`'s `mocker.patch`
**Jest:** `jest.mock()`, `jest.spyOn()`
**Java:** Mockito `@Mock` + `@InjectMocks`

### 6. Verify Coverage Improved

Re-run the coverage command from Step 1. Confirm:
- Line coverage >= 80%
- Branch coverage >= 75%
- No previously-covered lines regressed

## Output Format

After writing tests, provide a summary table:

```
File                    Before   After    Δ
src/pricing.py          42%      87%      +45%
src/auth/tokens.py      61%      91%      +30%
```

List any remaining uncovered branches that are intentionally excluded (dead code, platform-specific guards) with a brief justification.

## Edge Cases

**Legacy code with no tests at all**: Start with integration/smoke tests to establish a safety net before adding unit tests. Use `pytest --cov` with `--cov-fail-under=0` initially just to generate the baseline report.

**Over-mocking warning**: High coverage achieved by mocking away all real logic is misleading — tests pass because they only verify mock behavior, not the unit under test. If every meaningful call in the function is replaced by a mock return value, the coverage number is meaningless. Mock only external boundaries (HTTP, DB, filesystem); leave business logic unmocked.

**Coverage inflation via trivial tests**: Never write tests that just call a function without asserting anything meaningful. A test that passes with `assert True` harms more than it helps — reviewers should reject it.

**Async code**: Use `pytest-asyncio` with `@pytest.mark.asyncio`, or Jest's `async/await` test bodies. Ensure all async branches (resolved, rejected, timeout) are covered.
