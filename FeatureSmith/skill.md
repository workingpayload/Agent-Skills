---
name: featuresmith
description: Decomposes product requirements into actionable engineering tasks with acceptance criteria, story points, and feature flag configurations. Use when a user wants to break down a feature, write user stories, define Given/When/Then scenarios, or set up feature flags with LaunchDarkly or Unleash.
---

# FeatureSmith

## Overview

Transforms raw product requirements into fully-specified engineering tasks: user stories, Given/When/Then acceptance criteria, story point estimates, sub-task breakdowns, and feature flag configurations ready for LaunchDarkly or Unleash.

## Workflow

### 1. Parse the Requirement

- Identify the **actor** (who), **action** (what), and **outcome** (why) from the input.
- Clarify ambiguities before proceeding: missing actors, undefined success states, or unstated constraints.
- Tag the work type: new feature, enhancement, bug fix, or tech debt.

### 2. Write User Stories

Format every story as:
```
As a <actor>, I want to <action> so that <business outcome>.
```
- Split stories that contain "and" in the action into separate stories.
- Target stories at 3–8 story points; split anything larger into child stories.

### 3. Define Acceptance Criteria (Given/When/Then)

Write at minimum:
- One **happy path** scenario
- One **failure/error** scenario
- One **boundary/edge** scenario

```gherkin
Scenario: <descriptive title>
  Given <precondition / system state>
  When  <actor performs action>
  Then  <observable outcome>
  And   <secondary outcome if needed>
```

Use `Background:` blocks for shared preconditions across multiple scenarios.

### 4. Estimate Story Points

Use the Fibonacci scale (1, 2, 3, 5, 8, 13):
| Points | Meaning |
|--------|---------|
| 1–2    | Trivial change, well-understood, no unknowns |
| 3–5    | Moderate complexity, 1–2 unknowns |
| 8      | High complexity or cross-team dependency |
| 13     | Needs spike; break down further |

State the primary sizing driver (complexity / uncertainty / scope).

### 5. Define Sub-Tasks

Break each story into concrete engineering tasks:
- Schema / API contract changes
- Backend implementation
- Frontend implementation
- Unit + integration tests
- Documentation / changelog entry

### 6. Configure Feature Flags

When the feature requires a staged rollout, output a flag spec:

**LaunchDarkly:**
```json
{
  "key": "feature-<kebab-name>",
  "name": "<Human Readable Name>",
  "kind": "boolean",
  "variations": [{"value": false}, {"value": true}],
  "defaultRule": {"variation": 0},
  "targeting": {
    "rules": [{"clauses": [{"attribute": "email", "op": "endsWith", "values": ["@internal.company.com"]}]}]
  }
}
```

**Unleash — flexible rollout with constraints:**
```yaml
name: feature.<kebab-name>
description: "<description>"
enabled: false
strategies:
  - name: flexibleRollout
    parameters:
      rollout: "10"
      stickiness: userId
      groupId: feature.<kebab-name>
    constraints:
      - contextName: region
        operator: IN
        values: ["us-east-1"]
```

Include a **kill-switch** plan: what to set the flag to and which systems to verify on rollback.

**Flag lifecycle compliance gate:** Before enabling in production, confirm: legal/privacy review completed (if feature collects new data), data-retention policy documented, and regional regulation checks (GDPR, CCPA) signed off. Add a sub-task: "Legal/compliance sign-off for `<flag-key>`."

## Output Format

Deliver a structured artifact per feature:

```markdown
## Story: <title>
**Type:** Feature | Enhancement | Bug Fix
**Points:** <N> (<driver>)

### User Story
As a <actor>, I want to <action> so that <outcome>.

### Acceptance Criteria
(gherkin scenarios)

### Sub-Tasks
- [ ] ...

### Feature Flag (if applicable)
(flag config)

### Out of Scope
- ...
```

## Edge Cases

**Ambiguous actor:** If the requirement says "users" without specifying role (admin vs. end-user), create separate stories per role with distinct permission checks noted.

**Cross-cutting concerns:** When a story touches auth, rate limiting, or audit logging, add an explicit sub-task for each concern and flag the dependency in the story description.

**Cross-team story splitting:** When a story spans multiple teams (e.g., platform + product), split at the team boundary. Each sub-story gets a distinct owner, its own acceptance criteria, and an explicit integration contract (API schema or event contract) defined before either team begins. Assign the integration contract sub-task to the team that owns the shared interface.

**Flag lifecycle:** Always include a cleanup task: "Remove feature flag `<key>` after 100% rollout and 2-sprint soak period." Assign it immediately to avoid flag debt.
