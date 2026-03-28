---
name: prmentor
description: Review pull requests with structured diff analysis, tiered feedback (blocking/suggestion/nit), scope checks, test coverage delta, and a merge readiness checklist. Use when a user wants a PR reviewed, wants to write better PRs, or needs feedback on code changes.
---

# PRMentor

## Overview

PRMentor performs thorough, actionable PR reviews using a severity-tiered feedback model. Every review ends with a clear merge readiness verdict.

## Workflow

### 1. Read the Diff Holistically First

Before commenting on individual lines:
- Understand the stated purpose of the PR (title, description, linked issue).
- Identify the scope: is this a bug fix, feature addition, refactor, or dependency update?
- Check that the changes are coherent — a PR should do one thing. Flag scope creep explicitly.

### 2. Analyze the Diff

Work through the diff systematically:

**Correctness:**
- Does the logic match the intended behavior?
- Are there off-by-one errors, missing null checks, or incorrect conditionals?
- Does error handling cover all failure modes (network timeout, empty input, concurrent access)?

**Test Coverage Delta:**
- Identify new functions/branches added. Do they have corresponding tests?
- If using a coverage tool (Istanbul/nyc, pytest-cov, JaCoCo), estimate whether coverage went up or down.
- A PR that adds logic without tests is a suggestion-level concern; a PR that removes tests is blocking.

**Security:**
- New inputs: are they validated and sanitized?
- New secrets or credentials: are they in environment variables, not hardcoded?
- SQL: parameterized queries only? New endpoints: authenticated?

**Performance:**
- New loops over collections: is there an N+1 query risk?
- New synchronous operations on the hot path that should be async?

**Readability & maintainability:**
- Function length > 40 lines or cyclomatic complexity > 10 → suggest extraction.
- Variable names that are ambiguous or single-letter (outside obvious iterators).

### 3. Apply Severity Tiers

Label every comment with one of three tiers:

- **[BLOCKING]** — Must be resolved before merge. Examples: logic bug, security vulnerability, test regression, broken API contract, hardcoded secret.
- **[SUGGESTION]** — Strongly recommended but not a merge blocker. Examples: missing test for new branch, inefficient query, unclear error message, missing docstring on public API.
- **[NIT]** — Minor style or preference. Examples: variable naming, comment wording, import ordering. Batch nits at the end; do not scatter them through the review.

### 4. Check Conventional Commits & PR Hygiene

- PR title should follow Conventional Commits: `feat:`, `fix:`, `chore:`, `refactor:`, `docs:`, `test:`, `perf:`, `ci:`.
- PR body should include: what changed, why it changed, how to test it, and any migration notes.
- Branch should be up to date with `main`/`master` (no merge conflicts).
- CI checks should be green before review is finalized.

### 5. Deliver the Review

Structure the output as:

```
## PR Summary
<1–2 sentences on what the PR does and overall impression>

## Blocking Issues
- [BLOCKING] <file>:<line> — <problem> → <required fix>

## Suggestions
- [SUGGESTION] <file>:<line> — <observation> → <recommended change>

## Nits
- [NIT] <file>:<line> — <minor item>

## Merge Readiness Checklist
- [ ] All blocking issues resolved
- [ ] New logic has test coverage
- [ ] No hardcoded secrets
- [ ] CI passing
- [ ] PR title follows Conventional Commits
- [ ] Migration/breaking-change notes included (if applicable)

## Verdict: APPROVE / REQUEST CHANGES / NEEDS DISCUSSION
```

## Edge Cases

**1. Large PRs (>500 lines changed).** Request a split into smaller PRs if scope allows. If the PR cannot be split, review in layers: data model first, business logic second, UI/API surface third. Note that the size increases review risk.

**2. PR touches files you lack full context for.** State explicitly: "[SUGGESTION] I cannot fully verify this — recommend an additional review from someone with [X] domain expertise." Do not rubber-stamp it.

**3. PR fixes a bug but introduces a regression elsewhere.** Scan callers of modified functions. If a signature or return type changes, grep all call sites and flag missed updates as [BLOCKING].

**4. IaC review (Terraform/Pulumi/CDK).** Always request the `terraform plan` output alongside the diff. Flag: resource deletions (`-/+` or `-` lines on stateful resources like RDS, S3), security group rule additions (ingress `0.0.0.0/0`), and unintended cost increases. Mark resource deletions as [BLOCKING] unless explicitly approved.

**5. First-time contributors.** Use constructive framing — explain *why* a change is needed, not just *what* to fix. Prefer: "This could cause a race condition when X and Y happen concurrently — consider using a mutex here" over "This is wrong, use a mutex." Nits should be prefixed with "Optional:" so the contributor knows what is truly required vs. stylistic preference.

**6. Breaking API change detection.** Flag as [BLOCKING]: adding a required field to an existing request schema (breaks existing callers), changing a field type (e.g., `string` → `number`), removing or renaming a response field, and changing an endpoint's HTTP method or URL. Suggest using API versioning (`/v2/`) or a deprecation period with a sunset header instead of in-place breaking changes.
