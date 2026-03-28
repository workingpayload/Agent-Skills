---
name: bughunter-pro
description: Diagnoses application bugs using hypothesis-driven debugging, reproduces failures with minimal test cases, isolates root causes, and produces regression tests. Use when a user has an error, unexpected behavior, crash, memory leak, race condition, or intermittent failure they cannot explain.
---

# BugHunter Pro

## Domain Scope

Logic bugs, runtime errors, memory leaks, race conditions, performance regressions, intermittent/flaky failures, and misconfiguration-induced failures. Across languages: Python, JavaScript/TypeScript, Java, Go, C/C++, Rust.

---

## Workflow

### 1. Collect Evidence
Before forming hypotheses, gather:
- **Error message + full stack trace**: get the entire trace, not just the last line.
- **Reproduction steps**: what exact inputs/actions trigger it? Is it 100% reproducible or intermittent?
- **When it started**: last known-good commit/version. Run `git bisect` if unclear.
- **Environment delta**: what changed? (dependency update, config change, OS update, data volume increase)
- **Logs**: timestamps, surrounding context — not just the error line.
- **Code path**: identify the entry point and trace to the failure site.

### 2. Form Hypotheses (Before Touching Code)
Write down 2-4 candidate causes ranked by likelihood. For each:
- State the hypothesis in one sentence.
- State what evidence would confirm or refute it.
- State how to test it without side effects (read-only investigation first).

Example:
```
Hypothesis: Cache returns stale data after TTL expiry because TTL is set in seconds
but the cache library expects milliseconds.
Evidence to confirm: log cache TTL value and compare with documentation default unit.
Test: print effective TTL in ms, check if items expire at wrong time.
```

### 3. Reproduce with a Minimal Test Case
- Reduce the reproduction to the smallest possible input/state. A 5-line reproducer is more valuable than a 500-line one.
- Isolate from external dependencies: mock out database, network, file system where possible.
- Make it deterministic: set seeds for random, control time (`freezegun` in Python, `jest.useFakeTimers()` in JS, `clock.Install()` in Go).
- Write the reproducer as a failing test first — this becomes the regression test.

```python
# Minimal reproducer example
def test_cache_ttl_bug():
    cache = Cache(ttl=1)          # 1 second TTL
    cache.set("key", "value")
    time.sleep(1.1)
    assert cache.get("key") is None  # Fails: returns "value" — TTL bug confirmed
```

### 4. Isolate Root Cause

**Binary search the call stack**: if you have a multi-step pipeline, add assertions/logging at the midpoint to determine which half contains the bug. Repeat until the single faulty function is identified.

**Debugger-first for runtime errors**:
- Python: `python -m pdb script.py` or `breakpoint()` in code; use `pdb.pm()` post-mortem after exception.
- Node.js: `node --inspect-brk` + Chrome DevTools or VS Code debugger.
- Java: remote debug port (`-agentlib:jdwp=transport=dt_socket,server=y,address=5005`).
- Go: `dlv debug` or `dlv test`.
- C/C++: `gdb` with `bt` (backtrace), `info locals`, `watch` on memory addresses.

**Memory issues**:
- Python: `tracemalloc` for allocation tracing; `objgraph.show_growth()` for reference leaks.
- Node.js: `--inspect` + Chrome heap snapshot; `clinic.js` for allocation profiling.
- C/C++: `valgrind --leak-check=full`; `AddressSanitizer` (`-fsanitize=address`).
- Rust: memory safety by default; use `valgrind` or `heaptrack` for fragmentation/performance.

**Race conditions**:
- Python: `threading.Lock()` around shared state; use `queue.Queue` for thread communication.
- Go: `go test -race` (ThreadSanitizer integration); always run with `-race` in CI.
- Java: `synchronized`, `ReentrantLock`, or `java.util.concurrent` atomics; detect with ThreadSanitizer or Helgrind.
- Node.js: event loop is single-threaded but async code has shared state bugs — look for closure captures in callbacks modifying shared variables.

**Intermittent failures checklist**:
- [ ] Time-dependent (timezone, DST, clock skew) — use UTC everywhere, mock system time in tests
- [ ] Order-dependent (tests sharing global state) — add test isolation; check for missing `setUp`/`tearDown`
- [ ] Resource exhaustion (file descriptors, connections) — check for missing `close()`/`finally` blocks
- [ ] Race condition (timing-dependent on CPU/load) — add synchronization, use `-race` flag
- [ ] External service flakiness — add retry logic with backoff; mock in tests

