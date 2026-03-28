---
name: dataweaver
description: Designs normalized database schemas (1NF-3NF), writes optimized SQL with EXPLAIN ANALYZE, and manages reversible migrations with Flyway, Alembic, or Prisma Migrate. Use when a user asks for database design, schema changes, query optimization, or migration scripts.
---

# DataWeaver

## Overview

Design schemas that survive real-world requirements, write queries that the query planner can execute efficiently, and produce reversible migration files that can be safely deployed and rolled back.

## Workflow

### 1. Understand the Domain

Before designing tables, extract:
- **Entities**: the nouns (users, orders, products)
- **Relationships**: one-to-one, one-to-many, many-to-many
- **Cardinality and access patterns**: how data is read most often dictates index strategy
- **Volume expectations**: millions of rows changes index and partitioning choices

Sketch an ER diagram (text is fine):
```
users (1) ──< orders (many)
orders (many) >──< products (many) [via order_items]
```

### 2. Apply Normalization (1NF → 3NF)

**1NF**: Eliminate repeating groups and multi-valued cells.
- Bad: `tags = "python,sql,docker"` → Good: `tags` table with FK to entity

**2NF**: Eliminate partial dependencies (applies to composite PKs).
- Bad: `order_items(order_id, product_id, product_name)` — product_name depends only on product_id
- Good: move product_name to `products` table

**3NF**: Eliminate transitive dependencies.
- Bad: `orders(order_id, customer_id, customer_city)` — customer_city depends on customer_id, not order_id
- Good: customer_city belongs in `customers` table

Denormalize deliberately and document it when read performance requires it (e.g., pre-aggregated reporting tables).

### 3. Define Schema with Constraints

Always define:
- Primary keys (prefer surrogate `BIGSERIAL`/`UUID` over natural keys unless the domain is truly stable)
- Foreign keys with explicit `ON DELETE` / `ON UPDATE` behavior
- NOT NULL where the value is always required
- CHECK constraints for domain rules
- Unique constraints on natural business keys

```sql
CREATE TABLE orders (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    status      TEXT NOT NULL CHECK (status IN ('pending','confirmed','shipped','cancelled')),
    total_cents BIGINT NOT NULL CHECK (total_cents >= 0),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status  ON orders(status) WHERE status != 'cancelled';
```

Store money as integer cents or use `NUMERIC(12,2)`. Never use `FLOAT` for currency.
Store timestamps as `TIMESTAMPTZ` (UTC-aware), never `TIMESTAMP`. A `TIMESTAMP` column stores no timezone info — when a client in a non-UTC timezone writes a value, Postgres stores the local time literally, causing reads from UTC clients to return the wrong instant. `TIMESTAMPTZ` always normalizes to UTC on write and converts back on read.

### 4. Optimize Queries with EXPLAIN ANALYZE

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT o.id, u.email, o.total_cents
FROM orders o
JOIN users u ON u.id = o.user_id
WHERE o.status = 'pending'
ORDER BY o.created_at DESC
LIMIT 50;
```

Read the output:
- **Seq Scan** on a large table → needs an index
- **Hash Join** is fine; **Nested Loop** with large outer → may need a better index
- **Rows** estimate vs actual: large divergence → run `ANALYZE table_name` to refresh statistics
- **Buffers: hit** vs **read**: high disk reads → consider caching or better index coverage

Target: all hot queries use **Index Scan** or **Index Only Scan**.

### 5. Write Reversible Migrations

Every migration must have an `up` (apply) and `down` (rollback). Never drop columns in the same migration that removes their references — separate into multiple deployments.

**Alembic (Python/SQLAlchemy):**
```python
# alembic/versions/20240115_add_orders_index.py
def upgrade():
    op.create_index('idx_orders_user_id', 'orders', ['user_id'])

def downgrade():
    op.drop_index('idx_orders_user_id', table_name='orders')
```

**Flyway (Java/any):**
```sql
-- V20240115__add_orders_index.sql
CREATE INDEX CONCURRENTLY idx_orders_user_id ON orders(user_id);
```
```sql
-- U20240115__add_orders_index.sql  (undo migration)
DROP INDEX CONCURRENTLY idx_orders_user_id;
```
Use `CREATE INDEX CONCURRENTLY` in Postgres to avoid locking the table in production.

**Prisma Migrate:**
```bash
prisma migrate dev --name add_orders_index
# Generates migration SQL + updates schema.prisma
# Rollback: prisma migrate resolve --rolled-back <migration-name>
```

**Prisma schema drift**: If the database was modified outside of Prisma Migrate (e.g., manual DDL), migrations will fail with a "drift detected" error. Diagnose with `prisma migrate diff --from-schema-datamodel prisma/schema.prisma --to-url $DATABASE_URL`. To baseline an existing database: `prisma migrate resolve --applied <migration-name>` marks it as already applied without running it.

### 6. Safe Schema Change Patterns

For zero-downtime deployments:

| Change | Safe approach |
|--------|--------------|
| Add nullable column | Add directly — no lock |
| Add NOT NULL column | Add nullable → backfill (`UPDATE table SET col = default WHERE col IS NULL`) → `ALTER TABLE ADD CONSTRAINT col_not_null CHECK (col IS NOT NULL) NOT VALID` → `VALIDATE CONSTRAINT` (validates without full lock in Postgres 12+) |
| Rename column | Add new → dual-write → migrate reads → drop old |
| Drop column | Remove app references first → deploy → then drop |
| Add index | `CREATE INDEX CONCURRENTLY` |
| Resize VARCHAR | In Postgres, widening is instant; narrowing requires a table rewrite |

## Output Format

Provide:
1. ER diagram (text or Mermaid `erDiagram`)
2. `CREATE TABLE` DDL with all constraints
3. Index definitions with justification
4. Migration files (up + down) for any changes to existing schemas
5. EXPLAIN ANALYZE output interpretation for any query being optimized

## Edge Cases

**Many-to-many with attributes**: A join table like `order_items` carries its own data (`quantity`, `unit_price`). It is a first-class entity, not a pure junction table — give it its own PK and audit columns.

**UUID vs BIGSERIAL**: UUIDs (`gen_random_uuid()`) enable distributed ID generation but cause index fragmentation in Postgres B-tree indexes. Prefer `ULID` or `UUIDv7` (time-ordered) for write-heavy tables. Use `BIGSERIAL` for single-database setups.

**Recursive/hierarchical data**: For trees (categories, org charts), use the `ltree` Postgres extension or an adjacency list with recursive CTEs (`WITH RECURSIVE`). Materialized path strings are fast to read but expensive to restructure.
