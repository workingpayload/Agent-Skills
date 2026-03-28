---
name: servicesplitter
description: Decomposes monolithic applications into microservices using DDD bounded contexts, event storming, and the strangler fig pattern. Use when asked to split a monolith, design microservice boundaries, define service contracts, or implement saga/circuit breaker patterns.
---

# ServiceSplitter

## Overview

Guides microservice decomposition using Domain-Driven Design (DDD) bounded contexts, event storming workshops, and incremental extraction via the strangler fig pattern. Produces service boundary maps, API contracts, event schemas, and resilience patterns (sagas, circuit breakers) — grounded in concrete architecture decisions rather than abstract principles.

## Workflow

### 1. Domain Discovery via Event Storming

Before drawing service boundaries, map the domain:

1. **Big Picture Event Storming**: List all domain events (past tense, orange stickies) across the full system: `OrderPlaced`, `PaymentProcessed`, `InventoryReserved`, `ShipmentDispatched`.
2. **Identify commands and actors**: What triggers each event? Who initiates it?
3. **Find aggregates**: Group events that share a consistency boundary (transactional consistency requirement).
4. **Spot pivot events**: Events that cross team/subdomain boundaries are natural seams for service cuts.
5. **Define bounded contexts**: Each context has its own ubiquitous language. The same word means different things in different contexts (e.g., "Customer" in Sales vs. Support vs. Billing).

Output: Context map diagram showing bounded contexts and their relationships (Partnership, Customer-Supplier, Conformist, Anti-Corruption Layer, Open Host Service).

### 2. Service Boundary Identification

Apply these heuristics to validate candidate boundaries:

| Criterion | Good Boundary Signal |
|-----------|---------------------|
| Business capability | Service owns one cohesive business capability end-to-end |
| Data ownership | Service is the single writer for its data; no direct DB sharing |
| Change frequency | Service deploys independently without coordinating other teams |
| Team alignment | Matches Conway's Law — one team owns one service |
| Transaction boundary | Avoids distributed transactions; uses eventual consistency |

Red flags: two services that always deploy together, services that call each other synchronously in a chain deeper than 2 hops, shared databases.

### 3. Strangler Fig Extraction Pattern

For incremental extraction from a monolith:

1. **Identify the seam**: Pick a bounded context with clear in/out HTTP or event boundaries.
2. **Route at the edge**: Place an API gateway or reverse proxy (Nginx, AWS API Gateway, Kong) in front of the monolith. All traffic still flows through.
3. **Implement the new service**: Build the extracted service in its own repo/deployment unit with its own database.
4. **Feature flag traffic routing**: Gradually route traffic to the new service (1% → 10% → 100%) using feature flags or weighted routing rules.
5. **Delete the monolith code**: Only after the new service handles 100% of traffic and is stable. Remove the dead code path from the monolith.
6. **Repeat**: Move to the next bounded context.

Never do a Big Bang rewrite. Extract one context at a time.

### 4. API Contracts

Define contracts before implementation using OpenAPI 3.1 or AsyncAPI 2.x:

**Synchronous (REST/gRPC)**:
```yaml
# openapi: 3.1.0
paths:
  /orders/{orderId}:
    get:
      operationId: getOrder
      parameters:
        - name: orderId
          in: path
          required: true
          schema: { type: string, format: uuid }
      responses:
        '200':
          content:
            application/json:
              schema: { $ref: '#/components/schemas/Order' }
        '404':
          content:
            application/json:
              schema: { $ref: '#/components/schemas/ProblemDetail' }
```

**Asynchronous (events)**:
Use AsyncAPI to document event schemas. Publish Avro or JSON Schema to a schema registry (Confluent Schema Registry, AWS Glue Schema Registry) for schema evolution governance.

Contract testing: use **Pact** (consumer-driven contract tests) to verify service contracts in CI without running the full stack.

### 5. Saga Pattern for Distributed Transactions

Use sagas for multi-service business transactions that span consistency boundaries.

**Choreography saga** (event-driven, no central coordinator):
- Each service listens for events and publishes compensating events on failure.
- Simple for 2–3 services. Difficult to debug as complexity grows.
- Use Kafka or RabbitMQ as the event bus.

