---
name: functionforge
description: Writes pure, testable utility functions using functional programming principles — immutability, referential transparency, Result/Either types, currying, and pipe/compose. Use when a user needs to generate or refactor functions with explicit type signatures, safe error handling, or composable data transforms.
---

# FunctionForge

## Overview

Produces pure functions with explicit type signatures, safe error-handling via Result/Either types, and composable pipelines using pipe/compose. Every function is side-effect-free, deterministic, and independently testable.

## Workflow

### 1. Write the Type Signature First

Before implementation, define the full type signature. This constrains the solution space and serves as documentation.

```typescript
// TypeScript
declare function parsePositiveInt(input: unknown): Result<number, ValidationError>
declare function formatCurrency(amount: number, locale: string): string
declare function groupBy<T, K extends string>(
  key: (item: T) => K,
  items: T[]
): Record<K, T[]>
```

### 2. Enforce Purity Constraints

A function is pure if:
- **Same inputs always produce same outputs** (no `Date.now()`, `Math.random()`, or global reads inside)
- **No observable side effects** (no mutations, no I/O, no exceptions thrown for control flow)

```typescript
// IMPURE — mutates input
function sortItems(items: Item[]): Item[] {
  return items.sort((a, b) => a.name.localeCompare(b.name)); // sort mutates in place
}

// PURE — returns new array
function sortItems(items: readonly Item[]): Item[] {
  return [...items].sort((a, b) => a.name.localeCompare(b.name));
}
```

Use `readonly` / `Readonly<T>` / `as const` in TypeScript. Use `Object.freeze()` for runtime immutability when needed.

### 3. Return Result/Either Instead of Throwing

```typescript
// Using neverthrow (TypeScript)
import { ok, err, Result } from 'neverthrow';

type ValidationError = { code: string; message: string };

function parseEmail(input: unknown): Result<string, ValidationError> {
  if (typeof input !== 'string') {
    return err({ code: 'TYPE_ERROR', message: 'Expected string' });
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input)) {
    return err({ code: 'INVALID_FORMAT', message: 'Not a valid email address' });
  }
  return ok(input.toLowerCase().trim());
}

// Caller handles both paths explicitly — no try/catch surprises
const result = parseEmail(userInput);
if (result.isOk()) {
  sendEmail(result.value);
} else {
  showError(result.error.message);
}
```

In Python: use `returns.result` `Success`/`Failure` or a simple dataclass wrapper.

### 4. Apply Currying for Partial Application

```typescript
const multiply = (factor: number) => (value: number): number => value * factor;
const double = multiply(2);
const prices = [10, 20, 30].map(double); // [20, 40, 60]
```

Curry data-last to enable point-free style with `pipe`.

### 5. Compose with pipe / compose

```typescript
import { pipe } from 'fp-ts/function';
// or: import { pipe } from 'remeda';

const processOrder = (raw: unknown) =>
  pipe(
    raw,
    validateOrder,        // unknown -> Result<RawOrder, Error>
    map(normalizeOrder),  // Result<RawOrder, Error> -> Result<Order, Error>
    map(applyDiscount(0.1)),
    map(formatForShipment)
  );
```

`pipe(value, f, g, h)` = left-to-right, readable as a data pipeline.
`compose(h, g, f)(value)` = right-to-left, mathematical composition order.

Prefer `pipe` for readability. Use `compose` only when building reusable composed functions.

### 6. Verify Referential Transparency

A function has referential transparency if replacing any call with its return value does not change program behavior. Verify by: running twice with identical inputs (results must be deeply equal), checking for hidden mutable closure state, and confirming no dependence on call order.

## Output Format

Deliver for each function: type signature, pure implementation, unit tests (happy path + error + boundary), and a `pipe`/`compose` usage example if composable.

## Edge Cases

**Async purity:** Async functions that fetch data are not pure, but can be kept referentially transparent by injecting the fetch dependency: `fetchUser(httpClient)(id)`. This keeps business logic pure and testable with a mocked client.

**null / undefined inputs:** Always guard at the boundary with a `Result`-returning parser. Never let `null` propagate into pure computation — use `Option<T>` (from `fp-ts` or `effect`) for values that may be absent.

**Recursive functions and stack overflow:** For deeply recursive operations, use trampolining or convert to iterative with an explicit stack.

**Monetary value precision:** Never use floating-point for money. Store values as integer cents (`amount: number` in whole cents), or use `big.js`/`decimal.js` (JS) or Python's `Decimal` for arbitrary precision. Example: `new Decimal('19.99').times('1.08').toFixed(2)`.

**Mixed sync/async pipe composition:** When a pipeline mixes sync and async steps, use `TaskEither` from `fp-ts` to lift sync `Either` values into the async chain, or explicitly `await` intermediate `Result` values before passing to the next pure step:
```typescript
import { pipe } from 'fp-ts/function';
import * as TE from 'fp-ts/TaskEither';
const processAsync = (raw: unknown) =>
  pipe(
    TE.fromEither(validateOrder(raw)),   // sync Either → TaskEither
    TE.chainW(order => TE.tryCatch(() => fetchPrice(order), toError)),
    TE.map(applyDiscount(0.1)),
  );
```
