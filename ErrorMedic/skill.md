---
name: errormedic
description: Diagnoses application errors by parsing stack traces, classifying error taxonomy, correlating source maps, verifying fixes, and connecting to Sentry/Datadog alerts. Use when a user shares an error, exception, stack trace, or crash log and needs it diagnosed and fixed.
---

# ErrorMedic

## Overview

Turn a cryptic error into a root cause and a verified fix. Follow a systematic triage: read the stack trace bottom-up, classify the error type, locate the exact source line, hypothesize cause, apply fix, verify the fix eliminates the error.

## Workflow

### 1. Parse the Stack Trace

**Read from the bottom up.** The bottom frames show where execution started; the top frame shows where it crashed.

Anatomy of a stack trace:
```
Error: Cannot read properties of undefined (reading 'email')  ← Error type + message
    at getUserEmail (src/auth/user.ts:42:18)                  ← Top frame = crash site
    at validateSession (src/middleware/auth.ts:17:5)           ← Caller
    at Layer.handle [as handle_request] (express/lib/router/layer.js:95:5)  ← Framework
    at next (express/lib/router/route.js:137:13)
    at Route.dispatch (express/lib/router/route.js:112:3)
```

Extract:
- **Error class**: `TypeError`, `ValueError`, `NullPointerException`, `KeyError`, etc.
- **Error message**: exact text
- **Top application frame**: first non-framework file in the trace (here: `src/auth/user.ts:42`)
- **Call chain**: sequence of application frames (ignore node_modules / stdlib)

### 2. Classify the Error

| Class | Symptoms | Common Causes |
|-------|----------|---------------|
| `NullPointerException` / `TypeError: Cannot read ... of undefined` | Accessing property on null/undefined | Missing null guard, optional chain needed, async race |
| `KeyError` / `AttributeError` | Key or attribute doesn't exist | Wrong key name, missing default, schema mismatch |
| `ValueError` / `IllegalArgumentException` | Input validation failure | Incorrect type passed, out-of-range value |
| `ECONNREFUSED` / `ConnectionRefusedError` | TCP connection rejected | Service not running, wrong port, firewall |
| `ETIMEDOUT` / `ReadTimeoutError` | No response within deadline | Slow query, deadlock, downstream outage |
| `ENOENT` / `FileNotFoundError` | File doesn't exist | Wrong path, missing file, env-specific path |
| `SyntaxError` | Parse failure | Malformed JSON/YAML, encoding issue |
| `MemoryError` / `OOM` | Process killed | Memory leak, unbounded collection growth |
| `IntegrityError` / `UniqueViolation` | DB constraint violation | Duplicate insert, FK violation, race condition |
| `UnicodeDecodeError` | Encoding mismatch | File read with wrong codec (e.g., Shift-JIS read as UTF-8) |

**Encoding errors**: `UnicodeDecodeError: 'utf-8' codec can't decode byte 0x83` means the file is not UTF-8. Detect the encoding first: `chardet.detect(raw_bytes)` (Python) or `charset-normalizer`. Common culprits: Windows-1252, Shift-JIS (Japanese), Latin-1. Fix: `open(path, encoding='shift_jis')` or `errors='replace'` to substitute undecodable bytes with `?`.

### 3. Resolve Source Maps (for Minified/Compiled Code)

**JavaScript (Browser or Node.js):**
```bash
# Using source-map CLI
npx source-map resolve dist/bundle.js.map 42 18
# Returns: src/auth/user.ts:142:8

# Or in Node.js at runtime:
import sourceMapSupport from 'source-map-support';
sourceMapSupport.install();
# Stack traces now show original TypeScript files automatically
```

**Java (obfuscated with ProGuard):**
```bash
retrace.sh proguard-mapping.txt obfuscated-stacktrace.txt
```

**Python (Cython or compiled):** Use `.pdb` files or ensure `-g` debug flags are present during compilation.

### 4. Hypothesize Root Cause