**Orchestration saga** (central coordinator, recommended for complex flows):
- Use **Temporal** (`io.temporal.workflow`) or **AWS Step Functions** as the orchestrator.
- Coordinator calls services and handles compensation:

```python
# Temporal workflow example
@workflow.defn
class OrderFulfillmentWorkflow:
    @workflow.run
    async def run(self, order_id: str) -> str:
        try:
            await workflow.execute_activity(reserve_inventory, order_id)
            await workflow.execute_activity(charge_payment, order_id)
            await workflow.execute_activity(ship_order, order_id)
        except ActivityError:
            await workflow.execute_activity(cancel_inventory_reservation, order_id)
            await workflow.execute_activity(refund_payment, order_id)
            raise
```

Each activity must be **idempotent** — implement idempotency keys using a UUID stored in the DB with a unique constraint.

### 6. Circuit Breakers and Resilience

Implement circuit breakers on all synchronous inter-service calls:

- **Resilience4j** (Java): `@CircuitBreaker(name = "inventoryService", fallbackMethod = "fallback")`
- **resilience4j-js** or **Polly** (.NET) for other stacks
- **Istio** service mesh: configure circuit breaking at the infrastructure level via `DestinationRule`

Circuit breaker states: CLOSED (normal) → OPEN (failing, reject calls) → HALF_OPEN (probe recovery).
Configure: `failureRateThreshold=50`, `waitDurationInOpenState=30s`, `slidingWindowSize=10`.

Add **bulkheads** (thread pool isolation) to prevent one slow downstream from exhausting shared thread pools.

### 7. Output Artifacts

Produce:
1. **Context map** (Mermaid diagram): bounded contexts with relationship types.
2. **Service decomposition table**: service name, owned capabilities, owned data, APIs exposed, events published/consumed.
3. **Strangler fig migration plan**: ordered list of extraction phases with rollback strategy per phase.
4. **API contracts**: OpenAPI stubs for synchronous APIs, AsyncAPI for event schemas.
5. **Saga design**: sequence diagram showing happy path and compensation flows.
6. **ADR (Architecture Decision Record)**: document the decomposition rationale and rejected alternatives.

## Additional Patterns

**Network latency cost of extraction:** Each synchronous inter-service call adds 1–10ms of network overhead. After extracting a service, profile call chains: if ServiceA calls ServiceB synchronously on every request, co-locate them or introduce an async messaging pattern (publish event, consume asynchronously). Cache stable reference data (product catalog, user profile) in the calling service with a short TTL to eliminate round trips for read-heavy paths.

**Event schema backward/forward compatibility:** Follow these rules for Avro/JSON Schema event evolution: (1) adding optional fields is backward compatible — consumers that don't know the field ignore it; (2) removing or renaming fields is breaking — use a deprecation period with both old and new field present; (3) changing a field's type is always breaking. Register all schemas in a schema registry and enforce compatibility mode (`BACKWARD` or `FULL`) in CI before merging schema changes.

**God table physical splitting:** When a single table serves multiple bounded contexts (e.g., a `users` table with columns from Auth, Profile, Billing, and Analytics), split it physically by creating new tables per context with the same primary key, backfilling data, and then migrating reads/writes service by service using the strangler fig pattern. Use database views during transition to avoid a flag day. Do not split without first confirming each context's column set via query log analysis.

## Edge Cases

**Shared data without clear ownership**: When multiple services need the same data (e.g., product catalog), designate one service as the system of record and expose a read API or publish events. Never allow two services to write to the same table. Use the CQRS pattern to maintain read-optimized projections in downstream services.

**Distributed transactions you cannot avoid**: If strong consistency is truly required (e.g., financial double-entry bookkeeping), do not split those aggregates across services. Keep them in the same service behind a single ACID transaction. Distributed saga compensation is eventually consistent — not a substitute for ACID where correctness requires it.

**Service mesh vs. library-based resilience**: Istio/Linkerd handle circuit breaking and retries transparently but add operational complexity. For teams new to microservices, start with library-based resilience (Resilience4j, Polly) and migrate to a service mesh only when the per-service configuration overhead becomes prohibitive.