### 5. Fix with Minimal Scope
- Fix only what is broken — do not refactor surrounding code in the same commit.
- Comment the fix with: why this happened, what the fix does, and a link to the issue/ticket.
- If the fix is a workaround rather than a root-cause fix, add a TODO with the root cause explanation.

### 6. Write the Regression Test
The minimal reproducer from Step 3 becomes the regression test. Ensure it:
- Is in the appropriate test suite (unit if isolated, integration if it requires a real DB/service).
- Has a descriptive name: `test_cache_returns_none_after_ttl_expiry_in_seconds_not_ms`.
- Fails before the fix, passes after.
- Is added to CI so it runs on every PR.

### 7. Post-Fix Verification
- Run the full test suite, not just the new test.
- If the bug was in production: verify with the same data/inputs that triggered the original failure.
- For performance bugs: benchmark before and after (`pytest-benchmark`, `go test -bench=.`, `criterion` for Rust).

### 8. CI Parallelism and Test Isolation
When running tests in parallel with `pytest-xdist` (`pytest -n auto`), tests share a single process per worker but not across workers. Common pitfalls:
- **Database conflicts**: use per-worker databases. In `conftest.py`, read `worker_id = os.environ.get("PYTEST_XDIST_WORKER", "gw0")` and create/use `test_db_{worker_id}`.
- **Temp directory collisions**: use `tmp_path` fixture (xdist-safe) instead of hardcoded `/tmp/test_*` paths.
- **Port conflicts**: bind to `port=0` (OS assigns ephemeral port) instead of a fixed port in test servers.
- Fixture scope matters: `scope="session"` fixtures are shared within a worker process, not across workers — avoid mutable session-scoped state.

### 9. Production Memory Leak Detection
For live services, use continuous profiling instead of one-shot heap dumps:
- **Pyroscope** (Go/Python/Ruby): agent auto-instruments and streams flame graphs to the Pyroscope server. Zero code changes for Go; add `pyroscope.start()` for Python.
- **Parca** (eBPF-based, language-agnostic): attaches to running processes via eBPF, no instrumentation required. Safe for production — read-only kernel hooks.
- **Heap snapshots in Node.js**: use `v8.writeHeapSnapshot()` triggered by `SIGUSR2` signal handler — safer than `--inspect` in production. Compare two snapshots with Chrome DevTools to find retained objects.
- Establish a baseline heap size metric in your APM (Datadog, Prometheus) and alert when heap grows >20% over 1 hour without traffic increase.

---

## Output Artifacts

- **Root cause statement**: 1-2 sentences explaining exactly what is wrong and why.
- **Minimal reproducer**: failing test case (code).
- **Fix**: minimal diff with explanatory comment.
- **Regression test**: named test that prevents recurrence.
- **Impact assessment**: was other code affected by the same pattern?

---

## Edge Cases

1. **Heisenbug — bug disappears when instrumented**: Adding logging or a debugger changes timing or memory layout, making the bug disappear. For race conditions: use `ThreadSanitizer`/`-race` instead of print statements. For memory bugs: use `AddressSanitizer` or Valgrind. For timing-sensitive bugs: write a stress test that runs the scenario in a tight loop (1000+ iterations) to increase the probability of manifestation.

2. **Bug in a third-party library**: Confirm the bug is in the library and not in how it is called by writing a standalone minimal reproducer that uses only the library's public API. Check the library's issue tracker and changelog. If confirmed: pin to a known-good version, add a wrapper that documents the workaround, and open an upstream issue. Do not monkey-patch library internals without documenting it explicitly.

3. **Data-dependent bugs that only appear in production**: The production dataset has edge cases not present in dev/test (null values, Unicode, very large records, specific date ranges). Steps: (a) sanitize and import a production data sample into a local environment, (b) add database query logging to identify the exact record(s) triggering failure, (c) add property-based tests (`hypothesis` in Python, `fast-check` in JS, `quickcheck` in Rust/Haskell) that generate random inputs including boundary values to catch similar cases automatically.
