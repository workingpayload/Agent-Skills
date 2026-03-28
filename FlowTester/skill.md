---
name: flowtester
description: Writes end-to-end and integration tests using Playwright or Cypress with the Page Object Model, AAA pattern, and CI-friendly configuration. Use when a user needs help with E2E test structure, test isolation, flaky test debugging, API contract testing, or CI pipeline integration.
---

# FlowTester

## Overview

Produces production-quality integration and E2E tests using Playwright (preferred) or Cypress, structured with the Page Object Model (POM), Arrange-Act-Assert (AAA) pattern, proper test isolation, and CI pipeline hooks. Addresses flaky tests with deterministic waiting strategies.

## Workflow

### 1. Clarify Scope

Determine the test type needed:
- **E2E (browser):** Full user journey through the UI — use Playwright or Cypress.
- **Integration (API):** Cross-service contract verification — use Playwright's `request` fixture, Supertest, or Pact for consumer-driven contracts.
- **Component integration:** Isolated component with real child components — use Playwright Component Testing or Cypress Component Testing.

Identify: the user journey to test, the entry URL, required auth state, and any third-party services to stub.

### 2. Set Up Page Object Model

Create one PO class per page/feature area. POs encapsulate selectors and actions — tests contain only assertions and flow.

```typescript
// pages/LoginPage.ts
export class LoginPage {
  readonly emailInput = this.page.getByLabel('Email');
  readonly passwordInput = this.page.getByLabel('Password');
  readonly submitButton = this.page.getByRole('button', { name: 'Sign in' });
  readonly errorMessage = this.page.getByRole('alert');
  constructor(private page: Page) {}
  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }
  async goto() { await this.page.goto('/login'); }
}
```

Selector priority: `getByRole` > `getByLabel` > `getByTestId` > CSS. Never use positional selectors like `nth-child`.

### 3. Write Tests with AAA Pattern

```typescript
test('authenticates valid user → redirects to dashboard', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  // Act
  await loginPage.login('user@example.com', 'correct-password');
  // Assert
  await expect(page).toHaveURL('/dashboard');
});

test('shows error for invalid credentials', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login('user@example.com', 'wrong-password');
  await expect(loginPage.errorMessage).toContainText('Invalid email or password');
});
```

### 4. Test Isolation

- Use `test.beforeEach` to reset state, never `test.afterEach` (failures skip teardown).
- Seed DB state via API calls in `beforeEach`, not via UI interactions.
- Use Playwright's `storageState` to persist authenticated sessions across tests without re-logging in every test.

```typescript
// playwright.config.ts
export default defineConfig({
  globalSetup: './global-setup.ts',  // creates storageState file
  use: {
    storageState: 'playwright/.auth/user.json',
    baseURL: process.env.BASE_URL ?? 'http://localhost:3000',
  },
});
```

### 5. Stub External Services

Use **MSW (Mock Service Worker)** for browser-level API stubbing in component/integration tests:
```typescript
// Playwright: intercept at network level
await page.route('**/api/payments/**', route =>
  route.fulfill({ status: 200, body: JSON.stringify({ status: 'success' }) })
);
```

For Cypress: use `cy.intercept()` with `cy.fixture()` for response bodies.

### 6. Eliminate Flaky Tests

| Anti-pattern | Fix |
|---|---|
| `page.waitForTimeout(2000)` | `await expect(locator).toBeVisible()` |
| Hardcoded test IDs that change | `data-testid` attributes on stable elements |
| Shared global state between tests | `storageState` reset per test group |
| Race conditions on navigation | `await page.waitForURL('/target')` after click |
| Animation interference | `page.emulateMedia({ reducedMotion: 'reduce' })` |

### 7. CI Integration

```yaml
- run: npx playwright install --with-deps chromium
- run: npx playwright test --workers=4 --reporter=html --shard=1/4
  env: { BASE_URL: "${{ secrets.STAGING_URL }}" }
- uses: actions/upload-artifact@v4
  if: always()
  with: { name: playwright-report, path: playwright-report/ }
```

Use `--shard=N/M` across matrix jobs to parallelize large suites.

## Output Format

Deliver:
1. Page Object files in `tests/pages/`.
2. Test spec files in `tests/<feature>/`.
3. `playwright.config.ts` or `cypress.config.ts` snippet.
4. CI workflow YAML fragment.
5. Any MSW handler files if API stubbing is needed.

## Edge Cases

**Auth-protected routes:** Create a `global-setup.ts` that programmatically logs in once via the API, saves `storageState` to disk, and reuses it for all tests — avoids per-test login overhead and prevents rate-limiting.

**Dynamic data in assertions:** Never assert on data that changes between runs (e.g., `createdAt` timestamps). Assert on structure and type using regex or partial matchers: `expect(text).toMatch(/Order #\d+/)`.

**Cypress vs. Playwright for multi-tab/multi-origin:** Cypress cannot handle multiple browser tabs or cross-origin iframes in the same test. If the flow opens a new tab (e.g., OAuth popup), use Playwright's `context.waitForEvent('page')` pattern instead.

**File download assertions:**
```typescript
const [download] = await Promise.all([
  page.waitForEvent('download'),
  page.getByRole('button', { name: 'Export CSV' }).click(),
]);
expect(download.suggestedFilename()).toMatch(/^report-\d{4}\.csv$/);
const path = await download.path();
const stats = fs.statSync(path!);
expect(stats.size).toBeGreaterThan(100);  // non-empty file
```

**Shared staging DB isolation:** When parallel workers share a staging DB, namespace data per worker using unique prefixes or schemas. Wrap each test in a transaction and roll back on teardown:
```typescript
// Per-worker prefix
const prefix = `test_w${process.env.TEST_WORKER_INDEX ?? 0}_${Date.now()}`;
// Seed: createUser({ email: `${prefix}@example.com` })
// After each test: DELETE FROM ... WHERE email LIKE '${prefix}%'
// Or: wrap in a DB transaction and ROLLBACK in afterEach
```
