---
name: readmecraft
description: Write or improve README files following the standard-readme spec, with mandatory sections, shields.io badges, clear installation/usage examples, and a contribution guide. Use when a user needs a README created, reviewed, or updated for a project.
---

# ReadMeCraft

## Overview

ReadMeCraft produces READMEs that follow the [standard-readme spec](https://github.com/RichardLitt/standard-readme) and pass the discovery checklist — making projects immediately understandable to new visitors.

## Workflow

### 1. Gather Project Context

Before writing, collect:
- Project name, one-line description, and primary language/framework.
- Install method: npm/pip/cargo/go/brew/Docker?
- Minimum runtime requirements (Node ≥ 20, Python ≥ 3.11, etc.).
- License (MIT, Apache-2.0, GPL-3.0, etc.).
- CI/CD platform (for badge URLs).
- Link to hosted demo, docs site, or package registry if available.

### 2. Apply the Standard README Structure

Produce sections in this exact order (omit only if genuinely not applicable):

```markdown
# Project Name

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/org/repo/actions/workflows/ci.yml/badge.svg)](...)
[![npm version](https://img.shields.io/npm/v/package-name)](...)
[![PyPI version](https://img.shields.io/pypi/v/package-name)](...)

> One-sentence description of what this project does and for whom.

## Table of Contents
(auto-generated or manual links for READMEs > 100 lines)

## Background
Why this project exists. What problem does it solve? How is it different from alternatives?

## Install
\`\`\`bash
npm install package-name       # Node
pip install package-name       # Python
cargo add package-name         # Rust
\`\`\`
Prerequisites: list runtime versions, system dependencies (e.g., libpq-dev), env vars required.

## Usage
\`\`\`bash
# Minimal working example — copy-pasteable, no placeholders left unfilled
package-name --input data.json --output result.json
\`\`\`
Include a second example showing a common real-world use case. For libraries, show the import + core API call.

## API (if a library)
Document public exports: function signatures, parameters, return types, thrown errors.
Use a table for options objects.

## Configuration
List all environment variables and config file keys in a table:
| Variable | Required | Default | Description |
|---|---|---|---|

## Contributing
1. Fork → `git checkout -b feat/my-feature`
2. Make changes + add tests.
3. Run `npm test` / `pytest` / `cargo test`.
4. Open a PR against `main`.

Link to a `CONTRIBUTING.md` if it exists; otherwise include the essentials inline.

## License
[MIT](LICENSE) © Year Author
```

### 3. Write Effective Badges

Use `shields.io` dynamic badges (they pull live data):

```markdown
[![License](https://img.shields.io/github/license/org/repo)](LICENSE)
[![Build](https://img.shields.io/github/actions/workflow/status/org/repo/ci.yml)](...)
[![Coverage](https://img.shields.io/codecov/c/github/org/repo)](...)
[![npm](https://img.shields.io/npm/v/pkg)](https://npmjs.com/package/pkg)
[![PyPI](https://img.shields.io/pypi/v/pkg)](https://pypi.org/project/pkg/)
[![Docker Pulls](https://img.shields.io/docker/pulls/org/image)](...)
```

Keep badges to 4–6 maximum. Avoid badges that are always green (e.g., "built with love").

### 4. Write the Usage Section for Scanners

Most visitors scan, not read. The Usage section must:
- Open with a copy-pasteable command that produces visible output.
- Use real values, not `<YOUR_VALUE_HERE>` placeholders.
- Include a second, slightly more complex example.
- For CLIs: show `--help` output or a table of flags.
- For libraries: show `import` + the single most common API call.

### 5. Discovery Checklist

Before finalizing, verify:
- [ ] Title and one-liner description present.
- [ ] At least one shield badge with live status.
- [ ] Install instructions that work on a clean machine.
- [ ] Usage example that produces observable output.
- [ ] All required env variables documented.
- [ ] License section with SPDX identifier.
- [ ] Contributing section (even if just one sentence linking to CONTRIBUTING.md).
- [ ] No broken links (test with `markdown-link-check`).
- [ ] No placeholder text left unfilled.

## Edge Cases

**4. Multilingual README convention.** For projects serving multiple language communities, create separate files per locale: `README.md` (English, canonical), `README.zh-CN.md`, `README.es.md`, etc. At the top of each file, add a language switcher link block: `[English](README.md) | [中文](README.zh-CN.md)`. Do not use machine-translated content without human review. Keep the English README as the source of truth; other languages may lag behind minor updates.

**5. Compiled-from-source installation.** When the project requires a build step (C/C++/Rust with make/cmake), the Install section must include: system dependencies (`sudo apt-get install cmake libssl-dev`), the full build sequence (`cmake -S . -B build && cmake --build build --parallel`), and the install step (`sudo cmake --install build`). List minimum compiler versions (GCC ≥ 11, Clang ≥ 14). For CMake projects, note any required `-DCMAKE_BUILD_TYPE=Release` flags and how to run the test suite (`ctest --test-dir build`).

**1. Monorepo with multiple packages.** The root README should describe the repository structure and link to each package's own README. Do not document all packages in a single file — it becomes unmaintainable. Include a directory tree showing package layout.

**2. Internal / private project (no public registry).** Omit registry badges. Replace the Install section with internal setup instructions (e.g., Artifactory, private npm registry, SSH clone URL). Include any VPN or authentication prerequisites prominently.

**3. README for a CLI tool vs. a library vs. a service.** Tailor the Usage section: CLIs need a full flags/options table; libraries need an API reference with type signatures; services (Docker/K8s apps) need a quickstart with `docker run` / `kubectl apply` commands and a link to the full ops runbook.
