---
name: taskorchestrator
description: Designs and implements asynchronous task queues, distributed workflows, and worker orchestration systems. Use when asked to build job queues, implement background workers, design saga workflows, handle retry logic, or configure dead-letter queues with Celery, BullMQ, or Temporal.
---

# TaskOrchestrator

## Overview

Designs production-grade task orchestration systems using Celery (Python), BullMQ (Node.js), or Temporal (polyglot). Covers queue topology, worker concurrency, retry strategies with exponential backoff, dead-letter queues, idempotency, saga orchestration, and backpressure. Every design decision is justified against the specific failure mode it addresses.

## Workflow

### 1. Tool Selection

Choose the orchestration tool based on the workload profile:

| Tool | Language | Best For | Avoid When |
|------|----------|----------|------------|
| **Celery** | Python | High-throughput task queues, ML pipelines, Django/Flask integration | Long-running workflows with complex state; use Temporal instead |
| **BullMQ** | Node.js/TypeScript | Job queues with Redis backend, UI dashboard (Bull Board), rate limiting | Large Python teams; missing native workflow orchestration |
| **Temporal** | Python/Go/Java/TS | Long-running workflows, saga orchestration, durable execution with replay | Simple fire-and-forget tasks; adds operational overhead |
| **Celery + Kombu** | Python | When broker flexibility needed (RabbitMQ, SQS, Redis) | |
| **AWS SQS + Lambda** | Any | Serverless, event-driven, AWS-native; no infra to manage | Tasks > 15 min, complex orchestration logic |
| **Inngest / Trigger.dev** | TypeScript | Serverless-first Node.js workflows with built-in retries | Non-TypeScript stacks |

### 2. Queue Topology Design

Design queues before writing code:

```
Priority queues: critical > high > default > low
  - critical: payment processing, auth tokens
  - high: user-triggered actions (export, import)
  - default: background enrichment, notifications
  - low: analytics, cleanup, maintenance tasks

Dead-letter queues: every queue has a corresponding DLQ
  - orders.queue → orders.dlq
  - emails.queue → emails.dlq
```

**Celery:** Use `task_routes` to map task name patterns to queue names. Set `x-max-priority: 10` on the critical queue.

**BullMQ:**
```typescript
const paymentQueue = new Queue('payments', {
  connection: redis,
  defaultJobOptions: { attempts: 5, backoff: { type: 'exponential', delay: 2000 },
    removeOnComplete: { count: 1000 }, removeOnFail: { count: 5000 } }
});
```

### 3. Retry Strategy with Exponential Backoff

Use `retry_delay = min(base * 2^attempt + jitter, max_delay)`. Never fixed-interval retries.

**Celery:** `@celery_app.task(retry_backoff=True, retry_backoff_max=600, retry_jitter=True, max_retries=5)`. Raise `self.reject(requeue=False)` for permanent errors (invalid card, validation failure).

**Temporal:** Configure `RetryPolicy(initial_interval=2s, backoff_coefficient=2.0, maximum_attempts=5, non_retryable_error_types=["PermanentPaymentError"])` on `execute_activity`.

Distinguish retryable (network, 429, 5xx) from non-retryable (validation, 4xx, business rule violations).

### 4. Idempotency Keys

Every task that produces side effects must be idempotent:

```python
# Pattern: idempotency key stored in DB with unique constraint
def send_email_idempotent(email_id: str, recipient: str, subject: str):
    idempotency_key = f"email:{email_id}:{recipient}"

    with db.transaction():
        # Attempt insert; if it already exists, this email was already sent
        try:
            db.execute(
                "INSERT INTO processed_tasks (idempotency_key, processed_at) VALUES (?, NOW())",
                (idempotency_key,)
            )
        except UniqueConstraintError:
            logger.info(f"Task already processed: {idempotency_key}")
            return  # idempotent no-op

        # Only runs if insert succeeded (first time)
        email_service.send(recipient, subject)
```

Use UUID v4 or content-based hash as idempotency key. Store in Redis with TTL for short-lived tasks, or in a DB table for audit trail requirements.

### 5. Dead-Letter Queue Handling

DLQs catch tasks that exhausted all retries. Never leave DLQs unmonitored:
1. **Alert**: when DLQ depth > threshold (e.g., > 10 messages in `payments.dlq`).
2. **Inspect**: Log task ID, queue, attempt count, last error, timestamp when routing to DLQ.
3. **Reprocess**: fix root cause first, then replay via `queue.retryJobs()` (BullMQ) or re-queue (Celery).
4. **Retention**: Keep DLQ messages 14 days minimum.

```python
# Celery dead-letter with RabbitMQ
Queue('default', queue_arguments={
    'x-dead-letter-exchange': 'dlx',
    'x-dead-letter-routing-key': 'default.dlq',
})
```

### 6. Backpressure

- **Celery**: `worker_prefetch_multiplier=1` prevents pre-fetching excess tasks. `task_acks_late=True` prevents loss on worker crash.
- **BullMQ**: Set `concurrency` and `limiter: { max: 100, duration: 60000 }` on the Worker.
- **Temporal**: `WorkerOptions.max_concurrent_activity_task_executions` limits parallelism. Use `workflow.pause()` if the downstream is unhealthy.

### 7. Monitoring and Observability

Key metrics per queue: task throughput (tasks/sec), queue depth (lag > 5 min = alert for high-priority), error rate (> 1% = alert on critical queues), worker saturation.

```python
@task_failure.connect
def on_task_failure(task_id, exception, sender, **kwargs):
    metrics.increment('celery.task.failure', tags=[f'task:{sender.name}'])
    logger.error("Task failed", extra={"task_id": task_id, "error": str(exception)})
```

Use **Flower** (Celery) or **Bull Board** (BullMQ) for dashboards. Temporal Cloud provides built-in workflow visibility.

## Additional Patterns

**Temporal determinism requirement:** Temporal workflows are replayed from event history to resume after crashes. This means workflow code must be fully deterministic: never call `datetime.now()`, `random.random()`, `uuid4()`, or any I/O (DB, HTTP, filesystem) directly in the workflow body. All non-deterministic operations must be placed in activities. Use `workflow.now()` for current time and `workflow.uuid4()` for IDs inside workflows.

## Edge Cases

**Long-running tasks and worker restarts**: For tasks that run > 5 minutes, use Temporal's durable execution (workflows survive worker restarts via event sourcing replay) or implement a heartbeat mechanism in Celery (`self.update_state(state='PROGRESS')` + monitor for stale heartbeats). Never run long tasks in a queue designed for fast tasks — separate pools.

**Task deduplication**: Prevent the same logical task from being enqueued twice (e.g., double-click on "Export" button). Implement deduplication at enqueue time: check for an in-progress job with the same key before adding to the queue. BullMQ supports `jobId` deduplication natively. For Celery, use Redis `SET NX` with TTL as a distributed lock before calling `.apply_async()`.

**Poison pill messages**: A malformed message that always causes a task to crash will cycle through retries and fill the DLQ. Detect by inspecting DLQ for repeated task signatures. Add a payload validation step at the start of every task handler that raises a non-retryable exception on schema validation failure — this routes malformed messages to DLQ immediately without wasting retry attempts.
