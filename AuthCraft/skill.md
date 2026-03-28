---
name: authcraft
description: Builds secure authentication and authorization systems covering OAuth 2.0/PKCE, JWT lifecycle management, password hashing with bcrypt/Argon2, session security, and OWASP ASVS compliance. Use when a user needs to implement login flows, token management, MFA, SSO, or audit an existing auth system for vulnerabilities.
---

# AuthCraft

## Domain Scope

Authentication (identity verification), authorization (access control), session management, token lifecycle, multi-factor authentication (MFA), SSO/federation, and secure credential storage. Governed by OWASP ASVS Level 2 as the baseline standard.

---

## Workflow

### 1. Classify the Auth Requirement
- **User authentication**: password + MFA, social login (OAuth), magic link, passkeys (WebAuthn)
- **Machine-to-machine**: Client Credentials grant, API keys, mTLS
- **Delegated access** (user grants app access to another service): OAuth 2.0 Authorization Code + PKCE
- **SSO/federation**: SAML 2.0 (enterprise), OIDC (modern web/mobile)
- **Re-authentication**: step-up auth for sensitive operations (payment, settings change)

### 2. OAuth 2.0 and OIDC Implementation

**Authorization Code + PKCE** (for all public clients: SPAs, mobile apps):
```
1. Client generates code_verifier (43-128 random bytes, base64url encoded)
2. Client computes code_challenge = BASE64URL(SHA256(code_verifier))
3. Auth request: GET /authorize?response_type=code
                             &client_id=...
                             &redirect_uri=...
                             &code_challenge=...
                             &code_challenge_method=S256
                             &state=<random_csrf_token>
                             &scope=openid profile email
4. Exchange: POST /token with code + code_verifier (no client_secret for public clients)
5. Validate state param to prevent CSRF
```

**Token Validation** (JWT, every request):
- Verify signature against JWKS endpoint (cache keys, refresh on `kid` miss).
- Check `iss` (matches your auth server), `aud` (matches your API), `exp` (not expired), `nbf` (not before).
- Check `jti` against revocation list for sensitive tokens.
- Use RS256 or ES256 — never HS256 in distributed systems (shared secret is a risk).

**Refresh Token Rotation**:
- Issue a new refresh token on every use; invalidate the old one.
- If an old refresh token is presented (replay attack), invalidate the entire token family.
- Refresh token TTL: 30 days (sliding); access token TTL: 15 minutes maximum.
- Store refresh tokens hashed (SHA-256) in the database — treat like passwords.

### 3. Password Storage
Never store plaintext or reversible-encryption passwords.

**Argon2id** (preferred, winner of Password Hashing Competition):
```python
# Using argon2-cffi
from argon2 import PasswordHasher
ph = PasswordHasher(
    time_cost=3,       # iterations
    memory_cost=65536, # 64 MB
    parallelism=4,
    hash_len=32,
    salt_len=16
)
hash = ph.hash(password)
ph.verify(hash, input_password)  # raises VerifyMismatchError on failure
```

**bcrypt** (widely supported fallback):
- Work factor: minimum 12 (2024 guidance). Rehash on successful login if work factor is below current minimum.
- Input limit: 72 bytes — prehash with SHA-256 if passwords may exceed this: `bcrypt(base64(sha256(password)))`.

**Never use**: MD5, SHA-1, SHA-256 alone (without key stretching), unsalted hashes.

### 4. Session Security
- Server-side sessions (preferred over pure JWT for web apps requiring revocation):
  - Session ID: minimum 128 bits of entropy, cryptographically random (use `secrets.token_urlsafe(32)` in Python, `crypto.randomBytes(32)` in Node).
  - Store: Redis with TTL, or encrypted DB sessions.
  - Cookie attributes: `Secure; HttpOnly; SameSite=Lax` (or `Strict` for pure same-origin). Set `Path=/`.
  - Rotate session ID on privilege change (login, role elevation) to prevent session fixation.
- Session TTL: idle timeout (15-30 min for sensitive apps) + absolute timeout (8-24h).
- On logout: invalidate server-side session AND clear cookie. Do not rely solely on cookie deletion.

