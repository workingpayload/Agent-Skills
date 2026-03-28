---
name: inputshield
description: Implements rigorous input validation, sanitization, and encoding to prevent OWASP Top 10 vulnerabilities including XSS, SQL injection, and command injection. Use when a user needs schema validation with Zod/Joi/Pydantic, parameterized queries, CSP headers, allowlist strategies, or context-specific output encoding.
---

# InputShield

## Overview

Designs and implements a defense-in-depth input validation strategy: schema validation at the boundary (Zod/Joi/Pydantic), parameterized queries for database access, context-specific output encoding for XSS prevention, and HTTP security headers (CSP, CORS). Follows OWASP Top 10 2021 guidelines.

## Workflow

### 1. Identify All Input Surfaces

Enumerate every point where untrusted data enters the system:
- HTTP request body, query params, path params, headers, cookies
- File uploads (name, MIME type, content)
- WebSocket messages
- Environment variables read at runtime
- Data imported from external APIs or files

Mark each surface with its trust level: **untrusted** (external user), **semi-trusted** (internal service), or **trusted** (own DB read).

### 2. Validate at the Boundary — Schema First

**TypeScript (Zod):**
```typescript
import { z } from 'zod';

const CreateUserSchema = z.object({
  email: z.string().email().max(255).toLowerCase(),
  username: z.string()
    .min(3).max(30)
    .regex(/^[a-zA-Z0-9_-]+$/, 'Only alphanumeric, underscore, hyphen allowed'),
  age: z.number().int().min(13).max(120).optional(),
  role: z.enum(['viewer', 'editor', 'admin']),  // allowlist, never freeform
});

type CreateUserInput = z.infer<typeof CreateUserSchema>;

// In Express route handler:
const result = CreateUserSchema.safeParse(req.body);
if (!result.success) {
  return res.status(400).json({ errors: result.error.flatten() });
}
const data: CreateUserInput = result.data;  // type-safe from here
```

**Python (Pydantic v2):**
```python
class CreateUserRequest(BaseModel):
    email: EmailStr
    username: str
    role: Literal['viewer', 'editor', 'admin']
    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_-]{3,30}$', v): raise ValueError('Invalid format')
        return v
```

**Rules:**
- Always use **allowlists** (define what is permitted) over denylists (block known bad values).
- Validate **type → format → range → business rule** in that order.
- Reject on first failure; do not attempt to sanitize malformed input.

### 3. Prevent SQL Injection — Parameterized Queries Only

```typescript
// VULNERABLE — never do this
const query = `SELECT * FROM users WHERE email = '${email}'`;

// SAFE — parameterized (node-postgres)
const { rows } = await pool.query(
  'SELECT id, name FROM users WHERE email = $1 AND active = $2',
  [email, true]
);

// SAFE — ORM (Prisma)
const user = await prisma.user.findUnique({ where: { email } });

// SAFE — raw query with ORM escape (TypeORM)
await dataSource.query('SELECT * FROM users WHERE email = ?', [email]);
```

Never interpolate user data into SQL strings, even after regex validation.

### 4. Prevent XSS — Context-Specific Output Encoding

Different contexts require different encoding:

| Context | Encoding method |
|---|---|
| HTML body | `DOMPurify.sanitize(html)` or `escapeHtml(text)` |
| HTML attribute | `encodeURIComponent()` or template engine auto-escape |
| JavaScript string | `JSON.stringify()` — never template literal interpolation |
| CSS value | Allowlist permitted values; reject anything else |
| URL parameter | `encodeURIComponent()` |

Use `DOMPurify.sanitize(html, { ALLOWED_TAGS: ['b','i','em','strong','a'], ALLOWED_ATTR: ['href'] })` only for rich-text rendering. For plain text: use framework auto-escaping (React JSX, Jinja2). Never use `dangerouslySetInnerHTML` / `v-html` with untrusted data.

### 5. Set HTTP Security Headers

Use `helmet` (Express) with CSP directives: `defaultSrc: ["'self'"]`, `scriptSrc` with a per-request nonce, `objectSrc: ["'none'"]`, `frameAncestors: ["'none'"]`. Set `referrerPolicy: strict-origin-when-cross-origin`. Always set cookies with `httpOnly; Secure; SameSite=Strict`.

### 6. File Upload Validation

Check file signature (magic bytes) via `file-type` library — not just extension or `Content-Type`. Enforce size limits. Store outside web root; serve via signed URLs (S3, GCS):
```typescript
const detected = await fromBuffer(buffer);
const allowed = ['image/jpeg', 'image/png', 'image/webp'];
if (!detected || !allowed.includes(detected.mime)) throw new ValidationError('Not permitted');
if (buffer.length > 5 * 1024 * 1024) throw new ValidationError('Exceeds 5MB');
```

## Output Format

For each input surface, deliver:
1. Schema definition (Zod/Joi/Pydantic) with all constraints documented.
2. Integration point (where validation runs in the request lifecycle).
3. Error response format (RFC 7807 Problem Details recommended).
4. Any headers or encoding additions required.

## Edge Cases

**Open redirect via URL inputs:** Validate that redirect URLs are either relative paths or match an explicit allowlist of trusted domains. `new URL(input).hostname` must match `ALLOWED_REDIRECT_HOSTS`.

**Unicode normalization attacks:** Input like `ＳＥＬＥＣＴ` (fullwidth characters) may bypass keyword denylists. Normalize to NFKC before validation: `input.normalize('NFKC')`.

**Mass assignment / over-posting:** Use `z.pick()` or Pydantic's `model_validate(..., strict=True)`. Never spread the entire validated object into an ORM call.

**GraphQL-specific validation:** Enforce query depth limiting (reject depth > 7), complexity analysis (assign cost per field, reject above budget), and disable introspection in production. Guard against batch attacks by rate-limiting per operation name and rejecting arrays of operations exceeding a threshold.
```typescript
import depthLimit from 'graphql-depth-limit';
const schema = makeExecutableSchema({ ... });
app.use('/graphql', graphqlHTTP({
  validationRules: [depthLimit(7)],
  // disable introspection:
  // fieldResolver: (src, args, ctx, info) => { if (info.fieldName === '__schema') throw new Error('Forbidden'); }
}));
```

**SVG upload risk:** SVGs are XML that can contain embedded `<script>` tags and event handlers. Never serve user-uploaded SVGs as `image/svg+xml` without sanitization. Pipe through DOMPurify (server-side via `jsdom`) or `svg-sanitizer`, or convert to PNG/WebP via `sharp` before serving.
