---
name: commitcraft
description: Crafts Conventional Commits v1.0.0 compliant messages by analyzing git diffs. Use when a user asks for help with commit messages, git commits, or wants to commit staged changes.
---

# CommitCraft

## Overview

Produce Conventional Commits v1.0.0 messages from staged diffs or change descriptions. Every message must be machine-parseable for changelogs and semver automation.

## Workflow

### 1. Gather the Diff

Run `git diff --staged` (or `git diff HEAD~1` for the last commit). If nothing is staged, tell the user and stop.

Read the diff to identify:
- Which files changed and in what way (added, deleted, modified, renamed)
- Whether any public API surface changed (exported functions, REST routes, DB schema)
- Whether any config, env var, or migration is included

### 2. Choose Type and Scope

**Type** — pick exactly one:
| Type | When to use |
|------|-------------|
| `feat` | New user-facing capability |
| `fix` | Bug correction |
| `refactor` | Code restructure with no behaviour change |
| `perf` | Performance improvement |
| `test` | Adding or fixing tests only |
| `docs` | Documentation only |
| `build` | Build system / dependency changes (webpack, npm, gradle) |
| `ci` | CI/CD pipeline changes |
| `chore` | Housekeeping (linting, formatting) |
| `revert` | Reverting a prior commit |

**Scope** — optional, in parentheses. Use the module, package, or route name: `feat(auth)`, `fix(api/users)`.

Before choosing types or scopes, check for `commitlint.config.js` or `.commitlintrc` — these override defaults and define allowed types/scopes. Use only values listed there; introducing an unlisted scope will break automated changelog tooling.

**Monorepo multi-scope**: When a change spans tightly coupled packages (e.g., a shared type changed in `core` that requires updates in `api` and `ui`), use the most impacted scope and list affected packages in the body: `feat(core): add PaymentIntent type` then `Affects: api, ui` in the body. Avoid comma-separated scopes like `feat(api,ui)` — most parsers reject them.

### 3. Write the Subject Line

Rules (all mandatory):
- Format: `<type>(<scope>): <imperative description>`
- Max **72 characters** total
- Imperative mood: "add", "fix", "remove" — never "added", "fixes", "adding"
- No period at the end
- Lowercase everything except proper nouns and acronyms

Examples:
```
feat(payments): add Stripe webhook signature verification
fix(auth): handle expired JWT refresh tokens correctly
refactor(db): replace raw queries with Drizzle ORM
perf(images): lazy-load thumbnails below the fold
```

### 4. Write the Body (when needed)

Include a body when the diff is non-trivial. Separate from subject with a blank line. Wrap at 72 characters. Explain *why*, not *what* — the diff already shows what.

### 5. Add Footers

**Breaking change** (triggers major semver bump):
```
BREAKING CHANGE: <description of what breaks and migration path>
```

**Issue references:**
```
Closes #42
Refs #17, #23
```

**Co-authors:**
```
Co-authored-by: Name <email>
```

### 6. Validate Before Presenting

Check:
- [ ] Subject ≤ 72 chars
- [ ] Imperative verb in subject
- [ ] `BREAKING CHANGE:` footer present if any public API removed or changed incompatibly
- [ ] Body explains motivation, not mechanics
- [ ] No trailing whitespace, no period on subject

## Output Format

Present the final message in a fenced code block so the user can copy it directly:

```
feat(scope): short imperative description

Longer explanation of why this change was needed. Mention
any trade-offs or alternatives considered.

BREAKING CHANGE: describe what breaks and how to migrate.
Closes #42
```

## Edge Cases

**Multiple unrelated changes in one diff**: Flag this. Suggest splitting with `git add -p`. Offer a message for the dominant change only, with a note listing the other concerns.

**Revert commit**: Use `revert: revert "original subject"` as subject, and include `This reverts commit <SHA>` in the body. For merge or squash commits, use `git revert -m 1 <SHA>` to revert to the mainline parent; without `-m 1`, git cannot determine which parent to revert to and will error.

**Dependency-only bump**: Use `build(deps): bump <package> from X to Y` — never `chore` for security-relevant dependency upgrades; use `fix(deps)` if it patches a CVE.
