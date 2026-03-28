---
name: changescribe
description: Generates and maintains changelogs following Keep a Changelog format and Conventional Commits, determines semver bump rules from commit history, and parses git log output into structured release notes. Use when a user needs to create a CHANGELOG.md, prepare release notes, determine the next version number, or automate changelog generation in CI.
---

# ChangeScribe

## Domain Scope

Changelog generation, semantic versioning (semver 2.0.0), Conventional Commits specification parsing, Keep a Changelog format, git log analysis, and release automation.

---

## Workflow

### 1. Parse the Commit History
```bash
git log $(git describe --tags --abbrev=0)..HEAD --pretty=format:"%H|%s|%b|%an|%ae|%ci" --no-merges
```

### 2. Classify Commits — Type-to-Semver Mapping

| Commit Type | Semver Bump | Changelog Section |
|-------------|-------------|-------------------|
| `feat` | MINOR | Added |
| `fix`, `perf` | PATCH | Fixed / Changed |
| `refactor` | PATCH (if behavior change) | Changed |
| `docs`, `chore`, `test`, `ci`, `build` | none | (omit) |
| `BREAKING CHANGE` or `!` suffix | MAJOR | Breaking Changes |

**Breaking change detection**: footer `BREAKING CHANGE: <desc>` or type with `!` suffix (`feat!: remove API`). Always list breaking changes first.

### 3. Determine the Next Version
```
Current: 1.4.2 → BREAKING CHANGE → 2.0.0
                → feat commits    → 1.5.0
                → fix/perf only   → 1.4.3
                → docs/chore only → no release
```
Version `0.x.y`: MINOR bumps may contain breaking changes — document in changelog header.

### 4. Write the Changelog Entry

Follow **Keep a Changelog** format:
```markdown
## [1.5.0] - 2026-03-28

### Breaking Changes
- **api**: Removed `GET /v1/users/search`. Use `POST /v1/users/query`. ([#342](link)) — by @alice

### Added
- **auth**: WebAuthn/passkey authentication ([#318](link)) — by @bob

### Fixed
- **auth**: Refresh token not invalidated on logout ([#340](link)) — by @alice
```
**Section order**: Breaking Changes → Added → Changed → Deprecated → Removed → Fixed → Security.
Entry format: `- **<scope>**: <Imperative description> ([#<issue>](<url>)) — by @<author>`

### 5. Maintain CHANGELOG.md Structure
```markdown
# Changelog
## [Unreleased]
## [1.5.0] - 2026-03-28
...
[Unreleased]: https://github.com/owner/repo/compare/v1.5.0...HEAD
[1.5.0]: https://github.com/owner/repo/compare/v1.4.2...v1.5.0
```
Rules: never delete old entries; `[Unreleased]` always present; newest version first; version comparison links at bottom.

### 6. Monorepo Per-Package Changelogs
Use **changesets** for monorepos with independent package versioning:
```bash
npx changeset          # developer describes change + bump type interactively
npx changeset version  # consumes changesets, bumps package.json versions, writes CHANGELOG.md per package
npx changeset publish  # publishes to npm
```
For commit-based automation without changesets, scope parsing by directory: filter `git log` with `-- packages/my-pkg/` and parse only commits touching that package's path. `git-cliff` supports per-package `cliff.toml` with `commit_parsers` scoped to `paths`.

### 7. Hotfix Branch Changelog Placement
When a hotfix is cut from a release branch (e.g., `release/1.4.x`) and produces `v1.4.3` after `v1.5.0` already exists on main:
- Insert the `## [1.4.3]` section **chronologically** in CHANGELOG.md (after `1.5.0`, before `1.4.2`), not at the top.
- Add a note: `_Backport of security fix from v1.5.1 to the v1.4.x maintenance branch._`
- After merging the hotfix back to main, update the `[Unreleased]` diff link to include the hotfix commits.

### 8. Automation in CI
```bash
# git-cliff: generate changelog from last tag to HEAD
git cliff --output CHANGELOG.md --latest

# GitHub Actions: determine bump + generate
BUMP=$(git log $(git describe --tags --abbrev=0)..HEAD --pretty=format:"%s" | python scripts/bump_type.py)
git cliff --tag "$NEXT_VERSION" --unreleased --output release-notes.md
```

---

## Output Artifacts

- Updated `CHANGELOG.md` with new release section.
- Version determination rationale: commit types found and resulting bump.
- `release-notes.md` for GitHub Release body.
- Git tag command: `git tag -a v1.5.0 -m "Release 1.5.0"`.

---

## Edge Cases

1. **Non-conventional commits**: Classify by keyword heuristics (fix/bug → Fixed; add/new → Added; update/migrate → Changed; remove/drop → Removed). Flag ambiguous commits for review. Recommend `commitlint` hook going forward.

2. **Multiple releases from one branch**: Split commits by tag boundary. Use `git log v1.4.2..v1.4.3` and `git log v1.4.3..v1.5.0` separately — never aggregate all commits under the latest version.

3. **Merge commits, reverts, squash PRs**: Skip merge commits. Reverts remove the original entry and add a note only if user-visible. For squash-merged PRs, enforce PR title linting via branch protection rules.