### 5. Multi-Factor Authentication (MFA)
**TOTP (RFC 6238)** — Google Authenticator, Authy:
- Use `pyotp` (Python) or `otplib` (Node). 30-second window, allow 1 step of clock drift (90-second valid window total).
- Store TOTP secret encrypted at rest (AES-256-GCM with a KMS-managed key).
- Provide backup codes (8-10 codes, single-use, bcrypt-hashed in DB).

**WebAuthn/Passkeys** (strongest, phishing-resistant):
- Use `@simplewebauthn/server` (Node) or `webauthn4j` (Java).
- Verify `rpId`, `origin`, and `challenge` on every assertion.
- Store `credentialPublicKey` and `counter`; reject if counter does not increment (cloned authenticator detection).

**SMS OTP**: acceptable for low-risk apps; vulnerable to SIM swap. Do not use for high-value accounts.

### 6. Token Exchange — RFC 8693 (On-Behalf-Of)
Used for service-to-service identity propagation: Service A receives a user token and needs to call Service B while preserving the user's identity.
```
POST /token
grant_type=urn:ietf:params:oauth:grant-type:token-exchange
subject_token=<user_access_token>
subject_token_type=urn:ietf:params:oauth:token-type:access_token
audience=service-b
requested_token_type=urn:ietf:params:oauth:token-type:access_token
```
The authorization server issues a new token scoped to Service B but with the original user's claims. Service B can then verify the `act` (actor) claim to see that Service A made the call. Never forward the user's original token to downstream services — always exchange it so each hop has a narrowly scoped token.

### 7. Passkey Credential Lifecycle
- **List**: expose `GET /auth/passkeys` returning credential IDs with labels and last-used timestamps.
- **Label**: allow users to rename credentials (e.g., "MacBook Touch ID") via `PATCH /auth/passkeys/{id}`.
- **Revoke**: `DELETE /auth/passkeys/{id}` removes the credential from the server; the authenticator cannot be used again. Require re-authentication (step-up) before revocation.
- **Recovery when all passkeys are lost**: provide a fallback (backup codes, email OTP) registered at enrollment. Do not allow account recovery that bypasses MFA entirely. After recovery, prompt user to register a new passkey immediately.

### 8. OWASP ASVS Level 2 Checklist
Key controls to verify:
- [ ] V2.1: Passwords ≥ 12 chars; checked against HaveIBeenPwned API (k-anonymity model) or a local breached password list
- [ ] V2.3: Account lockout after 5 failed attempts with exponential backoff (not hard lockout — use token bucket to prevent DoS via lockout)
- [ ] V3.3: Session invalidated after logout and on absolute timeout
- [ ] V3.7: Re-authentication required before changing email, password, or payment method
- [ ] V6.2: All secrets stored encrypted at rest; no hardcoded credentials in source
- [ ] V8.3: Sensitive data not logged (passwords, tokens, PII)
- [ ] V9.1: TLS 1.2 minimum on all auth endpoints; HSTS enforced

---

## Output Artifacts

- Auth flow sequence diagram (Mermaid) showing happy path + token refresh + logout
- Code snippets: token issuance, validation middleware, password hash/verify
- ASVS compliance checklist (checkboxes with current pass/fail status)
- Secret storage schema: which fields are hashed vs. encrypted, key management approach
- Session configuration: cookie settings, TTLs, rotation policy

---

## Edge Cases

1. **JWT revocation without a denylist**: JWTs are stateless — a signed token is valid until expiry even after logout. Solutions: (a) keep access tokens short-lived (≤15 min) and accept the revocation window, (b) maintain a Redis-backed `jti` denylist for tokens issued to revoked sessions (check on every request, O(1) Redis lookup), (c) switch to opaque tokens with introspection endpoint. Document the chosen approach and its revocation lag in the security model.

2. **OAuth token leakage in browser history and logs**: The `response_type=token` implicit flow puts the access token in the URL fragment, which lands in browser history and server access logs. Always use Authorization Code + PKCE. For redirect URIs, ensure exact string matching (not prefix matching) to prevent open redirect attacks that steal the authorization code.

3. **Account enumeration via timing and error messages**: Returning different error messages for "user not found" vs. "wrong password" enables user enumeration. Always return a generic message ("Invalid credentials"). Use constant-time comparison (`hmac.compare_digest` in Python, `crypto.timingSafeEqual` in Node) for token/hash comparisons. Add a consistent artificial delay (~100ms) to all failed auth responses to prevent timing-based enumeration.
