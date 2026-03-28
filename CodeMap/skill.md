---
name: codemap
description: Generates and maintains a structured codemap file that gives AI agents instant codebase context without costly exploration. Produces a navigable index of entry points, modules, key abstractions, dependency flow, and file roles. Use when starting a new session, after major refactors, at PR boundaries, or when an agent is burning context on repeated file discovery.
---

# CodeMap

## Overview

Generates a `.codemap.md` file at the repository root — a structured index that gives AI agents instant codebase orientation without spending tokens on exploration. Regenerated at **checkpoints**: session start, post-merge, post-refactor, or on demand.

---

## Workflow

### 1. Discover Project Shape

Scan the repo to determine language(s) (from `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`), framework (React, FastAPI, Spring Boot, etc.), monorepo layout (`workspaces`, `packages/`, `apps/`), and build system (`Makefile`, `docker-compose.yml`, CI config).

Build a file tree via `glob`. Exclude: `node_modules`, `.git`, `dist`, `build`, `__pycache__`, `.venv`, `vendor`, `coverage`, `.next`.

### 2. Classify Files by Role

Assign each significant file one or more roles:

| Role | Description | Examples |
|------|-------------|----------|
| **entry** | Application entry point | `main.py`, `index.ts`, `cmd/server/main.go`, `App.tsx` |
| **route** | HTTP/API route definitions | `routes/*.py`, `app/api/**/*.ts`, `controllers/` |
| **model** | Data models / schemas / types | `models/`, `schema.prisma`, `types.ts`, `entities/` |
| **service** | Business logic layer | `services/`, `usecases/`, `domain/` |
| **repo** | Data access / database layer | `repositories/`, `dal/`, `db/queries/` |
| **config** | Configuration and env setup | `config/`, `settings.py`, `.env.example`, `next.config.js` |
| **test** | Test files | `tests/`, `__tests__/`, `*_test.go`, `*.spec.ts` |
| **migration** | Database migrations | `migrations/`, `alembic/versions/`, `prisma/migrations/` |
| **infra** | Infrastructure / deployment | `Dockerfile`, `k8s/`, `terraform/`, `docker-compose.yml` |
| **script** | Build/dev/CI scripts | `scripts/`, `Makefile`, `bin/` |
| **ui** | Frontend components | `components/`, `pages/`, `views/`, `templates/` |
| **middleware** | Request/response interceptors | `middleware/`, `interceptors/` |
| **util** | Shared utilities / helpers | `utils/`, `lib/`, `helpers/`, `common/` |

Skip files under 5 lines (empty stubs) and auto-generated files (note them as `[generated]`).

### 3. Map Key Abstractions

For each module/package, identify:

- **Exported interfaces / classes / functions**: the public API surface.
- **Primary responsibility**: one sentence.
- **Key dependencies**: what it imports from other internal modules (not third-party).

Use this to build a **dependency graph** section showing how modules connect:

```
auth/service.py → db/user_repo.py → models/user.py
                → utils/jwt.py
                → config/settings.py
```

### 4. Identify Hot Paths

Mark the most-changed files using `git log --format='' --name-only | sort | uniq -c | sort -rn | head -20`. These are the files an agent will most likely need to modify.

Also flag:
- Files with the most imports (high fan-in = critical shared code).
- Files with the most outgoing imports (high fan-out = potential god modules).
- Files touched in the last 5 commits (active work area).

### 5. Generate the Codemap

Write `.codemap.md` at the repository root with this structure:

```markdown
# Codemap
> Auto-generated at <ISO-8601 timestamp>. Checkpoint: <reason>.

## Project
- **Language**: TypeScript, Python
- **Framework**: Next.js 14 (App Router), FastAPI
- **Package manager**: pnpm, uv
- **Monorepo**: yes (apps/web, apps/api, packages/shared)

## Directory Map
```
apps/
  web/                    # Next.js frontend [entry: app/layout.tsx]
    app/                  # App Router pages and layouts [ui]
    components/           # React components [ui]
    lib/                  # Client utilities [util]
  api/                    # FastAPI backend [entry: main.py]
    routes/               # API endpoints [route]
    services/             # Business logic [service]
    models/               # SQLAlchemy models [model]
    repositories/         # Data access [repo]
packages/
  shared/                 # Shared types and constants [util]
