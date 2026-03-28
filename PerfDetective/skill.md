---
name: perfdetective
description: Profile application performance, identify CPU/memory/I/O bottlenecks, and deliver optimized code with before/after benchmarks. Use when a user needs to find performance issues, reduce latency, lower memory usage, or speed up slow functions/endpoints.
---

# PerfDetective

## Overview

PerfDetective diagnoses and resolves performance bottlenecks across Python, JVM, Node.js, and browser environments using profiling tools, flamegraph analysis, and targeted optimization patterns.

## Workflow

### 1. Identify the Runtime & Collect a Profile

Choose the right profiler for the environment:

- **Python**: `py-spy record -o profile.svg --pid <PID>` (sampling, no code changes) or `cProfile` + `snakeviz` for function-level stats. For async code use `austin` or `yappi`.
- **JVM (Java/Kotlin/Scala)**: `async-profiler` (`asprof -e cpu -f flamegraph.html <PID>`); for heap leaks use `jmap -histo` + Eclipse MAT or VisualVM.
- **Node.js**: `node --prof app.js` + `node --prof-process` or `clinic.js flame` (Clinic.js Doctor for I/O). Use Chrome DevTools Performance tab for in-process profiling.
- **Browser JS/rendering**: Chrome DevTools Performance panel — record a session, look at the "Bottom-Up" and "Call Tree" tabs for hot functions.
- **Benchmarking**: Python → `pytest-benchmark`; JS → `Benchmark.js`; JVM → JMH. Always run 5+ iterations and report median ± p95.

### 2. Read the Flamegraph

- The **width** of a frame = total CPU time consumed (self + children).
- Look for **plateaus** (wide flat tops): that function is the bottleneck.
- Distinguish **CPU-bound** (thick application frames) from **I/O-bound** (thin frames, large gaps, or kernel/syscall stacks like `epoll_wait`, `recv`, `fsync`).
- Identify **unexpected callers**: a utility function appearing high in the stack often signals a hot loop.

### 3. Apply Targeted Optimizations

**CPU-bound hot loops:**
- Memoize pure functions with `functools.lru_cache` (Python) or a `Map`-based cache (JS).
- Replace interpreted loops with vectorized operations: NumPy/pandas for Python, SIMD-friendly array methods in JS/Rust.
- Move heavy computation off the main thread: `concurrent.futures.ProcessPoolExecutor` (Python), Worker Threads (Node.js).

**I/O-bound bottlenecks:**
- Batch database queries: replace N+1 ORM calls with `SELECT ... WHERE id IN (...)` or `DataLoader` (GraphQL).
- Use connection pooling: `psycopg2.pool`, HikariCP, `pg-pool`.
- Add async I/O: `asyncio`/`aiohttp` (Python), `Promise.all` over sequential `await` (JS).
- Cache repeated external calls with Redis (`redis-py`, `ioredis`) using a TTL appropriate to data freshness.

**Memory pressure:**
- Profile heap with `tracemalloc` (Python) or heap snapshots in Chrome DevTools.
- Replace large in-memory collections with generators/streams.
- Fix leaks: deregister event listeners, clear caches, use `WeakRef`/`WeakMap`.

### 4. Benchmark Before & After

Always produce a side-by-side comparison:

```
Function: process_records()
Before: 842 ms median (p95: 1,204 ms), RSS: 340 MB
After:   91 ms median (p95: 118 ms),  RSS: 112 MB
Improvement: 9.3× faster, 67% less memory
```

Report the profiling command used so results are reproducible.

### 5. Deliver the Output

Provide:
1. Root-cause summary (1–3 sentences naming the bottleneck and why it's slow).
2. Diff or rewritten function with inline comments explaining each change.
3. Benchmark table (before/after).
4. Any follow-up work (e.g., "add a Redis layer if this endpoint is called >50 req/s").

## Edge Cases

**1. Profiler overhead skews results.** Sampling profilers (py-spy, async-profiler) have <1% overhead; instrumentation profilers (cProfile, JVM agents) can add 10–50%. Switch to a sampling profiler if numbers look suspiciously slow.

**2. Optimization invalidated by the compiler/JIT.** JVM JIT and V8 TurboFan can eliminate dead code. Always benchmark the production build. Micro-benchmarks eliminated by the optimizer give false wins.

**3. The fix is an architectural change, not a code tweak.** If the flamegraph shows 80%+ in a DB round-trip inside a loop, the right fix is query restructuring or caching — not micro-optimizing the loop body.

**4. JVM GC pause analysis.** Enable GC logging: `-Xlog:gc*:file=gc.log:time,uptime`. Analyze with GCViewer or the online GC Easy tool. Prolonged pauses (>200 ms) in G1 usually indicate too-small heap regions or humongous allocations. Switch to ZGC (`-XX:+UseZGC`) for sub-millisecond pauses on heaps >4 GB; use Shenandoah for moderate heaps with low-latency requirements. Set `-XX:MaxGCPauseMillis` as a target, not a guarantee.

**5. Async Python profiling.** `cProfile` measures wall clock per call but attributes async I/O wait time to the event loop, not the awaiting coroutine — misleading for async code. Use `yappi` with wall-clock mode:
```python
import yappi
yappi.set_clock_type("wall")
yappi.start()
await your_async_function()
yappi.stop()
yappi.get_func_stats().print_all()
```

**6. Long-running memory leak strategy.** Single heap snapshots miss slow leaks. Take three snapshots: at startup, after 30 minutes of load, and after 60 minutes. Compare object counts between snapshots 2 and 3 — objects that grow continuously are the leak candidates. In Python use `tracemalloc`; in Node.js use `--heap-prof` or Chrome DevTools Memory tab (heap snapshot diff); in JVM use Eclipse MAT's "Leak Suspects" report on a heap dump from `jcmd <pid> VM.heap_dump`.
