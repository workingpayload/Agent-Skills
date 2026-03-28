---
name: architekt-ai
description: Designs scalable system architectures using C4 model diagrams, Architecture Decision Records (ADRs), CQRS, event sourcing, and microservices patterns. Use when a user needs to design a new system, evaluate trade-offs between architectural styles, document decisions, or review an existing architecture for scalability and resilience.
---

# Architekt AI

## Domain Scope

System architecture design, architectural pattern selection (microservices, monolith, CQRS, event sourcing, saga), non-functional requirements (NFRs) elicitation, C4 model diagrams, Architecture Decision Records, distributed systems trade-offs (CAP theorem, BASE vs. ACID), and technology stack selection.

---

## Workflow

### 1. Elicit Non-Functional Requirements (NFRs)
Before designing anything, gather:
- **Availability**: target SLA (99.9% = 8.7h/year downtime; 99.99% = 52min/year)
- **Throughput**: peak requests/sec, data ingestion rate (events/sec, MB/s)
- **Latency**: p50/p95/p99 targets (e.g., "p99 < 200ms for reads")
- **Consistency**: strong vs. eventual — which operations require linearizability?
- **Durability**: RPO (max data loss), RTO (max recovery time)
- **Scale**: current users, 12-month growth projection, geographic distribution
- **Compliance**: GDPR, SOC2, HIPAA, PCI-DSS — data residency requirements
- **Team size & structure**: Conway's Law — architecture will mirror the org chart

### 2. Apply CAP Theorem to Data Tier Decisions
When choosing between consistency and availability during network partition:
- **CP systems** (HBase, Zookeeper, etcd): used for coordination, leader election, distributed locks. Accept unavailability over stale reads.
- **AP systems** (Cassandra, DynamoDB, CouchDB): used for user-facing data requiring high availability. Accept eventual consistency; design for conflict resolution (LWW, CRDTs, application-level merge).
- **CA systems** (traditional RDBMS, single-node): only valid in absence of network partition — not suitable for geo-distributed deployments.

### 3. Choose an Architectural Style

**Monolith first** if: team < 8 engineers, domain not yet fully understood, MVP phase. Prefer **modular monolith** (clear module boundaries, separate packages, enforced via ArchUnit or Dependency Cruiser) over a "big ball of mud".

**Microservices** when: teams own services independently, services have different scaling requirements, polyglot persistence is needed. Each service: owns its data store (no shared DB), communicates via versioned APIs or events, is independently deployable.

**CQRS (Command Query Responsibility Segregation)**:
- Separate write model (Commands → aggregate → event store) from read model (projections, denormalized read DB).
- Use when read and write throughput/shape requirements differ significantly.
- Implement with: Axon Framework (Java), EventStoreDB, or Kafka + PostgreSQL read model.

**Event Sourcing**:
- Store all state changes as an immutable sequence of events; current state = replay of events.
- Benefits: full audit log, temporal queries, easy event replay.
- Costs: eventual consistency for reads, snapshot strategy needed for large aggregates, schema evolution complexity.
- Do NOT use event sourcing just for audit logs — use CDC (Debezium) + an audit table instead if that's the only requirement.

**Saga Pattern** for distributed transactions:
- **Choreography**: each service publishes events; others react. Simple, no central coordinator. Risk: hard to track overall state.
- **Orchestration**: a saga orchestrator (state machine) sends commands and handles failures. Easier to reason about; single point of failure risk.

### 4. Design with the C4 Model
Produce diagrams at the appropriate level of detail:

**Level 1 — System Context**
- Boxes: the system being designed, external users, external systems it integrates with.
- Focus: what the system does and who uses it.

**Level 2 — Container**
- Boxes: web app, API server, worker, database, message broker, CDN.
- Arrows: synchronous (REST/gRPC) vs. asynchronous (Kafka/RabbitMQ) with protocol labels.

**Level 3 — Component** (within a container)
- Boxes: controllers, services, repositories, domain aggregates.
- Show dependency direction; ensure it aligns with layered/hexagonal architecture rules.

**Level 4 — Code** (optional; only for complex aggregates or algorithms)
- Class/sequence diagrams for critical paths.

Use Mermaid or PlantUML for text-based C4 diagrams in ADRs.

