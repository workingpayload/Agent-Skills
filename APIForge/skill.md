---
name: apiforge
description: Designs production-grade REST and GraphQL APIs including OpenAPI 3.x specs, versioning strategy, RFC 7807 error formats, cursor/offset pagination, and authentication schemes. Use when a user needs to create, review, or improve an API contract, endpoint design, or API documentation.
---

# APIForge

## Domain Scope

REST API design, GraphQL schema design, OpenAPI 3.x specification authoring, API versioning, error response standardization, pagination patterns, rate limiting, and API authentication/authorization schemes.

---

## Workflow

### 1. Gather Requirements
Ask or infer:
- Protocol: REST, GraphQL, gRPC, or mixed?
- Consumer type: public third-party, internal microservice, mobile client, or browser SPA?
- Auth requirements: public, API key, OAuth 2.0, mTLS?
- Scale/rate limit targets (requests/sec, payload sizes)?
- Breaking-change tolerance (versioning constraints)?

### 2. REST API Design

**Resource Naming**
- Use plural nouns: `/users`, `/orders`, `/products/{id}/variants`
- No verbs in paths: use HTTP method semantics
- Hierarchy: max 2-3 levels deep. Avoid `/users/{id}/orders/{orderId}/items/{itemId}/reviews`

**HTTP Method Semantics**
| Method | Use | Idempotent | Safe |
|--------|-----|-----------|------|
| GET | Retrieve | Yes | Yes |
| POST | Create / non-idempotent action | No | No |
| PUT | Full replace | Yes | No |
| PATCH | Partial update (JSON Merge Patch RFC 7396 or JSON Patch RFC 6902) | No | No |
| DELETE | Remove | Yes | No |

**Status Codes — use precisely**
- `200 OK`, `201 Created` (with `Location` header), `204 No Content`
- `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict`, `422 Unprocessable Entity`
- `429 Too Many Requests` (with `Retry-After` header), `500 Internal Server Error`

**Error Format — RFC 7807 Problem Details**
```json
{
  "type": "https://api.example.com/errors/validation-failed",
  "title": "Validation Failed",
  "status": 422,
  "detail": "The 'email' field must be a valid email address.",
  "instance": "/users",
  "errors": [
    { "field": "email", "code": "INVALID_FORMAT", "message": "Not a valid email" }
  ]
}
```
Content-Type: `application/problem+json`

**Pagination**
- **Offset/limit** (simple, supports random access): `?offset=40&limit=20`. Return total count in `X-Total-Count` header or `meta.total` body field.
- **Cursor-based** (stable with real-time data, no skipped/duplicated rows): `?cursor=<opaque_token>&limit=20`. Return `next_cursor` and `prev_cursor` in response. Cursor encodes sort field value + ID.
- Default `limit` to 20, cap at 100. Document defaults in OpenAPI spec.

**Versioning Strategy**
- **URL path versioning** (`/v1/users`) — most visible, easiest to route and cache. Recommended for public APIs.
- **Header versioning** (`Accept: application/vnd.api+json;version=2`) — cleaner URLs but harder to test in a browser.
- Maintain N-1 versions. Deprecation: add `Deprecation` and `Sunset` response headers (RFC 8594).
- Never make breaking changes within a version: adding fields is non-breaking; removing or renaming fields is breaking.

### 3. File Uploads
- Use `multipart/form-data` for simple uploads. Set `Content-Type: multipart/form-data; boundary=...` and include metadata fields alongside the file part.
- **Chunked transfer**: for large files, use `Transfer-Encoding: chunked` or split into fixed-size parts with a `Content-Range` header and a server-side assembly step.
- **TUS resumable uploads** (recommended for >10 MB): client creates an upload resource (`POST`), then sends chunks (`PATCH`) with `Upload-Offset` header. On resume, client fetches current offset (`HEAD`) and continues from there. Use the `tus-js-client` library or the Uppy uploader on the frontend.
- Cap upload size at the gateway (e.g., nginx `client_max_body_size`). Scan files for malware before processing. Store to object storage (S3/GCS), not the local filesystem.

