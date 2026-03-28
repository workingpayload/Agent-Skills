---
name: pipelinepro
description: Design and implement CI/CD pipelines using GitHub Actions or GitLab CI, including pipeline stages, secrets management, deployment strategies (blue-green, canary), artifact pinning, and rollback procedures. Use when a user needs to build, fix, or improve a CI/CD pipeline or deployment workflow.
---

# PipelinePro

## Overview

PipelinePro builds production-grade CI/CD pipelines for GitHub Actions and GitLab CI, covering the full lifecycle from commit to production deployment with safety controls.

## Workflow

### 1. Gather Requirements

Before writing any YAML, confirm:
- **Platform**: GitHub Actions (`.github/workflows/`) or GitLab CI (`.gitlab-ci.yml`)?
- **Build target**: Docker image, npm package, Python wheel, binary, Terraform plan?
- **Environments**: dev / staging / production? Any approval gates?
- **Deployment strategy**: rolling, blue-green, or canary?
- **Secret sources**: GitHub/GitLab secret store, AWS Secrets Manager, Vault, or `.env` file?

### 2. Structure the Pipeline Stages

Use this canonical stage order:

```
lint → test → build → security-scan → publish-artifact → deploy-staging → [approval] → deploy-production
```

**GitHub Actions skeleton:**
```yaml
on: { push: { branches: [main] }, pull_request: {} }
jobs:
  lint:
    runs-on: ubuntu-latest
    steps: [{ uses: actions/checkout@v4 }, { run: npm ci && npm run lint }]
  test:
    needs: lint
    runs-on: ubuntu-latest
    steps: [{ uses: actions/checkout@v4 }, { run: npm ci && npm test -- --coverage }]
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/build-push-action@v5
        with: { push: true, tags: "ghcr.io/${{ github.repository }}:${{ github.sha }}" }
```

### 3. Secrets Injection — OIDC-Based Cloud Auth (Preferred)

Never use static cloud credentials in CI. Use OIDC to assume short-lived roles:

**GitHub Actions → AWS:**
```yaml
permissions:
  id-token: write
  contents: read
steps:
  - uses: aws-actions/configure-aws-credentials@v4
    with:
      role-to-assume: arn:aws:iam::123456789012:role/github-ci-role
      aws-region: us-east-1
```

**GitHub Actions → GCP:**
```yaml
- uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: projects/123/locations/global/workloadIdentityPools/github/providers/github
    service_account: ci@my-project.iam.gserviceaccount.com
```

For static secrets (API keys, DB passwords): store in GitHub/GitLab secret store or Vault (`hashicorp/vault-action@v3`). Use `environment:` scoping so production secrets are only available in the production job. Never echo secrets; use `::add-mask::` for dynamic values.

### 4. Artifact Pinning

- Pin third-party actions to a full commit SHA, not a mutable tag:
  ```yaml
  uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
  ```
- Pin Docker base images to digest: `FROM node:20-alpine@sha256:abc123...`
- Use `actions/upload-artifact@v4` / `download-artifact@v4` to pass build outputs between jobs rather than rebuilding.

### 5. Deployment Strategies

**Blue-Green:** Deploy to idle environment → smoke test → swap load balancer target → keep old live 10–15 min for instant rollback.

**Canary:** Deploy at 1–5% traffic weight (Argo Rollouts, Flagger) → monitor error rate + p99 for 5–30 min → auto-promote or rollback on threshold breach.

**Rollback:** `kubectl rollout undo deployment/my-app`. Store previous image SHA as a pipeline artifact for deterministic rollback.

### 6. Output Artifacts

Deliver:
1. Complete, runnable YAML file(s) with inline comments.
2. List of secrets/variables that must be configured and where.
3. Deployment strategy diagram (text-based if needed).
4. Rollback command or job snippet.

### 6. DB Migration Sequencing

Run migrations before the new code deploys — never after. The pattern:
```yaml
migrate:
  needs: build
  steps:
    - run: |
        npx prisma migrate deploy   # or: alembic upgrade head / rails db:migrate
        if [ $? -ne 0 ]; then echo "Migration failed — aborting deploy"; exit 1; fi
deploy:
  needs: migrate
```
For rollback: always provide a `down` migration and keep the previous image SHA as a pipeline artifact so `kubectl rollout undo` or a re-deploy of the prior image is deterministic.

### 7. Container Image Vulnerability Scanning

Scan images after build, before publish. Fail the pipeline on critical or high CVEs:
```yaml
scan:
  needs: build
  steps:
    - uses: aquasecurity/trivy-action@master
      with:
        image-ref: ghcr.io/${{ github.repository }}:${{ github.sha }}
        format: table
        exit-code: '1'           # fail pipeline
        severity: CRITICAL,HIGH
        ignore-unfixed: true     # skip CVEs with no fix available
```
Grype alternative: `grype ghcr.io/myorg/myapp:sha --fail-on high`. Review and suppress false positives via `.trivyignore` or `grype.db` exceptions with documented justification.

## Edge Cases

**1. Self-hosted runners with no internet access.** Cache dependencies explicitly (`actions/cache@v4`, `pip download --dest`, npm `--prefer-offline`) and mirror Docker images to an internal registry. Document the exact registry URL as an environment variable.

**2. Flaky tests causing false deployment failures.** Add a retry mechanism (`retry: 2` in GitLab; a step-level `continue-on-error` + re-run logic in GitHub Actions) only for known-flaky test suites. Mark the job with a `flaky` label and open a tracking issue — never silently suppress test failures in gates.

**3. Monorepo with multiple independently deployable services.** Use path filters to trigger only affected pipelines:
```yaml
on:
  push:
    paths: ['services/api/**']
```
Or use tools like `nx affected`, `turborepo`, or GitLab's `rules: changes:` to skip unaffected jobs.