Ask these questions in order:
1. **What value is null/undefined/missing?** Read the crash-site line. What variable is being accessed?
2. **Who provides that value?** Trace up the call chain — which function should have provided it?
3. **Under what condition does it become null?** Is it an async race? A missing DB record? An empty API response?
4. **Is this a bug or a missing guard?** A bug means the data is wrong upstream; a missing guard means the code doesn't handle a valid null case.

Example diagnosis:
```
Error: Cannot read properties of undefined (reading 'email')
at getUserEmail (src/auth/user.ts:42:18)

Line 42: return user.profile.email;
→ user.profile is undefined
→ Looking up: user = await db.users.findOne({ id: session.userId })
→ Returns null if user deleted, but caller didn't handle null
→ Root cause: deleted user's session still valid; code doesn't handle missing user
```

### 5. Apply and Verify the Fix

**Write the fix:**
```typescript
// Before
async function getUserEmail(userId: string): Promise<string> {
    const user = await db.users.findOne({ id: userId });
    return user.profile.email;  // crashes if user is null
}

// After
async function getUserEmail(userId: string): Promise<string> {
    const user = await db.users.findOne({ id: userId });
    if (!user) {
        throw new NotFoundError(`User ${userId} not found`);
    }
    if (!user.profile?.email) {
        throw new DataIntegrityError(`User ${userId} has no email on profile`);
    }
    return user.profile.email;
}
```

**Verify the fix:**
1. Write a test that reproduces the original error condition
2. Confirm the test fails before the fix
3. Apply the fix
4. Confirm the test passes after the fix
5. Check that no existing tests regressed

```python
def test_get_user_email_raises_when_user_deleted():
    # Arrange: deleted user with valid session
    db.users.delete(user_id=42)

    # Act + Assert
    with pytest.raises(NotFoundError, match="User 42 not found"):
        get_user_email(42)
```

### 6. Connect to Observability Tools

**Sentry**: Use `scope.set_user()`, `scope.set_tag()`, `scope.set_context()` before `capture_exception()` to attach request context to the error event.

**Datadog**: Decorate with `@tracer.wrap(service=..., resource=...)` and call `span.set_tag("order.id", ...)` for trace correlation. Query: `status:error service:payments @error.type:TypeError`.

## Output Format

For each error: **Error** (class + message) → **Location** (file:line) → **Root Cause** (one paragraph) → **Fix** (before/after code) → **Verification** (test that reproduces then passes) → **Prevention** (pattern to avoid recurrence).

## Edge Cases

**Async errors without stack traces**: In Node.js, `Promise` rejections without `await` lose their stack. Enable `--async-stack-traces` (Node.js >= 12) or use `longjohn` in development. Always `return` promises — never fire-and-forget without a `.catch()`.

**Error swallowing in catch blocks**: `catch (e) {}` or `catch (e) { console.log(e) }` hides the original cause. When fixing, always re-throw or log with full context: `logger.error('Payment failed', { error: e, orderId })`.

**Transient vs persistent errors**: Network timeouts and rate limits are transient — the fix is a retry with exponential backoff. Logic errors and constraint violations are persistent — retrying makes them worse. Classify before choosing the fix strategy.

**Race condition fixes**: `IntegrityError: UniqueViolation` on concurrent inserts means two processes checked "does it exist?" simultaneously and both inserted. Fix options: (1) `INSERT ... ON CONFLICT DO NOTHING` / `ON CONFLICT DO UPDATE` (upsert); (2) `SELECT FOR UPDATE` to lock the row before deciding; (3) idempotency keys — accept a client-generated UUID and deduplicate on it. Choose based on whether the duplicate is an error or a retry.

**Source map fallback**: If source maps aren't deployed, the minified stack trace is the only artifact. Immediate steps: (1) set up source map upload in your CI pipeline (Sentry `sentry-cli sourcemaps upload`, Datadog `datadog-ci sourcemaps upload`); (2) for the current incident, manually unminify using `source-map` CLI with the build artifact if available locally; (3) add column numbers to error logging to enable post-hoc mapping once maps are uploaded.
