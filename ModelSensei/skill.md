---
name: modelsensei
description: Designs domain-driven data models using DDD aggregates and value objects, produces ORM mappings for SQLAlchemy/Prisma/ActiveRecord, prevents N+1 queries, and generates database migration files. Use when a user needs help with data modeling, ORM schema design, query optimization, or database migrations.
---

# ModelSensei

## Overview

Designs data models using Domain-Driven Design (DDD) tactical patterns — aggregates, entities, value objects, repositories — then maps them to ORM schemas (SQLAlchemy, Prisma, ActiveRecord). Identifies N+1 problems and generates migration files.

## Workflow

### 1. Model the Domain First (DDD Tactical Patterns)

- **Aggregate Root:** Entry point for a cluster of related objects. All external references go through the root.
- **Entity:** Has unique identity that persists over time (`Order`, `User`).
- **Value Object:** Defined by attributes, no identity, immutable (`Money`, `Address`).

```typescript
class Money {  // Value Object
  constructor(readonly amount: number, readonly currency: 'USD' | 'EUR') {
    if (amount < 0) throw new DomainError('Amount cannot be negative');
  }
  add(other: Money): Money {
    if (other.currency !== this.currency) throw new DomainError('Currency mismatch');
    return new Money(this.amount + other.amount, this.currency);
  }
}
class Order {  // Aggregate Root
  private _items: OrderItem[] = [];
  addItem(item: OrderItem): void {
    if (this._status !== 'draft') throw new DomainError('Cannot modify non-draft order');
    this._items.push(item);
  }
}
```

Aggregate rules: only the root has a repository; external aggregates reference each other by ID only; keep aggregates small.

### 2. Map to ORM Schema

**Prisma:**
```prisma
model Order {
  id          String      @id @default(uuid())
  customerId  String
  customer    Customer    @relation(fields: [customerId], references: [id])
  status      OrderStatus @default(DRAFT)
  totalAmount Decimal     @db.Decimal(12, 2)
  items       OrderItem[]
  createdAt   DateTime    @default(now())
  updatedAt   DateTime    @updatedAt
  @@index([customerId, status])
}
```

**SQLAlchemy:** Use `selectinload` for collections, `joinedload` for single relations. **ActiveRecord:** Use `includes(:items, :customer)`.

### 3. Prevent N+1 Queries

Detect N+1 by finding queries inside loops. Fix with eager loading:
```typescript
// Prisma fix — 2 queries instead of 1+N
const orders = await prisma.order.findMany({
  include: { items: true, customer: { select: { id: true, name: true } } },
  where: { status: 'pending' }, take: 50,
});
```
Rule: `joinedload`/`joins` for to-one; `selectinload`/`includes` for to-many.

### 4. Generate Migrations

```bash
npx prisma migrate dev --name add_order_currency_index
alembic revision --autogenerate -m "add_order_currency_index"
rails generate migration AddCurrencyIndexToOrders
```

Migration rules: always provide a `downgrade`/`down` method; never drop a column in the same migration that removes it from code; large table index additions must use `CONCURRENTLY` (Postgres).

**Zero-downtime NOT NULL column addition on large tables:** Never add `NOT NULL` with a `DEFAULT` in a single migration on a large table — it locks the table for the full backfill. Instead:
1. Add the column as nullable: `ALTER TABLE orders ADD COLUMN notes TEXT`.
2. Backfill in batches: `UPDATE orders SET notes = '' WHERE id BETWEEN $1 AND $2`.
3. Add the `NOT NULL` constraint using `NOT VALID` to skip historical rows: `ALTER TABLE orders ADD CONSTRAINT orders_notes_not_null CHECK (notes IS NOT NULL) NOT VALID`.
4. Validate in a separate transaction: `ALTER TABLE orders VALIDATE CONSTRAINT orders_notes_not_null`.

### 5. Hierarchical Data Modeling

Choose the right pattern for tree/hierarchy data:

| Pattern | Best for | Recursive CTE? |
|---|---|---|
| Adjacency list (`parent_id`) | Simple, shallow trees; easy updates | Yes (`WITH RECURSIVE`) |
| Closure table | Fast ancestor/descendant queries | No |
| Nested sets (left/right) | Frequent reads, infrequent writes | No |

```sql
-- Adjacency list with recursive CTE (Postgres)
WITH RECURSIVE tree AS (
  SELECT id, name, parent_id, 0 AS depth FROM categories WHERE parent_id IS NULL
  UNION ALL
  SELECT c.id, c.name, c.parent_id, t.depth + 1
  FROM categories c JOIN tree t ON c.parent_id = t.id
)
SELECT * FROM tree ORDER BY depth, name;
```

### 6. Outbox Pattern for Reliable Domain Events

Never publish domain events directly inside a transaction — the event may fire even if the DB commit fails. Use the outbox pattern:

1. Within the same DB transaction that modifies the aggregate, insert a row into an `outbox_events` table.
2. A background poller (or Debezium CDC) reads unpublished outbox rows and publishes them to the message broker.
3. Mark rows as `published_at = NOW()` after successful broker acknowledgement.

```sql
CREATE TABLE outbox_events (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  aggregate   TEXT NOT NULL,
  event_type  TEXT NOT NULL,
  payload     JSONB NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  published_at TIMESTAMPTZ
);
```

## Output Format

Deliver: domain model (plain classes, no ORM dependency), ORM schema, migration file(s) with up/down, index strategy justification, and N+1 risks with fixes.

## Edge Cases

**Value objects in relational DBs:** Map as embedded columns on the owning entity (`money_amount`, `money_currency`), not separate tables. Only extract to a table if the value object is queried independently.

**Soft delete:** Add a partial unique index to exclude soft-deleted rows: `CREATE UNIQUE INDEX ON users (email) WHERE deleted_at IS NULL`.

**Oversized aggregates:** If an `Order` could have thousands of `OrderItem` rows, split into a separate aggregate and enforce cross-aggregate invariants asynchronously via domain events.