```

## Entry Points
| File | Role | Description |
|------|------|-------------|
| `apps/web/app/layout.tsx` | entry | Root layout, providers, global CSS |
| `apps/api/main.py` | entry | FastAPI app factory, middleware, router mount |
| `apps/api/worker.py` | entry | Celery worker bootstrap |

## Module Map
### apps/api/services/auth.py [service]
- **Does**: Handles login, signup, token refresh, password reset.
- **Exports**: `authenticate_user()`, `create_tokens()`, `refresh_access_token()`
- **Depends on**: `repositories/user_repo`, `models/user`, `utils/jwt`, `config/settings`

### apps/web/lib/api-client.ts [util]
- **Does**: Typed fetch wrapper for all API calls.
- **Exports**: `apiClient`, `useQuery` wrappers
- **Depends on**: `packages/shared/types`

## Dependency Flow
```
[web] app/page.tsx → lib/api-client.ts → [api] routes/auth.py → services/auth.py → repositories/user_repo.py → models/user.py
```

## Hot Files (most changed, last 30 days)
| File | Changes | Last touched |
|------|---------|-------------|
| `apps/api/services/auth.py` | 14 | 2 days ago |
| `apps/web/app/(dashboard)/page.tsx` | 11 | today |

## Active Work Area (last 5 commits)
- `apps/api/routes/billing.py` — new Stripe webhook handler
- `apps/web/components/PricingTable.tsx` — pricing UI overhaul
```

### 6. Embed Checkpoint Metadata

Add a `.codemap-meta.json` alongside the codemap:

```json
{
  "version": 1,
  "generated_at": "2026-03-28T12:00:00Z",
  "checkpoint": "post-merge main",
  "file_count": 247,
  "module_count": 18,
  "git_sha": "a1b2c3d",
  "hot_files_window_days": 30
}
```

This lets the agent decide whether the codemap is stale (compare `git_sha` to `HEAD`).

---

## Checkpoint Triggers

Regenerate the codemap when:

| Trigger | When | Command |
|---------|------|---------|
| **Session start** | Agent begins a new conversation | Auto-check: if `.codemap.md` is stale or missing, regenerate |
| **Post-merge** | After merging a PR or rebasing | Regenerate to reflect new files and structure |
| **Post-refactor** | After moving/renaming files or directories | Regenerate to update paths and dependency flow |
| **On demand** | User requests `/codemap` | Full regeneration |
| **Pre-PR** | Before opening a pull request | Update hot files and active work area sections |
| **Staleness threshold** | `.codemap-meta.json` `git_sha` != current `HEAD` and > 10 commits behind | Auto-suggest regeneration |

---

## Edge Cases

1. **Monorepo with 500+ packages**: Do not map every file. Generate a top-level codemap with package summaries, then generate per-package codemaps (`packages/auth/.codemap.md`) only for packages the agent is actively working in. Use `--scope <package>` to limit scope.

2. **Generated code directories** (Prisma client, protobuf, OpenAPI): Mark entire directories as `[generated — do not edit]` in the directory map. Do not analyze individual files or exports. Note the generator config file (e.g., `schema.prisma`, `proto/*.proto`) as the real source of truth.

3. **Rapidly changing codebase** (10+ commits/day to same area): Set `hot_files_window_days` to 7 instead of 30 to keep the hot files section relevant. Consider running codemap generation as a post-commit hook or CI step.

4. **No git history** (fresh clone, shallow clone, or non-git project): Skip hot files and active work area sections. Use file modification timestamps (`stat`) as a fallback for recency. Note the limitation in the codemap header.

5. **Very large files** (> 1000 lines): Do not attempt to list all exports. Instead, note the file as `[large — 1,247 lines]` and list only the top 5 most-imported exports (determine via grep for import/require statements across the codebase).

6. **Polyglot repos** (e.g., Python backend + TypeScript frontend + Go CLI): Generate separate module map sections per language/runtime. Cross-language dependencies (e.g., frontend calling backend API) go in the Dependency Flow section as `[HTTP]` or `[gRPC]` edges, not direct import arrows.

7. **Codemap conflicts on merge**: `.codemap.md` will frequently conflict in merge scenarios since it changes with every checkpoint. Add `.codemap.md` and `.codemap-meta.json` to `.gitattributes` with `merge=ours` strategy, or add to `.gitignore` and generate locally. Recommend: do not commit the codemap; generate it on session start.

---

## Output Format

The primary output is `.codemap.md` (see Section 5 for template). Print a summary:

```
Codemap generated: .codemap.md
  Files scanned: 247 | Modules: 18 | Entry points: 3 | Hot files: 12
  Git SHA: a1b2c3d | Checkpoint: session-start
```
