---
name: accessplus
description: Designs and implements role-based access control (RBAC), fine-grained permissions, and WCAG 2.1-compliant accessibility. Use when a user needs authorization models, permission policies, ARIA markup, screen-reader support, or audit of access control logic.
---

# AccessPlus

## Domain Scope

Two distinct but related concerns:
1. **Authorization** — who can do what (RBAC, ABAC, policy engines)
2. **Accessibility** — who can perceive and operate the UI (WCAG 2.1, ARIA, keyboard nav)

---

## Workflow: Authorization (RBAC / Permissions)

### 1. Model the Permission Space
- Enumerate **subjects** (users, service accounts, API keys), **resources** (routes, data objects, UI sections), and **actions** (read, write, delete, approve).
- Choose the right model:
  - **RBAC** — roles own permissions; users own roles. Use for most SaaS apps.
  - **ABAC** — policies evaluate attributes (user.department, resource.classification). Use for data-level row security.
  - **ReBAC** — relationships define access (Google Zanzibar style). Use for social/collaborative apps.

### 2. Implement with a Policy Engine
- **Casbin**: define models in `model.conf`, policies in `policy.csv` or a DB adapter. Use `enforce(subject, object, action)` at every gate.
- **OPA (Open Policy Agent)**: write Rego policies, bundle and serve via sidecar or `opa eval`. Integrate via REST API or WASM.
- **AWS IAM / Cedar**: for cloud-native; Cedar policies are typed and formally verifiable.
- Always externalize policies from application code — no hardcoded `if role === 'admin'` blocks.

**ABAC with environmental attributes (Rego example)**:
```rego
# Allow read only during business hours from corporate IP range
allow {
    input.action == "read"
    hour := time.clock(time.now_ns())[0]
    hour >= 8; hour < 18                        # 08:00–18:00 UTC
    net.cidr_contains("10.0.0.0/8", input.ip)  # corporate network
}
```
Cedar equivalent: `when { context.hour >= 8 && context.hour < 18 && context.ip.isInRange(ip("10.0.0.0/8")) }`. Always pass `time` and `ip` as request context — never evaluate them inside the policy engine without an explicit input.

### 3. Enforce at Every Layer
- **Network/API gateway**: coarse-grained (route-level) checks via middleware (e.g., Express `rbac` middleware, FastAPI dependency injection).
- **Service layer**: business-object-level checks before mutations.
- **Database**: row-level security (PostgreSQL RLS policies) as the final safety net.
- Never rely solely on UI hiding — always enforce server-side.

**PostgreSQL RLS multi-tenant example**:
```sql
-- Set tenant context before queries (application layer)
SET app.current_tenant_id = '42';

-- Policy: users see only their tenant's rows
CREATE POLICY tenant_isolation ON orders
  USING (tenant_id = current_setting('app.current_tenant_id')::int);

ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Test: query as a restricted role
SET ROLE app_user;
SELECT * FROM orders;  -- returns only tenant 42 rows
```
Use `SET LOCAL` inside transactions to scope the setting; verify with `EXPLAIN` that the RLS filter is applied before any joins.

### 4. Audit and Test
- Log every authorization decision with: `{subject, resource, action, decision, timestamp, request_id}`.
- Write unit tests per policy rule; write integration tests for privilege escalation paths.
- Use tools: `casbin-editor` (visual policy debugger), `opa test` (Rego unit tests).

---

## Workflow: Accessibility (WCAG 2.1 / ARIA)

### 1. Audit Existing Markup
- Run automated scanners: **axe-core** (browser extension or `@axe-core/react`), **Lighthouse** accessibility audit, **Pa11y** in CI.
- Automated tools catch ~30-40% of issues. Manual testing covers the rest.

### 2. Fix by POUR Principles
**Perceivable**
- All `<img>` must have `alt` text (empty `alt=""` for decorative images).
- Color contrast ratio: ≥ 4.5:1 for normal text, ≥ 3:1 for large text (18pt+). Use `colour-contrast-checker` or Figma plugin.
- Captions for all `<video>` content.

**Operable**
- Every interactive element reachable and usable via keyboard alone (Tab, Shift+Tab, Enter, Space, arrow keys).
- No keyboard traps. Modals must trap focus internally and restore on close.
- `prefers-reduced-motion` media query: disable or reduce animations.

**Understandable**
- `<html lang="en">` set correctly. Lang attribute on mixed-language spans.
- Form inputs have associated `<label>` (not just placeholder text).
- Error messages identify the field and describe the fix.

**Robust**
- Use semantic HTML first: `<nav>`, `<main>`, `<aside>`, `<button>`, `<table>`.
- Add ARIA only when native semantics are insufficient.
- ARIA rules: `role` must be valid; `aria-labelledby` must reference an existing `id`; do not use `aria-hidden="true"` on focusable elements.

### 3. Key ARIA Patterns
```html
<!-- Live regions for dynamic content -->
<div aria-live="polite" aria-atomic="true">Status message</div>

<!-- Custom button (prefer <button> instead) -->
<div role="button" tabindex="0" aria-pressed="false">Toggle</div>

<!-- Skip link (must be first focusable element) -->
<a href="#main-content" class="skip-link">Skip to main content</a>

<!-- Dialog -->
<div role="dialog" aria-modal="true" aria-labelledby="dialog-title">
  <h2 id="dialog-title">Confirm Action</h2>
</div>
```

### 4. Screen Reader Testing
- Test with: **NVDA** + Chrome (Windows), **VoiceOver** + Safari (macOS/iOS), **TalkBack** (Android).
- Verify: heading hierarchy (`h1`→`h2`→`h3`), landmark regions, form labels, error announcements.

---

## Output Artifacts

- **Authorization**: policy file (Casbin `.conf`/`.csv` or OPA `.rego`), middleware snippet, test cases covering escalation paths, audit log schema.
- **Accessibility**: annotated diff of HTML/JSX fixes, axe-core report summary, keyboard nav checklist, WCAG 2.1 level (A/AA/AAA) compliance statement.

---

## Edge Cases

1. **Wildcard permissions and scope creep**: When a `*` action is granted, validate it cannot transitively grant higher-privilege actions (e.g., `write` on a config resource should not imply `admin`). Enumerate all resources explicitly; avoid implicit wildcards in production policies.

2. **Dynamic ARIA and SPAs**: Single-page apps mutate the DOM without page loads. Screen readers do not automatically announce DOM changes — every dynamic update must use `aria-live` regions or focus management. After route navigation, move focus to the `<h1>` or a skip target.

3. **Inherited roles and permission conflicts**: In hierarchical RBAC (e.g., `manager` inherits `employee`), a `deny` rule on the child role must not be silently overridden by an `allow` on the parent. Use explicit deny-wins semantics and test conflict resolution order in the policy engine.
