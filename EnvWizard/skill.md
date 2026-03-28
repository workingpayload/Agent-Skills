---
name: envwizard
description: Manages environment variables and secrets securely: creates .env.example, validates required vars at startup with envalid or pydantic-settings, integrates vault solutions (HashiCorp Vault, AWS Secrets Manager, Doppler), prevents secret leaks with git-secrets, and separates build-time from runtime config. Use when a user asks to set up environment config, manage secrets, or validate environment variables.
---

# EnvWizard

## Overview

Every application needs config. Config done wrong leaks secrets into git, breaks deployments silently, and creates "works on my machine" problems. Follow this workflow to do it right: validate early, separate concerns, never commit secrets.

## Workflow

### 1. Categorize Variables

Separate into three buckets before writing any code:

**Build-time config** (baked into image/artifact at compile/bundle time):
- `NODE_ENV`, `VITE_API_URL`, `REACT_APP_*`, `NEXT_PUBLIC_*`
- Set via CI/CD env vars or `--build-arg` in Docker

**Runtime config** (read when the process starts):
- `PORT`, `LOG_LEVEL`, `DATABASE_URL`, `REDIS_URL`, feature flags

**Secrets** (never in env var files on disk, never in image layers):
- API keys, database passwords, private keys, JWT secrets
- Source from a vault at runtime; inject as env vars or files

### 2. Create .env.example

Commit this file. It is the contract for what variables are needed. Never put real values in it.

```bash
# .env.example — copy to .env and fill in values
# Application
PORT=3000
NODE_ENV=development
LOG_LEVEL=info

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/myapp
DATABASE_POOL_SIZE=10

# Redis
REDIS_URL=redis://localhost:6379

# Auth
JWT_SECRET=<generate with: openssl rand -hex 32>
JWT_EXPIRES_IN=7d

# External APIs (get from https://dashboard.stripe.com/apikeys)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Feature flags
ENABLE_NEW_CHECKOUT=false
```

Create `.env.local` for local overrides (gitignored), `.env.test` for test values (can be committed if no real secrets), and `.env.production` only on the server via your secrets manager.

### 3. Prevent Secret Leaks with git-secrets

Install and configure before the first commit:
```bash
git secrets --install && git secrets --register-aws
git secrets --add 'sk_live_[a-zA-Z0-9]+'   # Stripe live keys
git secrets --add 'password\s*=\s*\S+'
git secrets --scan-history
```

**False positive handling**: Legitimate strings that match secret patterns (e.g., example keys in docs) can be allowlisted: `git secrets --add --allowed 'sk_test_example'`. For `detect-secrets`, run `detect-secrets scan > .secrets.baseline` to establish a baseline, then commit `.secrets.baseline` — future scans only flag new secrets not in the baseline.

Add to `.gitignore`:
```
.env
.env.local
.env.production
.env.*.local
*.pem
*.key
secrets/
```

### 4. Validate at Startup (Fail Fast)

**Node.js with envalid:**
```typescript
import { cleanEnv, str, port, url, bool, num } from 'envalid';

export const env = cleanEnv(process.env, {
  NODE_ENV:       str({ choices: ['development', 'test', 'production'] }),
  PORT:           port({ default: 3000 }),
  DATABASE_URL:   url(),
  REDIS_URL:      url(),
  JWT_SECRET:     str({ docs: 'https://internal/secrets' }),
  LOG_LEVEL:      str({ choices: ['debug', 'info', 'warn', 'error'], default: 'info' }),
  STRIPE_SECRET:  str(),
  ENABLE_FEATURE: bool({ default: false }),
  WORKER_COUNT:   num({ default: 4 }),
});

// env.PORT is typed as number, env.DATABASE_URL is string
// Process exits immediately with a clear error if any required var is missing
```

**Python with pydantic-settings:**
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, AnyUrl

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    port: int = 8000
    database_url: AnyUrl
    jwt_secret: SecretStr   # requires .get_secret_value() to read
    log_level: str = "info"

settings = Settings()  # raises ValidationError on startup if misconfigured
```

### 5. Integrate a Vault Solution

**HashiCorp Vault**: `envconsul -secret secret/myapp/production ./myapp` — injects secrets as env vars and restarts the process on rotation.

**AWS Secrets Manager (Python)**:
```python
import boto3, json
def get_secret(name): return json.loads(boto3.client("secretsmanager").get_secret_value(SecretId=name)["SecretString"])
```

**Doppler**: `doppler run -- node dist/index.js` — injects all project secrets as env vars without modifying code.

### 6. Separate Build vs Runtime in Docker

Use `ARG` for build-time non-sensitive values (`NODE_ENV`, `NEXT_PUBLIC_API_URL`). Use `ENV` for runtime defaults. Never use `ARG JWT_SECRET` — ARGs appear in `docker history`. Inject secrets at container start via `env_file: .env.local` (Compose) or `envFrom.secretRef` (Kubernetes).

## Output Format

Provide:
1. `.env.example` with all variables, safe placeholder values, and source comments
2. Startup validation code (envalid or pydantic-settings)
3. `.gitignore` additions
4. git-secrets setup commands
5. Vault integration snippet for the deployment target

## Edge Cases

**Secret rotation dual-version window**: AWS Secrets Manager rotation uses `AWSPENDING` (new secret being set) and `AWSCURRENT` (active secret) stages. During rotation, both versions are valid simultaneously — design the app to accept either until rotation completes (`setSecret` → `testSecret` → `finishSecret` Lambda hooks). Vault dynamic secrets have a lease TTL; renew leases before expiry or the credential is revoked mid-session.

**Multi-tenant config**: Per-tenant config (API keys, feature flags, limits) should not live in env vars — use a DB-backed config table or a key-value store keyed by tenant ID. Inject tenant config at request time after authentication, not at process startup. This enables runtime changes without redeployment.

**Rotating secrets without downtime**: Design the app to read secrets on each request or cache with a TTL (e.g., 5 minutes), not at startup. For database credentials, use a connection pool that reconnects on auth failure, triggering a fresh Vault lookup.

**Different envs needing different validation**: Use `envalid`'s `devDefault` or pydantic-settings' `default` for vars that are optional in development but required in production. Add an explicit check: `if settings.node_env == "production": assert settings.stripe_secret_key`.

**Leaked secret in git history**: Run `git filter-repo --path .env --invert-paths` to remove the file. Rotate all exposed credentials immediately — assume they are compromised. Notify the security team.
