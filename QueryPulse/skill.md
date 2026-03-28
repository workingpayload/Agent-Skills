---
name: querypulse
description: Analyze and optimize SQL query performance using EXPLAIN ANALYZE, index design, covering indexes, N+1 detection, and deadlock diagnosis across PostgreSQL and MySQL. Use when a user has a slow query, a deadlock, a missing index, or wants to understand a query execution plan.
---

# QueryPulse

## Overview

QueryPulse diagnoses SQL performance problems using execution plan analysis, index theory, and engine-specific optimizations for PostgreSQL and MySQL.

## Workflow

### 1. Collect the Execution Plan

Always start with the actual (not estimated) plan:

**PostgreSQL:**
```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) <your query>;
```
- `ANALYZE`: runs the query and shows actual row counts and timing.
- `BUFFERS`: shows cache hit vs. disk read ratio.

**MySQL / MariaDB:**
```sql
EXPLAIN FORMAT=JSON <your query>;
-- Or for actual execution stats (MySQL 8.0+):
EXPLAIN ANALYZE <your query>;
```

Ask for the full output, not a screenshot. Key fields to examine:
- `Seq Scan` / `ALL` type → full table scan, likely missing an index.
- `Rows` estimate vs. actual: large divergence → stale statistics; run `ANALYZE <table>` (Postgres) or `ANALYZE TABLE <table>` (MySQL).
- `cost` / `actual time`: find the most expensive node.
- `Buffers: shared hit/read`: low hit ratio → data not in cache, I/O bound.

### 2. Identify the Bottleneck Type

**Missing or unused index:**
- Look for `Seq Scan` on large tables or `Using filesort` / `Using temporary` in MySQL.
- Check existing indexes: `\d <table>` (psql) or `SHOW INDEX FROM <table>` (MySQL).

**Poor index selectivity:**
- An index on a boolean or low-cardinality column (e.g., `status IN ('active','inactive')`) may be ignored by the planner.
- Index selectivity = `COUNT(DISTINCT col) / COUNT(*)`. Aim for > 0.1 before indexing.

**N+1 query pattern:**
- Symptom: application executes hundreds of nearly identical queries differing only by a single ID.
- Fix: rewrite as a single `SELECT ... WHERE id = ANY($1)` (Postgres) or `SELECT ... WHERE id IN (...)` (MySQL) and fetch all rows at once, or use ORM eager loading (Django: `select_related`/`prefetch_related`; Rails: `includes`; Hibernate: `JOIN FETCH`).

**Deadlock:**
- PostgreSQL: check `pg_locks` and the server log for `deadlock detected`.
- MySQL: `SHOW ENGINE INNODB STATUS\G` — look for the `LATEST DETECTED DEADLOCK` section.
- Fix pattern: ensure all transactions acquire locks in the same order; use `SELECT ... FOR UPDATE SKIP LOCKED` for queue-style workloads.

### 3. Design the Index

**Basic B-tree index:**
```sql
CREATE INDEX CONCURRENTLY idx_orders_user_created
  ON orders (user_id, created_at DESC);
```
Use `CONCURRENTLY` (Postgres) to avoid table lock on production.

**Covering index** (avoids heap fetch entirely):
```sql
-- Query: SELECT status, total FROM orders WHERE user_id = $1 AND created_at > $2
CREATE INDEX idx_orders_covering
  ON orders (user_id, created_at DESC)
  INCLUDE (status, total);  -- Postgres 11+
```
In MySQL, covering indexes are standard B-trees — include all SELECT and WHERE columns.

**Partial index** (index only rows matching a condition):
```sql
CREATE INDEX idx_orders_pending
  ON orders (created_at)
  WHERE status = 'pending';
```

**GIN index for full-text / JSONB (Postgres):**
```sql
CREATE INDEX idx_docs_fts ON documents USING gin(to_tsvector('english', body));
CREATE INDEX idx_meta_gin ON products USING gin(metadata);  -- for JSONB @> queries
```

### 4. Engine-Specific Differences

| Feature | PostgreSQL | MySQL 8.0 |
|---|---|---|
| EXPLAIN actual stats | `EXPLAIN ANALYZE` | `EXPLAIN ANALYZE` (8.0+) |
| Concurrent index build | `CREATE INDEX CONCURRENTLY` | Online DDL (default) |
| Covering index syntax | `INCLUDE (cols)` | All columns in index |
| JSON indexing | GIN on JSONB | `JSON_EXTRACT` + generated column + index |
| Full-text search | `tsvector` + GIN | `FULLTEXT` index + `MATCH AGAINST` |
| Skip locked | `SELECT FOR UPDATE SKIP LOCKED` | `SELECT FOR UPDATE SKIP LOCKED` (8.0+) |
| Materialized views | Native | Not native; use a table + scheduled refresh |

### 5. Deliver the Output

Provide:
1. Annotated execution plan (highlight the slow node).
2. Root cause diagnosis (1–2 sentences).
3. `CREATE INDEX` statement or query rewrite (with `EXPLAIN` output showing improvement if possible).
4. `EXPLAIN ANALYZE` command to verify the fix.
5. Any follow-up: statistics refresh, application-level N+1 fix, connection pool settings.

### 6. Advanced Query Patterns

**CTE materialization (PostgreSQL 12+):** By default, CTEs in Postgres 12+ are not materialized — the planner can inline them like a subquery. Force materialization with `WITH cte AS MATERIALIZED (...)` when the CTE is expensive and referenced multiple times; use `NOT MATERIALIZED` to allow inlining when the planner is over-estimating CTE cost. Check `EXPLAIN` to see whether the CTE appears as a separate node or is inlined.

**Partitioned table optimization:** Always include the partition key in `WHERE` clauses so the planner performs partition pruning (skips irrelevant partitions). Verify pruning with `EXPLAIN` — look for `Append` nodes that list only the relevant child partitions. Create indexes on each partition separately; a global index on the parent table is not available in PostgreSQL range/list partitioning. Avoid `OR` conditions across the partition key — they suppress pruning.

**Replica vs. primary plan divergence:** Read replicas may have stale statistics (last `ANALYZE` ran on the primary; replica lag delays propagation). A query that runs fast on the primary can pick a bad plan on the replica. Run `ANALYZE` on the replica directly, or check `pg_stat_user_tables.last_analyze` per replica. For critical read paths, force a plan with `pg_hint_plan` or promote the replica's statistics refresh schedule.

## Edge Cases

**1. Statistics are stale — planner chooses a bad plan.** If estimated rows diverge wildly from actual rows, run `ANALYZE <table>` (or `VACUUM ANALYZE` to also reclaim dead tuples). For tables with highly skewed distributions, use `CREATE STATISTICS` (Postgres 10+) to capture column correlations.

**2. Index exists but is not used.** The planner may skip a valid index if: (a) the table is small enough that a seq scan is cheaper, (b) the query uses a function on the indexed column (`WHERE LOWER(email) = ...` bypasses a plain index — use a functional index: `CREATE INDEX ON users (LOWER(email))`), or (c) the index has bloat — `REINDEX CONCURRENTLY` to rebuild it.

**3. Query is fast in isolation but slow under concurrency.** Check for lock contention: `pg_stat_activity` + `pg_locks` join, or `SHOW PROCESSLIST` in MySQL. Solutions: shorter transactions, optimistic locking, row-level vs. table-level locks, or `SKIP LOCKED` queue patterns.
