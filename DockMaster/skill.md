---
name: dockmaster
description: Creates optimized, secure Dockerfiles using multi-stage builds, non-root users, pinned digests, and .dockerignore. Scans images with Trivy, writes Docker Compose files, and advises on Helm chart structure. Use when a user asks to write a Dockerfile, containerize an application, or set up container orchestration.
---

# DockMaster

## Overview

Produce production-grade Dockerfiles and Compose configs that are minimal, reproducible, and secure. Every image must: use multi-stage builds to minimize final size, run as a non-root user, pin base images to digests, and pass a Trivy scan with no CRITICAL or HIGH CVEs.

## Workflow

### 1. Analyze the Application

Determine:
- **Runtime**: Node.js, Python, Go, Java, etc.
- **Build requirements**: compiler, package manager, test runner
- **Artifact**: compiled binary, bundled JS, JAR, or source with interpreter
- **Port and protocol**: HTTP, gRPC, WebSocket
- **Config source**: environment variables, mounted secrets, config files

### 2. Write a Multi-Stage Dockerfile

Separate the **build** stage (has compilers, dev deps, source code) from the **runtime** stage (has only what runs).

**Node.js example:**
```dockerfile
# syntax=docker/dockerfile:1
FROM node:20.11-alpine3.19 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --ignore-scripts
COPY . .
RUN npm run build

FROM node:20.11-alpine3.19 AS runtime
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
WORKDIR /app
COPY --from=builder --chown=appuser:appgroup /app/dist ./dist
COPY --from=builder --chown=appuser:appgroup /app/node_modules ./node_modules
USER appuser
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

**Go (scratch final stage for minimal attack surface):**
```dockerfile
FROM golang:1.22-alpine3.19 AS builder
WORKDIR /app
COPY go.* ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o server ./cmd/server

FROM scratch AS runtime
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /app/server /server
EXPOSE 8080
ENTRYPOINT ["/server"]
```

**Scratch image hidden deps**: The `scratch` base has no timezone database, no `/etc/nsswitch.conf`, and no `/etc/passwd`. If your binary calls `time.LoadLocation()`, DNS resolves via NSS, or reads user info, copy the needed files explicitly:
```dockerfile
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo
COPY --from=builder /etc/passwd /etc/passwd
```

### 3. Pin Base Images to Digests

Tags are mutable. Use digests for reproducibility:
```dockerfile
FROM node:20.11-alpine3.19@sha256:a8b5c... AS builder
```

Get the digest: `docker pull node:20.11-alpine3.19 && docker inspect node:20.11-alpine3.19 --format='{{index .RepoDigests 0}}'`

### 4. Write .dockerignore

Exclude: `.git`, `.env*`, `node_modules`, `__pycache__`, `dist`, `build`, `coverage`, `*.log`, `docs/`, `tests/`. This prevents secrets and large dirs from entering the build context.

### 5. Scan with Trivy

```bash
trivy image --severity HIGH,CRITICAL --exit-code 1 myapp:latest
trivy config --exit-code 1 ./Dockerfile
```

Fix CVEs by bumping to a newer base image, or removing packages that introduced them. Prefer a newer base over `apt-get upgrade -y` in the build stage.

### 6. Write Docker Compose for Local Development

```yaml
# compose.yml (Docker Compose v2 — preferred over docker-compose.yml)
services:
  app:
    build:
      context: .
      target: runtime
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - DATABASE_URL=postgresql://dev:dev@db:5432/myapp
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  db:
    image: postgres:16.2-alpine3.19@sha256:...
    environment:
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
      POSTGRES_DB: myapp
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dev -d myapp"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s   # grace period before health failures count; use for slow-starting services

volumes:
  postgres_data:
```

### 7. Helm Chart Structure (Kubernetes)

Standard layout: `Chart.yaml`, `values.yaml`, `values.prod.yaml`, `templates/{deployment,service,ingress,configmap,secret,hpa}.yaml`. Always set `resources.requests`/`limits` and `securityContext.runAsNonRoot: true`, `readOnlyRootFilesystem: true`.

**Note on `pg_isready`**: `pg_isready` only checks that Postgres accepts connections — it does not verify schema migrations have run or that the DB is ready for DDL. For services that run migrations on startup, add a retry loop in the app or use an init container.

## Output Format

Provide:
1. The complete Dockerfile with inline comments explaining non-obvious choices
2. The `.dockerignore` file
3. `compose.yml` if local dev setup was requested
4. Trivy scan command to run, and how to interpret results

## Edge Cases

**BuildKit prerequisite**: `RUN --mount=type=secret`, `RUN --mount=type=cache`, and `# syntax=docker/dockerfile:1` directives require BuildKit. Enable with `DOCKER_BUILDKIT=1 docker build .` or use `docker buildx build .` (BuildKit is the default in Docker 23+). Without BuildKit, these directives are silently ignored or cause build errors.

**Secrets in build args**: Never use `ARG` for secrets — they appear in `docker history`. Use `--secret` with BuildKit:
```dockerfile
RUN --mount=type=secret,id=npm_token \
    NPM_TOKEN=$(cat /run/secrets/npm_token) npm install
```

**Large monorepo context**: If `docker build` is slow due to context size, add `# syntax=docker/dockerfile:1` and use `--mount=type=cache` for package manager caches:
```dockerfile
RUN --mount=type=cache,target=/root/.npm npm ci
```

**ARM64 / multi-platform images**: Build with `docker buildx build --platform linux/amd64,linux/arm64 -t myapp:latest --push .` and ensure base images support both platforms.