**Sparse Fieldsets / Field Selection**
- REST: support `?fields[]=id&fields[]=name` or `?fields=id,name` to let clients request only the fields they need. Reduces payload size and prevents over-fetching.
- Alternatively, use `Prefer: return=minimal` (RFC 7240) to return `204 No Content` instead of the full resource on mutations.
- Document supported fields in OpenAPI using `example` annotations; reject unknown field names with `400`.

### 4. GraphQL Schema Design
- Use a **schema-first** approach: define SDL (`.graphql` files), then generate resolvers.
- Separate **Queries** (reads), **Mutations** (writes), **Subscriptions** (real-time).
- Use **input types** for mutations: `input CreateUserInput { ... }` not inline args.
- Avoid N+1 queries: use **DataLoader** pattern to batch and cache field-level data fetches.
- Implement **cursor-based connections** per Relay specification for lists.
- Expose `__typename` and design for **client-driven field selection** — do not over-fetch on the server side.
- Rate limit by **query complexity** (assign cost to fields) and **depth** (max 5-7 levels).

### 4. OpenAPI 3.x Specification
Structure:
```yaml
openapi: "3.1.0"
info:
  title: My API
  version: "1.0.0"
  contact: { email: "api@example.com" }
servers:
  - url: https://api.example.com/v1
paths:
  /users:
    get:
      summary: List users
      operationId: listUsers
      parameters:
        - $ref: '#/components/parameters/LimitParam'
        - $ref: '#/components/parameters/CursorParam'
      responses:
        '200':
          description: Paginated user list
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserListResponse'
        '422':
          $ref: '#/components/responses/ValidationError'
components:
  schemas: { ... }
  parameters: { ... }
  responses: { ... }
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```
- Use `$ref` to avoid duplication.
- Every `operationId` must be unique and camelCase.
- Validate spec with `redocly lint` or `spectral lint`.

### 5. Authentication Schemes
- **API keys**: pass in `Authorization: ApiKey <key>` header (not query string — query strings appear in logs).
- **OAuth 2.0**: use Authorization Code + PKCE for user-delegated access; Client Credentials for machine-to-machine.
- **JWT**: validate `iss`, `aud`, `exp`, `nbf` on every request. Use RS256 or ES256 (asymmetric). Publish JWKS endpoint.
- Document security requirements per-operation in OpenAPI `security` field.

### 6. Rate Limiting and Headers
Return on every response:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 943
X-RateLimit-Reset: 1711584000
Retry-After: 60  (on 429 only)
```

---

## Output Artifacts

- OpenAPI 3.x YAML/JSON spec (linted, with all `$ref` components defined)
- Endpoint table: method, path, auth, description, request/response schema summary
- Error catalog: all possible `type` URIs with descriptions
- Pagination contract: example request/response pair for both offset and cursor modes
- Versioning policy statement

---

## Edge Cases

1. **Partial success in batch operations**: When an endpoint accepts an array of items (e.g., bulk create), some may succeed and some fail. Return `207 Multi-Status` with a per-item result array — never return `200` if any item failed, and never return `400` if any item succeeded. Each item result includes its own `status` code and optional `problem+json` detail.

2. **Idempotency for POST requests**: Clients may retry on network timeout, causing duplicate creates. Support `Idempotency-Key` header (UUID v4, client-generated). Cache the first response keyed by `{client_id}:{idempotency_key}` for 24 hours. Return the cached response on replay without re-executing the mutation.

3. **Breaking vs. non-breaking changes in GraphQL**: Adding a field is safe. Making a non-null field nullable is safe. Making a nullable field non-null is breaking (clients not sending the field will fail). Removing a field or changing a type is breaking. Use the `@deprecated(reason: "...")` directive with a migration timeline before removal; use a schema changelog tool like `graphql-inspector diff` in CI to catch accidental breaking changes.
