---
name: testcrafter
description: Writes unit and integration tests using Jest, Vitest, Pytest, or JUnit following the AAA pattern and test pyramid principles. Use when asked to write tests, improve test coverage, set up a testing strategy, configure CI test gates, or decide between mocking vs. real implementations.
---

# TestCrafter

## Overview

Produces high-quality, maintainable tests following the AAA (Arrange-Act-Assert) pattern, test pyramid principles, and clear naming conventions. Framework-specific guidance for Jest/Vitest (JavaScript/TypeScript), Pytest (Python), and JUnit 5 (Java). Targets 80% line coverage as a floor, with emphasis on testing behavior over implementation.

## Workflow

### 1. Test Pyramid Strategy

Before writing tests, identify the appropriate layer:

```
        /\
       /E2E\          ~5% — Playwright/Cypress/Selenium; slow, costly, high confidence
      /------\
     /Integr. \       ~20% — DB, HTTP, message queue integration; real dependencies
    /----------\
   /  Unit Tests \    ~75% — Pure logic, isolated, fast (< 10ms each)
  /--------------\
```

**Unit tests**: Test one function/class in isolation. Mock all external dependencies (DB, HTTP, filesystem, time). Goal: < 10ms per test, no I/O.

**Integration tests**: Test the interaction between components (e.g., repository + real DB, HTTP handler + real router). Use test containers (Testcontainers library) or an in-memory DB (SQLite for PostgreSQL compatibility testing, `mongomock` for MongoDB).

**E2E tests**: Test the full user journey through the real UI. Reserve for critical paths only (login, checkout, core workflow). Do not write E2E tests for every feature.

### 2. Naming Convention

Use the **"should [expected behavior] when [condition]"** pattern:

```javascript
// Good
describe('UserService', () => {
  describe('createUser', () => {
    it('should return the created user with an assigned ID when valid data is provided')
    it('should throw ValidationError when email is already taken')
    it('should hash the password before persisting to the database')
  })
})
```

```python
# Pytest: use descriptive function names
def test_create_user_returns_user_with_id_when_valid_data():
def test_create_user_raises_validation_error_when_email_taken():
def test_create_user_hashes_password_before_persisting():
```

Avoid: `test1`, `testHappyPath`, `test_create_user_works`. The test name should be self-documenting enough to diagnose a failure without reading the test body.

### 3. AAA Pattern Implementation

Every test has exactly three sections: Arrange, Act, Assert.

**Jest/Vitest (TypeScript)** — mock the repo, call the service, assert the result:
```typescript
it('should return created user with ID when valid data is provided', async () => {
  // Arrange
  mockUserRepo.findByEmail.mockResolvedValue(null);
  mockUserRepo.save.mockResolvedValue({ id: 'uuid-123', email: 'user@example.com' });
  // Act
  const result = await userService.createUser({ email: 'user@example.com', password: 'secret' });
  // Assert
  expect(result.id).toBe('uuid-123');
  expect(mockUserRepo.save).toHaveBeenCalledOnce();
});
```

**Pytest**:
```python
def test_returns_user_with_id_when_valid_data(self):
    self.mock_repo.find_by_email.return_value = None
    self.mock_repo.save.return_value = {"id": "uuid-123", "email": "u@example.com"}
    result = self.service.create_user(email="u@example.com", password="secret")
    assert result["id"] == "uuid-123"
    self.mock_repo.save.assert_called_once()

def test_raises_validation_error_when_email_taken(self):
    self.mock_repo.find_by_email.return_value = {"id": "existing"}
    with pytest.raises(ValidationError, match="Email already in use"):
        self.service.create_user(email="u@example.com", password="secret")
```

### 4. Mock vs. Real Dependencies

**Mock** when the dependency has slow I/O, non-deterministic behavior, or you need to force specific error paths. Always mock in unit tests.

**Use real implementations** when testing the integration itself (repository + DB). Use Testcontainers (`PostgreSqlContainer`, `@testcontainers/postgresql`) for integration tests — spin up a real DB in `beforeAll`, run migrations, then tear down in `afterAll`.

**Avoid partial mocks** — they couple tests to implementation and hide bugs.

### 5. Framework-Specific Configuration

**Vitest** (`vitest.config.ts`):
```typescript
export default defineConfig({
  test: {
    globals: true, environment: 'node',
    coverage: {
      provider: 'v8', reporter: ['text', 'lcov'],
      thresholds: { lines: 80, functions: 80, branches: 75 },
      exclude: ['**/*.config.*', '**/migrations/**'],
    },
  },
});
```

**Pytest** (`pyproject.toml`):
```toml
[tool.pytest.ini_options]
addopts = "--cov=app --cov-report=term-missing --cov-fail-under=80"
```

**JUnit 5**: configure Jacoco with `<minimum>0.80</minimum>` on `LINE` counter.

### 6. Coverage Strategy

80% line coverage is a floor. Priorities: (1) 100% on domain logic and calculation functions; (2) every `catch` block and error path; (3) boundary conditions (empty, null, min/max). Exclude `toString()`, getters/setters, and generated code. Use `vitest --coverage` for branch coverage; `--cov-report=term-missing` in Pytest.

### 7. CI Integration

```yaml
- name: Run tests with coverage
  run: npx vitest run --coverage
- name: Upload coverage
  uses: codecov/codecov-action@v4
  with: { token: "${{ secrets.CODECOV_TOKEN }}", fail_ci_if_error: true }
```

Block PRs on test failures and coverage drops > 2% from main baseline.

## Additional Patterns

**WebSocket testing:** Mock the `WebSocket` constructor in unit tests to avoid real connections:
```typescript
const mockWs = { send: vi.fn(), close: vi.fn(), onmessage: null, onopen: null };
vi.stubGlobal('WebSocket', vi.fn(() => mockWs));
// Simulate incoming message
mockWs.onmessage?.({ data: JSON.stringify({ type: 'update', payload: 42 }) });
```
For integration tests, use a real `ws` server spun up in `beforeAll` on a random port.

**Large parameterized test performance:** When `pytest.mark.parametrize` produces thousands of cases (e.g., fuzzing inputs), test runs can take minutes. Apply stratified sampling: group inputs by equivalence class and pick one representative per class. For CI speed, split the full suite across workers with `pytest-xdist` (`pytest -n auto`), and run the full set only on main branch merges.

## Edge Cases

**Testing async code and timers**: Use `vi.useFakeTimers()` (Vitest) or `pytest-asyncio` + `asyncio.sleep` mocking to control time in tests. Never use `setTimeout(fn, 0)` or `asyncio.sleep(0.1)` in tests — they create flaky tests dependent on real time. Use `vi.advanceTimersByTime(5000)` to simulate time passage deterministically.

**Testing code with global state / singletons**: Reset global state in `beforeEach`/`afterEach`. For module-level singletons in Node.js, use `vi.resetModules()` to get a fresh module instance per test. For Python, use `importlib.reload()` or redesign the singleton to accept injected dependencies (constructor injection is inherently more testable).

**Snapshot tests**: Use Jest/Vitest snapshot tests sparingly — only for stable serialized output (serialized ASTs, rendered static HTML). Never snapshot for UI components that change frequently; use explicit assertions instead. Stale snapshots silently pass until someone runs `--updateSnapshot`, masking regressions. If a snapshot test fails unexpectedly, treat it as a regression, not an automatic update.
