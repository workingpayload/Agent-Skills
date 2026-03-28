---
name: issueforge
description: Creates detailed, well-structured bug reports and feature requests for GitHub Issues and Jira. Use when a user wants to file a bug, write a feature request, define reproduction steps, assign severity/priority, or generate acceptance criteria for an issue tracker.
---

# IssueForge

## Overview

Produces complete, actionable issue tickets for GitHub and Jira: bug reports with reproduction steps and environment details, feature requests with acceptance criteria, and correct severity/priority classification. Output is copy-paste ready for the target tracker.

## Workflow

### 1. Classify the Issue Type

Determine the issue type from the user's description:
- **Bug:** Something is broken or behaves contrary to specification.
- **Feature Request:** New capability that does not exist yet.
- **Task / Chore:** Engineering work without direct user-facing change (migration, refactor, dependency update).
- **Spike:** Time-boxed investigation to reduce uncertainty.

Ask for missing information before drafting — a bug report without reproduction steps is not actionable.

### 2. Bug Report Template

```markdown
## Bug Report

**Summary:** <One-line description — what is wrong, not what the user expected>

**Severity:** Critical | High | Medium | Low
**Priority:** P1 | P2 | P3 | P4
**Component:** <Frontend / Backend / API / Infrastructure / etc.>
**Assignee:** <leave blank if unknown>

---

### Description
<2–3 sentence explanation of the problem and its impact on users/business.>

### Environment
| Field           | Value                        |
|---|---|
| App version     | v2.4.1                       |
| Browser/OS      | Chrome 123 / macOS 14.4      |
| API env         | Production / Staging / Local |
| User role       | Admin / Free tier            |
| Feature flags   | List active flags/experiments and their variant (e.g., `checkout-v2=enabled`, `experiment-price-display=control`) |

### Steps to Reproduce
1. Navigate to `<URL or feature>`
2. <Action>
3. <Action>
4. Observe: <what actually happens>

### Expected Behavior
<What should happen per spec/design.>

### Actual Behavior
<What actually happens. Include error message verbatim if applicable.>

### Evidence
- [ ] Screenshot / screen recording attached
- [ ] Console error log attached
- [ ] Network request/response attached (redact auth tokens)

### Possible Cause / Hypothesis
<Optional — include if known. Do not guess without evidence.>

### Workaround
<If one exists, document it to unblock affected users.>
```

### 3. Feature Request Template

```markdown
## Feature Request
**Summary:** <Imperative verb + outcome>
**Priority:** P1–P4 | **Component:** <team> | **Epic:** <link>

### Problem Statement
When <situation>, users want to <motivation>, so they can <outcome>.

### Proposed Solution
<Experience description — not an implementation spec.>

### Acceptance Criteria
Scenario: <happy path>
  Given <precondition> / When <action> / Then <outcome>

### Out of Scope
- <What this issue does NOT cover>

### Success Metric
<e.g., "Export used by >20% of dashboard visitors">
```

### 4. Assign Severity and Priority

**Severity** (impact of the defect):
| Level | Definition |
|---|---|
| Critical | Data loss, security breach, complete feature outage with no workaround |
| High | Major feature broken, workaround exists but is unacceptable |
| Medium | Feature degraded; workaround available |
| Low | Cosmetic issue, minor inconvenience |

**Priority** (urgency of fix):
| Level | SLA |
|---|---|
| P1 | Fix and deploy within 24 hours |
| P2 | Fix in current sprint |
| P3 | Scheduled for next sprint or backlog grooming |
| P4 | Nice-to-have; fix when capacity allows |

Severity and priority are independent: a Low severity bug can be P2 if it affects a key sales demo flow.

### 5. GitHub vs. Jira Formatting Differences

**GitHub Issues:** Use Markdown headers, task lists, and code fences. Apply labels (`bug`, `priority: high`, `component: auth`). Reference related issues with `#N`; use `Closes #N` in the PR description, not the issue.

**Jira:** Use structured fields (`Issue Type`, `Priority`, `Component`, `Fix Version`, `Sprint`) — do not embed them in the description body. Link with `blocks`, `is blocked by`, `relates to`, `duplicates`. Story points go in the `Story Points` field.

## Output Format

Ask the user: "Is this for GitHub or Jira?" before generating the final ticket. Then output the complete ticket body formatted for that tracker, ready to paste.

Include a one-line **PR/branch name suggestion**: `fix/auth-token-expiry-redirect` or `feat/csv-export-reports`.

## Edge Cases

**Duplicate detection:** Before finalizing, ask the user if they searched the tracker for existing issues. If they provide a similar issue URL, add a `Duplicate of #<N>` reference or a "Related Issues" section rather than creating a new ticket.

**Security vulnerabilities:** If the bug involves a potential security issue (auth bypass, data exposure, injection), do NOT file it as a public GitHub issue. Output a note instructing the user to use the repository's private security advisory (`https://github.com/<org>/<repo>/security/advisories/new`) or the organization's responsible disclosure process instead.

**Insufficient reproduction steps:** If the user cannot reliably reproduce the bug, label it `needs-repro` and add a comment template asking for: browser console output, network tab HAR export, and the exact data/state when the issue occurred. Do not assign P1/P2 to an unreproducible bug.

**Performance regression fields:** For performance bugs, add a dedicated section:
```
### Performance Regression
| Metric      | Baseline (last release) | Current     |
|---|---|---|
| p50 latency | 120 ms                  | 890 ms      |
| p99 latency | 340 ms                  | 4,200 ms    |
| Throughput  | 850 req/s               | 210 req/s   |

**Profiling data:** Attach flamegraph or profiler output. Note the profiling tool and sampling duration.
```
