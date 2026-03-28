---
name: python-master
description: Builds, debugs, and fixes Python code using structured decision workflows with named tools (ruff, mypy, pytest, uv/poetry). Covers environment setup, testing, error handling, performance profiling, memory leak diagnosis, and dependency conflict resolution. Use when a user asks to build, fix, debug, or create Python code.
---

# Python Master

## Overview

Comprehensive Python development skill covering the full lifecycle: environment setup, building clean code, structured debugging, surgical fixing, testing, and performance optimization. Every step uses named tools with exact commands.

## Workflow

### 1. Environment Setup (Always First)

1. Check for existing environment: `.venv/`, `venv/`, or `pyproject.toml`.
   - `pyproject.toml` exists → use `uv` (preferred) or `poetry`.
   - Only `requirements.txt` → `python -m venv .venv && pip install -r requirements.txt`.
   - New project → `uv init <name>` or `poetry new <name>`.
2. Never install into the global Python environment.
3. Confirm: `which python && python --version`.

### 2. Building Code

- PEP 8 compliant; type hints on all function signatures.
- Use `dataclasses` or `pydantic` for structured data; f-strings for formatting.
- One module per concern; functions under 40 lines; no global mutable state.
- After writing: `ruff check . --fix` → `mypy .` → `pytest -x`.
- **Pitfall — mutable defaults**: `def f(x=[])` shares state across calls. Use `def f(x=None): x = x or []`.

### 3. Debugging Decision Workflow

Follow in order — stop at the step that resolves the issue:

1. **Read the full traceback.** Identify file, line, and exception type.
2. `ImportError` / `ModuleNotFoundError` → verify venv is active, `pip show <pkg>`.
3. `TypeError` / `AttributeError` → add `breakpoint()` or `print(type(x), x)` before the failing line.
4. `KeyError` / `IndexError` → inspect data shape; use `.get()` for dicts, guard list access with `len()`.
5. No exception but wrong output → add `logging.debug` at function entry/exit to trace variable state.
6. Test was passing before → `pytest -x --tb=short` to isolate the regression.
7. `RecursionError` → check for missing base case or infinite mutual recursion; add `@functools.lru_cache` if memoization helps.
8. Once root cause is identified, **explain it before applying the fix**.

### 4. Fixing Code

- Surgical fixes only; do not rewrite files unless >60% of logic is wrong.
- After fixing: run `pytest path/to/test_file.py -x`.
- If no tests exist, write a regression test that reproduces the bug **before** fixing.

### 5. Testing

- Framework: `pytest` with tests in `tests/test_*.py`.
- Run: `pytest --tb=short -q` (quick), `pytest --cov=src --cov-report=term-missing` (coverage).
- Use `pytest.mark.parametrize` for data-driven cases; `unittest.mock.patch` / `pytest-mock` for external deps.
- Edge cases: empty input, `None`, boundary values, exception paths.
- Target: every public function has at least one happy-path and one error-path test.

### 6. Error Handling

- Specific exceptions only — never bare `except:`.
- I/O and network calls: `try/except` with `logging.error(msg, exc_info=True)`.
- Re-raise with context: `raise RuntimeError("context") from original_exc`.
- Define custom exceptions for domain errors: `class ValidationError(ValueError): ...`.

### 7. Performance

- **Profile first**: `python -m cProfile -s cumulative script.py | head -20`.
- Collections: `set` for membership, `collections.deque` for queues, `dict` over nested `if` chains.
- Numerical: NumPy vectorized ops over Python loops; `pandas` only for tabular structure.
- Async: `asyncio` with `async def` / `await`; never `time.sleep` in async code.

### 8. Advanced Diagnostics

**Memory leak diagnosis:**
```python
import tracemalloc
tracemalloc.start()
# ... run workload ...
for stat in tracemalloc.take_snapshot().statistics('lineno')[:10]:
    print(stat)
```
Use `objgraph.show_most_common_types()` for reference cycles. For production: Py-Spy or Pyroscope for continuous profiling.

**Dependency conflicts:** `pip check` detects incompatible packages. Use `pip install --dry-run` to trace conflict chains. For forced versions: `constraints.txt` (`pip install -c constraints.txt`). With `uv`: `uv pip install --override`.

**Blocking calls in async code:**
```python
# CPU-bound → ProcessPoolExecutor (bypasses GIL)
# Blocking I/O → ThreadPoolExecutor (default)
loop = asyncio.get_running_loop()
result = await loop.run_in_executor(ProcessPoolExecutor(4), cpu_fn, data)
```
`ThreadPoolExecutor` does NOT bypass the GIL — use only for blocking I/O.

**Concurrency pitfalls:** `threading` shares the GIL — use `multiprocessing` or `ProcessPoolExecutor` for CPU parallelism. For async race conditions, use `asyncio.Lock`. For shared-memory data corruption, use `multiprocessing.Queue` or `multiprocessing.Value` with locks.

## Edge Cases

1. **Package with C extensions on Alpine Linux**: `pip install` fails with missing headers. Use `python:3.x-slim` (glibc) instead of Alpine (musl), or install build deps: `apk add gcc musl-dev`.
2. **Circular imports**: refactor by moving shared types to a `types.py` module, or use `TYPE_CHECKING` guard: `if TYPE_CHECKING: from module import Type`.
3. **`asyncio.run()` inside Jupyter**: Jupyter already runs an event loop. Use `await` directly or `nest_asyncio.apply()`.

## Output Format

When providing a fix or new code:
1. **Root cause**: what went wrong and why.
2. **Change**: the complete updated function/class (not a diff snippet).
3. **Verification**: exact command to confirm the fix works.
