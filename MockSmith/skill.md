---
name: mocksmith
description: Generates realistic, schema-driven mock data using Faker.js or factory_boy, stubs API responses with MSW, and produces edge-case datasets from OpenAPI specs or TypeScript interfaces. Use when a user needs test fixtures, factory functions, referentially consistent seed data, or browser/Node API mocking.
---

# MockSmith

## Overview

Produces deterministic, realistic mock data from OpenAPI specs or TypeScript/Python type definitions using Faker.js (JS/TS) or factory_boy (Python). Stubs HTTP APIs at the network layer using Mock Service Worker (MSW). Ensures referential integrity across related entities and covers edge-case data.

## Workflow

### 1. Derive the Schema First

Before generating any data, extract or confirm the schema from an OpenAPI spec (`components/schemas`), TypeScript interface, or user description. Never invent field names or types.

### 2. Build Factory Functions (TypeScript / Faker.js)

```typescript
// factories/user.factory.ts
import { faker } from '@faker-js/faker';

export function createUser(overrides: Partial<User> = {}): User {
  return {
    id:          faker.string.uuid(),
    email:       faker.internet.email().toLowerCase(),
    displayName: faker.person.fullName(),
    role:        faker.helpers.arrayElement(['admin', 'editor', 'viewer']),
    createdAt:   faker.date.past({ years: 2 }).toISOString(),
    isActive:    true,
    ...overrides,
  };
}

export const createUsers = (n: number, overrides: Partial<User> = {}) =>
  Array.from({ length: n }, () => createUser(overrides));
```

**Deterministic CI output:** `faker.seed(12345)` — same seed → same data every run.

**Per-worker seeding for parallel tests:** Seed with the worker ID so each worker produces unique but reproducible data:
```typescript
faker.seed((Number(process.env.TEST_WORKER_INDEX) ?? 0) * 1000);
```

### 3. Build Factory Functions (Python / factory_boy)

```python
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    id           = factory.LazyFunction(uuid.uuid4)
    email        = Faker('email')
    display_name = Faker('name')
    role         = factory.Iterator(['admin', 'editor', 'viewer'])
    is_active    = True
# Usage: UserFactory(role='admin') | UserFactory.create_batch(10, is_active=False)
```

### 4. Maintain Referential Integrity

Use sub-factories — never generate orphaned foreign keys:
```typescript
export function createOrder(overrides: Partial<Order> = {}): Order {
  const user = overrides.user ?? createUser();
  return { id: faker.string.uuid(), userId: user.id, user, status: 'pending', ...overrides };
}
```

### 5. Generate Edge-Case Data

```typescript
export const edgeCaseUsers = {
  emptyDisplayName: createUser({ displayName: '' }),
  unicodeName:      createUser({ displayName: '田中 太郎' }),
  sqlInjection:     createUser({ displayName: "'; DROP TABLE users; --" }),
  xssPayload:       createUser({ displayName: '<script>alert(1)</script>' }),
  inactiveAdmin:    createUser({ role: 'admin', isActive: false }),
};
```

### 6. Stub APIs with MSW

```typescript
// mocks/handlers.ts
export const handlers = [
  http.get('/api/users', ({ request }) => {
    const count = Number(new URL(request.url).searchParams.get('limit') ?? 10);
    return HttpResponse.json({ data: createUsers(count), total: 100 });
  }),
  http.get('/api/users/:id', ({ params }) =>
    HttpResponse.json(createUser({ id: params.id as string }))
  ),
  http.post('/api/users', async ({ request }) =>
    HttpResponse.json(createUser(await request.json() as Partial<User>), { status: 201 })
  ),
];
```

**Timeout and network error simulation:**
```typescript
import { delay } from 'msw';
http.get('/api/slow', async () => { await delay(3000); return HttpResponse.json({}); }),
http.get('/api/offline', () => HttpResponse.error()),  // simulates network failure
```

```typescript
// mocks/server.ts
export const server = setupServer(...handlers);
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

### 7. Polymorphic Schema Factories (`oneOf` / `anyOf`)

When an OpenAPI schema uses `oneOf`/`anyOf`, generate a factory per variant and a union factory:
```typescript
type Shape = Circle | Rectangle;
function createCircle(o: Partial<Circle> = {}): Circle {
  return { type: 'circle', radius: faker.number.float({ min: 1, max: 100 }), ...o };
}
function createRectangle(o: Partial<Rectangle> = {}): Rectangle {
  return { type: 'rectangle', width: faker.number.int({ min: 1, max: 200 }),
           height: faker.number.int({ min: 1, max: 200 }), ...o };
}
const createShape = (): Shape =>
  faker.helpers.arrayElement([createCircle, createRectangle])();
```

### 8. Generate from OpenAPI Spec

Parse `components/schemas`. Map types: `string/email` → `faker.internet.email()`, `string/uuid` → `faker.string.uuid()`, `string/date-time` → `faker.date.recent().toISOString()`. Respect `minimum`, `maximum`, `minLength`, `maxLength`, `enum`, `pattern`. Generate one factory per schema object.

## Output Format

Deliver: factory files in `tests/factories/`, MSW `mocks/handlers.ts` and `mocks/server.ts`, edge-case fixtures export, and Vitest/Jest setup snippet.

## Edge Cases

**Circular references:** Break cycles with a depth guard: `manager: depth < 2 ? createUser({}, depth + 1) : null`.

**Date consistency:** Generate `createdAt` first, then `updatedAt = faker.date.between({ from: createdAt, to: new Date() })`.

**MSW in SSR / Next.js:** Use `msw/node` `setupServer` for API route tests and `msw/browser` `setupWorker` for client-side tests. Share handler definitions in a single `handlers.ts`.
