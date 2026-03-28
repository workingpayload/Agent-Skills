---
name: fastapi-furious
description: Builds, debugs, and fixes FastAPI applications with structured project scaffolding, endpoint checklists, Alembic migrations, security (CORS, rate limiting, JWT), async testing with httpx, and advanced patterns (WebSockets, file uploads, BackgroundTasks). Use when a user asks to build, create, fix, debug, or improve FastAPI code.
---

# FastAPI Furious

## Overview

Production-ready FastAPI development covering project structure, endpoint design with validation checklists, database/migrations with Alembic, security hardening, async testing, and advanced patterns (WebSockets, file uploads, background tasks).

## Workflow

### 1. Project Scaffold

```
project/
├── app/
│   ├── main.py            # App instance, middleware, lifespan events
│   ├── api/v1/
│   │   ├── router.py      # Includes all v1 sub-routers
│   │   └── endpoints/     # One file per resource (users.py, items.py)
│   ├── core/
│   │   ├── config.py      # pydantic-settings BaseSettings; reads .env
│   │   └── security.py    # Password hashing, JWT encode/decode
│   ├── crud/              # DB query functions (no business logic)
│   ├── models/            # SQLAlchemy ORM models
│   ├── schemas/           # Pydantic v2 request/response models
│   └── deps.py            # Shared dependencies (get_db, get_current_user)
├── alembic/
├── tests/
│   ├── conftest.py        # Async test client, test DB setup
│   └── test_*.py
├── pyproject.toml
└── .env.example
```

### 2. Endpoint Checklist

Apply to every endpoint before it is complete:

- [ ] `response_model=Schema` declared for validated, documented output.
- [ ] `async def` for any I/O (DB, file, HTTP). Never `time.sleep` in async.
- [ ] `HTTPException` with standard status codes; never error detail in a 200.
- [ ] `Depends()` for DB sessions, auth, config — never instantiate in route body.
- [ ] Pydantic `Field(...)` constraints (`min_length`, `ge`, `pattern`) over manual `if` checks.
- [ ] Status: `201` for creation, `204` for delete with no body.

### 3. Database & Migrations (Alembic)

- Async engine: `create_async_engine(settings.DATABASE_URL)`.
- Session dependency:
  ```python
  async def get_db() -> AsyncGenerator[AsyncSession, None]:
      async with AsyncSessionLocal() as session:
          yield session
  ```
- Migration workflow: edit model → `alembic revision --autogenerate -m "description"` → review generated file → `alembic upgrade head`.
- **Pitfall**: `autogenerate` misses some changes (column type changes, constraints). Always review the diff before applying.
- Never edit applied migrations; create a new revision instead.

### 4. Security

- **CORS**: explicit `allow_origins` list. Never `["*"]` in production.
- **Rate limiting**: `slowapi` or `fastapi-limiter` (Redis-backed) on public endpoints. Stricter limits on auth endpoints.
- **Auth**: `python-jose` for JWT. Secrets via `pydantic-settings`; never hardcoded.
- **SQL injection**: always ORM queries or parameterized statements — never f-string SQL.

### 5. Error Handling

```python
@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    logger.error("Unhandled error", exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
```
- Custom exceptions for domain errors with dedicated handlers.
- Never expose raw stack traces to API consumers.

### 6. Testing

`pytest` + `httpx.AsyncClient` (all async). Per endpoint:
- Happy path: correct response model + status.
- `422` on bad input (missing field, wrong type).
- `401` on missing/invalid token.
- `404` on missing resource.

Mock external HTTP with `respx`. Use SQLite in-memory or separate Postgres schema — never production DB.

### 7. Debugging Decision Workflow

1. **Server won't start** → read traceback; usually missing env var or import error.
2. **422 Unprocessable Entity** → log `await request.body()`; compare against Pydantic schema.
3. **500 in production** → check structured logs for request ID; correlate with exception handler.
4. **Slow query** → `echo=True` on SQLAlchemy engine to log SQL; add index or rewrite.
5. **Event loop blocked** → `run_in_executor` for CPU-bound or synchronous blocking calls.
6. **Startup hangs** → check `lifespan` context manager; ensure `yield` is reached and async DB connections resolve.

### 8. Advanced Patterns

**WebSocket endpoints:**
```python
@router.websocket("/ws/{client_id}")
async def ws(websocket: WebSocket, client_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        pass  # Clean up connection state
```
Multi-instance: broadcast via Redis pub/sub, not in-process state. Add auth via query param token or first-message handshake.

**BackgroundTasks vs. task queue:** `BackgroundTasks` for fire-and-forget < 5s (emails, logging). External queue (Celery, ARQ, Dramatiq) for long-running, retriable, or critical work (payments, exports). Never `BackgroundTasks` for anything requiring failure tracking.

**File uploads:**
```python
@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    if file.size and file.size > 10_000_000:
        raise HTTPException(413, "File too large")
    contents = await file.read()
    return {"filename": file.filename, "size": len(contents)}
```
Large files: stream to S3/GCS via `file.read(chunk_size)` loop. Set `client_max_body_size` at nginx level.

**Lifespan events (replacing deprecated `on_startup`/`on_shutdown`):**
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = await create_pool()  # startup
    yield {"pool": pool}
    await pool.close()          # shutdown
```

## Edge Cases

1. **ASGI lifespan not supported by test client**: use `httpx.ASGITransport(app=app)` in test `conftest.py` to handle lifespan events during testing.
2. **Pydantic v1 vs v2 migration**: FastAPI 0.100+ uses Pydantic v2. If upgrading, run `bump-pydantic` to auto-migrate models. Key changes: `orm_mode` → `from_attributes`, `validator` → `field_validator`.
3. **Async DB session leaks**: if `get_db` doesn't use `async with`, sessions may not close on exceptions. Always use context manager pattern.

## Output Format

- Provide the complete updated file for changed files.
- State: (a) root cause (if debugging), (b) what changed, (c) how to verify.