### 5. Write Architecture Decision Records (ADRs)
Format (MADR — Markdown Architectural Decision Records):
```markdown
# ADR-0001: Use PostgreSQL with JSONB for product catalog

## Status
Accepted

## Context
The product catalog requires flexible schema for varying product attributes
across categories, combined with strong transactional guarantees for inventory.

## Decision
Use PostgreSQL with JSONB columns for attribute storage rather than a document
database, keeping relational guarantees for inventory and order tables.

## Consequences
+ Single database reduces operational complexity.
+ JSONB GIN indexes provide fast attribute queries.
- Schema validation must be enforced at the application layer.
- JSONB queries are less ergonomic than native document DB queries.

## Alternatives Considered
- MongoDB: rejected due to lack of multi-document ACID transactions (pre-4.0).
- Hybrid (PostgreSQL + MongoDB): rejected due to two-DB operational overhead.
```
Store ADRs in `/docs/adr/` numbered sequentially. Never delete — update status to "Superseded by ADR-XXXX".

### 6. Zero-Downtime Database Migrations
Use the **expand/contract pattern** to avoid locking tables during live traffic:
1. **Expand**: add new column/table alongside old one (both writes go to old + new).
2. **Migrate**: backfill data in batches; use `gh-ost` (GitHub Online Schema Change for MySQL) or `pg_repack` (PostgreSQL) to rebuild tables without long locks.
3. **Contract**: once all reads use the new column, drop the old one in a separate release.

Never run `ALTER TABLE … ADD COLUMN NOT NULL` without a default on a large table in production — it locks the table. Always add columns as nullable first, then add the constraint after backfill.

**CDN Caching Gotchas**
- The `Vary` header tells CDNs to cache separate copies per header value (e.g., `Vary: Accept-Encoding, Accept-Language`). Including `Vary: Cookie` or `Vary: Authorization` effectively disables CDN caching — use surrogate keys or cache bypass rules instead.
- For authenticated responses: set `Cache-Control: private, no-store` to prevent CDN/proxy caching. For public cacheable resources: `Cache-Control: public, max-age=3600, s-maxage=86400` (browser vs. CDN TTLs differ). Always set `Surrogate-Control` (Fastly/Varnish) or `CDN-Cache-Control` separately when you need different TTLs at the edge vs. the browser.

### 7. Address Resilience and Failure Modes
- **Circuit breaker**: Resilience4j (Java), Polly (.NET), `pybreaker` (Python). Open after N failures, half-open after timeout.
- **Retry with exponential backoff + jitter**: base delay 100ms, max 30s, jitter ±25%.
- **Bulkhead**: isolate thread pools or connection pools per downstream service.
- **Timeout**: set at every network call. No unbounded blocking.
- **Dead Letter Queue (DLQ)**: for every message consumer. Alert on DLQ depth > 0.
- **Health checks**: `/health/live` (process alive) and `/health/ready` (dependencies healthy), consumed by load balancer and orchestrator (Kubernetes).

---

## Output Artifacts

- C4 Level 1 + Level 2 diagrams (Mermaid)
- ADR document(s) for each significant decision
- NFR table with current targets and how the design meets them
- Data flow diagram for the critical path (happy path + failure path)
- Technology stack table with rationale and alternatives considered

---

## Edge Cases

1. **Premature microservices decomposition**: Splitting a monolith before understanding domain boundaries creates distributed monoliths — services that are tightly coupled and must be deployed together, gaining all the costs of microservices with none of the benefits. Apply Domain-Driven Design (DDD) bounded context analysis first. Use the Strangler Fig pattern to extract services incrementally from a working monolith.

2. **Event schema evolution in event sourcing**: Once events are written to the store they are immutable. When the event schema changes, old events cannot be rewritten. Implement upcasting (transform old event format to new at read time), or use schema registry (Confluent Schema Registry with Avro/Protobuf) with backward/forward compatibility rules. Never use `Object` or untyped JSON for events in production.

3. **CQRS read model consistency lag**: In CQRS, the read model is updated asynchronously after the command side commits. A client that writes then immediately reads may receive stale data. Options: (a) return the write result directly in the command response (sufficient for most UIs), (b) poll with a version token until the read model catches up, (c) use a synchronous projection for latency-sensitive reads at the cost of complexity. Document the chosen consistency contract in the API spec.
