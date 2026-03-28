---
name: stackwise
description: Advises on technology stack selection, evaluates library trade-offs, and produces Architecture Decision Records (ADRs). Use when asked to choose a framework, compare libraries, evaluate tech stack options, or document architectural decisions with rejected alternatives.
---

# StackWise

## Overview

Produces structured technology evaluations that account for team context, project constraints, and long-term maintainability. Output format is an Architecture Decision Record (ADR) with a scored evaluation rubric, library health metrics, and explicit documentation of rejected alternatives. No generic "it depends" answers — every recommendation is justified with concrete criteria.

## Workflow

### 1. Requirements Gathering

Before evaluating options, establish:

**Functional requirements**:
- What does the technology need to do? (e.g., "serve 10k req/s REST API", "render server-side HTML with dynamic data", "run ML inference on edge devices")
- What integrations are mandatory? (existing DBs, auth providers, cloud platform)
- What data/traffic scale is expected at launch and in 2 years?

**Non-functional constraints**:
- Team language/ecosystem familiarity (don't recommend Rust to a Python-only team without explicit buy-in)
- Deployment target: serverless, containers (Kubernetes), PaaS, edge runtime
- Licensing constraints: AGPL/GPL incompatibility with proprietary codebase?
- Compliance: HIPAA, PCI-DSS, GDPR — some require specific data handling capabilities
- Time to first production: weeks vs. months affects acceptable learning curve

**Team context**:
- Team size and experience level
- Existing stack to minimize cognitive overhead ("boring technology" preference)
- Open source vs. commercial support appetite

### 2. Evaluation Rubric

Score each candidate (1–5 per criterion) with weights adjusted to project context:

| Criterion | Weight (default) | Notes |
|-----------|-----------------|-------|
| Ecosystem maturity | 20% | Years in production, major adopters, LTS policy |
| Performance fit | 20% | Benchmarks relevant to the workload type |
| Developer experience | 15% | TypeScript types, documentation quality, error messages |
| Library health | 15% | See Section 3 |
| Operational complexity | 15% | Deployment, monitoring, debugging tooling |
| Community & support | 10% | GitHub stars trend, Stack Overflow activity, commercial support availability |
| Migration cost | 5% | Cost to switch away if the choice is wrong |

Weighted score = sum of (score × weight). Document numerical scores, not just opinions.

### 3. Library Health Metrics

For every candidate library, check:

| Metric | Tool / Source | Threshold |
|--------|--------------|-----------|
| Release recency | GitHub releases | Last release < 12 months |
| Issue response time | GitHub Insights | Median < 14 days |
| Open CVEs | `npm audit` / `pip-audit` / OSV.dev | Zero critical/high unpatched CVEs |
| npm weekly downloads | npmjs.com stats | > 100k/week for production dependency |
| PyPI download trend | pypistats.org | Stable or growing 6-month trend |
| Dependents count | GitHub "Used by" | Proxy for ecosystem lock-in risk |
| Bus factor | git log analysis | > 3 regular contributors |
| License | SPDX identifier | Compatible with project license (MIT/Apache-2.0 preferred) |

Flag libraries with: single maintainer, no releases in 18+ months, high CVE backlog, or license mismatch.

### 4. Technology-Specific Comparison Patterns

**Frontend framework selection** (React vs. Vue vs. Svelte vs. SolidJS):
- Evaluate: bundle size, SSR/SSG capabilities, TypeScript quality, ecosystem (component libraries, state management), hiring pool.
- Key differentiators: React = largest ecosystem; Svelte/Solid = smaller bundles; Vue = gentler learning curve.

**Backend framework selection** (Express vs. Fastify vs. NestJS vs. Hono for Node; FastAPI vs. Django vs. Flask for Python):
- Evaluate: throughput benchmarks (TechEmpower), built-in validation, OpenAPI generation, middleware ecosystem.
- Key differentiators: Fastify > Express on throughput; NestJS adds structure but heavier; FastAPI = auto-OpenAPI + async.

**Database selection** (PostgreSQL vs. MySQL vs. MongoDB vs. DynamoDB vs. CockroachDB):
- Evaluate: ACID guarantees, query flexibility, horizontal scaling model, managed cloud options.
- Default: PostgreSQL unless workload specifically requires document flexibility (MongoDB), global horizontal scale (CockroachDB/Spanner), or serverless cost model (DynamoDB).

**Caching layer** (Redis vs. Memcached vs. DragonflyDB):
- Redis: persistence, pub/sub, Lua scripting, cluster mode — default choice.
- Memcached: simpler, marginally faster for pure string cache — only if Redis features unneeded.
- DragonflyDB: Redis-compatible, multi-threaded, lower memory — evaluate if Redis memory cost is a bottleneck.

### 5. ADR Output Format

Produce every recommendation as an ADR:

```markdown
# ADR-001: API Framework Selection for Payment Service

## Status
Accepted | 2024-03-15

## Context
We are building a payment processing microservice in Python expected to handle
5,000 req/s. The team has strong Python experience. We need auto-generated OpenAPI
docs and async support for calling downstream payment gateways.

## Decision
Use **FastAPI** with **Uvicorn** (ASGI) as the API framework.

## Evaluation

| Criterion           | FastAPI (score) | Django REST (score) | Flask (score) |
|---------------------|----------------|---------------------|---------------|
| Ecosystem maturity  | 4              | 5                   | 5             |
| Performance fit     | 5              | 3                   | 3             |
| Developer experience| 5              | 4                   | 3             |
| Library health      | 5              | 5                   | 4             |
| Operational complexity| 4            | 3                   | 4             |
| **Weighted Total**  | **4.65**       | **3.90**            | **3.75**      |

## Rationale
FastAPI's native async support eliminates thread pool overhead when calling
payment gateway APIs (avg 200ms latency). Auto-generated OpenAPI schema removes
manual documentation maintenance. Pydantic v2 validation is 5–10x faster than
DRF serializers for our data shapes.

## Rejected Alternatives
- **Django REST Framework**: Excellent for CRUD APIs with ORM but sync-by-default
  adds unnecessary complexity for async-heavy workload. Migration to async views
  is incomplete as of Django 4.2.
- **Flask**: Too minimal; would require adding marshmallow/apispec manually for
  validation and docs. Higher integration maintenance cost.

## Consequences
- Team must learn FastAPI patterns (dependency injection, Pydantic models).
- Uvicorn + Gunicorn deployment is less familiar than Django's WSGI setup.
- Mitigation: 2-day internal workshop before sprint 1.
```

### 6. Avoid These Anti-Patterns

- Choosing a technology because it's trending on HN/X — evaluate against actual requirements.
- Recommending a rewrite from a working stack without quantifying the migration cost and business risk.
- Picking microservices/distributed architecture for a team of < 5 engineers — operational overhead outweighs benefits.
- Choosing unproven (< 1 year old, < 1.0 release) libraries for production critical paths.
- Ignoring the existing team's expertise — a 20% performance gain is not worth a 6-month ramp-up.

## Edge Cases

**Post-decision monitoring:** After a technology is adopted, schedule a review at 6 months and 12 months. Review triggers: library goes unmaintained (no releases in 12 months, maintainer announces EOL), critical unpatched CVE, major version breaking change, or team dissatisfaction score drops below threshold. Document the review criteria in the ADR's Consequences section so the team knows when to revisit.

**Compliance hard-blocking disqualifiers:** Certain choices are non-negotiable regardless of rubric score. Examples: AGPL-licensed library in a proprietary SaaS product (distribution triggers copyleft), data residency requirements that rule out specific cloud regions, FIPS-140-2 requirement that rules out non-certified crypto libraries. Evaluate compliance blockers before scoring — a blocked option should not appear in the rubric at all.

**RFC/spike process for tie votes:** When the evaluation rubric produces a tie (within 0.3 points) and team discussion does not converge, run a time-boxed technical spike: one engineer builds a proof-of-concept with each finalist option for 2–3 days, then presents findings to the team. Vote after the spike. Document the spike outcome in the ADR. This prevents indefinite debate and grounds the decision in hands-on evidence.

**Greenfield vs. brownfield context**: For brownfield, always evaluate migration cost as a first-class criterion. A technically superior option that requires migrating 200k lines of code is often the wrong choice. Prefer "good enough and migratable" over "theoretically best but costly to adopt."

**Vendor lock-in analysis**: For managed services (Firebase, PlanetScale, Neon, Vercel), assess: What is the data export story? What is the cost at 10x current scale? Is there a self-hosted option if the vendor changes pricing? Document lock-in risk in the ADR's Consequences section.

**When options are genuinely equivalent**: If two options score within 0.3 of each other on the weighted rubric, choose based on: (1) team familiarity, (2) existing organizational investment (training, tooling, expertise). Document the tie-breaking rationale explicitly — do not leave it as "we chose X" without justification.
