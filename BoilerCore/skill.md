---
name: boilercore
description: Scaffolds production-ready project structures with ecosystem-appropriate conventions, CI/CD pipelines, linter/formatter configs, and dependency setup. Use when a user needs to start a new project, add missing tooling infrastructure to an existing codebase, or standardize a project layout.
---

# BoilerCore

## Domain Scope

Project initialization and scaffolding for: Node.js/TypeScript, Python, Go, Java/Kotlin, Rust. Covers file structure, dependency management, linting, formatting, testing setup, CI/CD pipeline, Docker, and environment configuration.

---

## Workflow

### 1. Intake Checklist
Before scaffolding, determine:
- [ ] **Language / runtime**: Node 20+, Python 3.11+, Go 1.22+, Java 21, Rust stable?
- [ ] **Project type**: REST API, CLI tool, library/package, frontend app, monorepo?
- [ ] **Framework**: Express/Fastify/NestJS, FastAPI/Django/Flask, Gin/Chi, Spring Boot, Axum?
- [ ] **Test framework**: Jest/Vitest, pytest, Go test, JUnit 5, cargo test?
- [ ] **CI platform**: GitHub Actions, GitLab CI, CircleCI, Jenkins?
- [ ] **Container**: Docker required? Kubernetes manifests needed?
- [ ] **Package manager**: npm/pnpm/yarn, pip/uv/poetry, go mod, Maven/Gradle, Cargo?

### 2. File Tree Output
Always provide an annotated file tree first:
```
my-api/
├── src/
│   ├── routes/          # Route handlers
│   ├── services/        # Business logic
│   ├── repositories/    # Data access layer
│   └── index.ts         # Entry point
├── tests/unit/ tests/integration/
├── .github/workflows/   # ci.yml, release.yml
├── docker/Dockerfile docker-compose.yml
├── .env.example
└── package.json / pyproject.toml / go.mod
```

### 3. Language-Specific Conventions

**Node.js / TypeScript**: `tsconfig.json` with `strict: true`, `noUncheckedIndexedAccess: true`. ESLint + `@typescript-eslint/recommended`. Prettier. pnpm (monorepos). Vitest.

**Python**: `pyproject.toml` (PEP 517). `uv` or `poetry`. Ruff (lint + format). mypy `strict = true`. pytest + `pytest-cov`. Use `src/` layout.

**Go**: `go.mod`. `cmd/`, `internal/`, `pkg/` layout. `golangci-lint` with `errcheck`, `gosec`. Makefile with `build`, `test`, `lint`, `clean`.

**Rust**: `Cargo.toml` workspace. `cargo clippy -- -D warnings`. `cargo fmt`. `cargo audit` in CI.

### 4. npm Dual-Registry Publishing
For packages published to both npm public registry and a private registry (e.g., GitHub Packages):
```ini
# .npmrc
@myorg:registry=https://npm.pkg.github.com
//npm.pkg.github.com/:_authToken=${GITHUB_TOKEN}
```
```json
// package.json
"publishConfig": {
  "registry": "https://registry.npmjs.org",
  "access": "public"
}
```
Scoped packages (`@myorg/pkg`) route to the private registry; unscoped packages use the public registry. In CI, set `NODE_AUTH_TOKEN` for npm and `GITHUB_TOKEN` for GitHub Packages as separate secrets.

### 5. Alpine vs Slim Docker Images
- **Alpine** (`node:20-alpine`, `python:3.11-alpine`): ~5–10 MB base. Uses musl libc. Native extensions that require glibc (e.g., `sharp`, `bcrypt`, some Python C extensions) **will fail** or require extra build packages (`apk add python3 make g++`).
- **Slim** (`node:20-slim`, `python:3.11-slim`): ~50–80 MB base. Uses glibc. Native extensions work out of the box.
- **Rule of thumb**: use Alpine for pure-JS/pure-Python services. Use slim (or `debian:bookworm-slim`) when any dependency includes native extensions. Always test the final image — not just the build stage.

### 6. CI/CD Pipeline (GitHub Actions)
```yaml
name: CI
on: [pull_request, push]
jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'pnpm' }
      - run: pnpm install --frozen-lockfile
      - run: pnpm run typecheck && pnpm run lint && pnpm run test -- --coverage
```
Key rules: `--frozen-lockfile` always; fail on warnings (`--max-warnings 0`); cache by lockfile hash; coverage gate ≥ 80%.

### 7. Environment Configuration
`.env.example`: document every var with type and example. Never commit `.env`. Validate at startup:
```typescript
// env.ts
import { z } from 'zod';
export const env = z.object({
  DATABASE_URL: z.string().url(),
  JWT_SECRET: z.string().min(32),
  PORT: z.coerce.number().default(3000),
}).parse(process.env);
```

### 8. Docker Setup
```dockerfile
FROM node:20-slim AS builder       # slim for native extension compatibility
WORKDIR /app
COPY pnpm-lock.yaml package.json ./
RUN corepack enable && pnpm install --frozen-lockfile
COPY . . && RUN pnpm build

FROM node:20-slim AS runner
RUN addgroup -S app && adduser -S app -G app
COPY --from=builder --chown=app:app /app/dist ./dist
COPY --from=builder --chown=app:app /app/node_modules ./node_modules
USER app
EXPOSE 3000
CMD ["node", "dist/index.js"]
```
`.dockerignore`: exclude `node_modules`, `.git`, `.env`, `*.log`.

---

## Output Artifacts

- Annotated file tree with purpose comments.
- All config files: tsconfig/pyproject/go.mod, linter, formatter.
- CI/CD workflow file(s), Dockerfile + docker-compose.yml.
- `.env.example` with all required variables documented.

---

## Edge Cases

1. **Monorepo with mixed languages**: Workspace root with shared CI matrix. Node.js: pnpm workspaces + Turborepo (`turbo.json` pipeline). Avoid sharing `node_modules` between packages with incompatible peer deps.

2. **Conflicting peer dependencies**: Document in `peerDependenciesMeta` or add `overrides`. Python: pin all deps with `uv.lock` / `poetry.lock`. Never `pip install` without a lockfile in production.

3. **Scaffolding onto existing codebase**: Check for existing configs before writing. Present a diff of proposed changes. Require explicit confirmation before overwriting.
