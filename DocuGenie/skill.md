---
name: docugenie
description: Writes OpenAPI 3.x specs, JSDoc/TSDoc/Google-style docstrings, and developer guides with working code examples. Use when a user asks to document an API, write docstrings, generate a README, or create a developer guide.
---

# DocuGenie

## Overview

Generate documentation that developers actually use: accurate OpenAPI specs, docstrings that IDEs render, and guides with copy-paste-ready examples. Documentation must match the code — never invent behavior.

## Workflow

### 1. Identify What Needs Documenting

Determine the output type:
- **REST API** → OpenAPI 3.x YAML/JSON spec
- **Function/class/module** → Language-appropriate docstrings
- **SDK or library** → Developer guide with quickstart + reference
- **Internal system** → Architecture doc (ADR or C4-level description)

Read the actual source code before writing anything. Never document assumed behavior.

### 2. Write OpenAPI 3.x Specs

Every endpoint needs: summary, description, parameters, request body schema, and all response schemas including error cases.

```yaml
openapi: "3.1.0"
info:
  title: Payments API
  version: "2.0.0"
paths:
  /payments:
    post:
      operationId: createPayment
      summary: Create a payment
      description: Returns immediately with `pending` status. Listen to `payment.succeeded` webhook for confirmation.
      tags: [Payments]
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/CreatePaymentRequest' }
      responses:
        "201":
          content:
            application/json:
              schema: { $ref: '#/components/schemas/Payment' }
        "400": { description: Invalid request body }
        "422": { description: Payment method declined }
components:
  schemas:
    CreatePaymentRequest:
      type: object
      required: [amount_cents, currency, payment_method_id]
      properties:
        amount_cents: { type: integer, minimum: 1, description: "Cents (e.g. 4999 = $49.99)" }
        currency: { type: string, pattern: "^[A-Z]{3}$", description: ISO 4217 }
```

Always define reusable schemas in `components/schemas`. Use `$ref` to avoid repetition. Document every error status code the code actually returns.

**Content negotiation**: When the same endpoint returns multiple formats, list each under `content` separately:
```yaml
responses:
  "200":
    content:
      application/json:
        schema: { $ref: '#/components/schemas/Payment' }
      text/csv:
        schema: { type: string }
```

**API versioning**: Prefer separate spec files per major version (`openapi-v1.yaml`, `openapi-v2.yaml`) over embedding version in `info.version` alone — separate files enable per-version tooling, linting, and SDK generation without cross-version pollution.

### 3. Write Language-Appropriate Docstrings

**Python (Google style):**
```python
def calculate_discount(
    user: User,
    cart_total: float,
    coupon_code: str | None = None,
) -> float:
    """Calculate the discount amount for a user's cart.

    Applies tier-based discounts first, then coupon discounts additively.
    The total discount is capped at 50% of cart_total.

    Args:
        user: The authenticated user. Must have a valid `tier` attribute.
        cart_total: Pre-tax cart value in dollars. Must be >= 0.
        coupon_code: Optional promotional code. Invalid codes are silently
            ignored — no exception is raised.

    Returns:
        The discount amount in dollars, rounded to 2 decimal places.
        Returns 0.0 if no discount applies.

    Side Effects:
        Increments the coupon redemption counter in the database if coupon_code is valid.
        Emits a `discount_applied` analytics event.

    Raises:
        ValueError: If cart_total is negative.
        DatabaseError: If the coupon lookup fails due to a connection error.

    Example:
        >>> user = User(tier="gold")
        >>> calculate_discount(user, 100.0, coupon_code="SAVE10")
        25.0  # 15% gold tier + 10% coupon
    """
```

**TypeScript (TSDoc)**: Use `@param`, `@returns`, `@throws {@link ErrorType}`, and `@example` tags. Document each pagination/filter option individually. Ensure `@throws` lists every error the implementation can raise, not just the happy path.

### 4. Write a Developer Guide

Structure: What it does → Prerequisites (exact versions) → Installation (copy-paste) → Quickstart (minimal working example) → Core concepts → Common recipes (top 3-5) → Configuration reference table → Troubleshooting (top 3 errors with cause + fix).

### 5. Validate the Documentation

Run `redoc-cli lint openapi.yaml` or `swagger-parser` to validate the spec. Run all code examples against the current codebase. Confirm every parameter, return type, and error code in docstrings matches the implementation.

## Output Format

- OpenAPI: valid YAML in a fenced code block, ready to paste into a file
- Docstrings: inserted directly into the function/class, preserving existing code
- Developer guides: Markdown, with working code blocks and a clear header hierarchy

## Edge Cases

**Undocumented error paths**: When the code raises errors not yet documented, list them in the docstring and add a corresponding `4xx`/`5xx` response to the OpenAPI spec. Do not silently omit them.

**Overloaded functions/polymorphic endpoints**: Document each distinct call signature separately using `@overload` in Python (with `typing`) or separate `operationId` paths in OpenAPI. Combining them into one vague description creates confusion.

**Deprecated APIs**: Mark with `@deprecated` in JSDoc/TSDoc, `deprecated: true` in OpenAPI, and include the replacement: "Deprecated since v2.3. Use `createPaymentV2` instead."
