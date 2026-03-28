# 🧠 Agent Skills

> Install and run AI-powered developer skills across Claude, Gemini, and Google Antigravity.

⚡ Turn prompts into reusable, installable skills
⚡ Works from CLI in seconds
⚡ Built for developers

---

## 🚀 Quick Start

```bash
npx @workingpayload/agent-skills install
```

---

## ✨ Features

* 🧠 54 expert-level developer skills with named tools, concrete steps, and edge case coverage
* 🤖 Multi-LLM support (Claude, Gemini, Google Antigravity)
* 📦 CLI-first workflow with install, route, doctor, and score commands
* 🔄 Versioning & health checks for installed skills
* 🎯 Selective install — pick only the skills you need
* 🧩 File-based skill architecture with YAML frontmatter
* 🧪 Quality tooling — linter, auto-scorer, adversarial test harness
* 📊 Machine-readable skill index for programmatic routing

---

## 📦 Installation

### Use instantly (recommended)

```bash
npx @workingpayload/agent-skills install
```

### Or install globally

```bash
npm install -g @workingpayload/agent-skills
```

### Install specific skills only

```bash
npx @workingpayload/agent-skills install -s CodeSage,TestCrafter,BugHunter Pro
```

### Install for Gemini

```bash
npx @workingpayload/agent-skills install -t gemini
```

### Install for Google Antigravity

```bash
npx @workingpayload/agent-skills install -t antigravity
```

Skills are installed as directory-based packages (`SKILL.md` + optional scripts/references) to `~/.gemini/antigravity/skills/`. The Antigravity agent automatically matches skills to your tasks via semantic triggering.

---

## 🧪 Usage

### Use skills in Claude Code

After installing, invoke skills as slash commands:

```
/codesage          → "Review this function for security issues"
/bughunter-pro     → "Debug this failing test"
/testcrafter       → "Write unit tests for UserService"
/python-master     → "Fix this async race condition"
/react-ranger      → "Build a search component with debounce"
/fastapi-furious   → "Create a CRUD API for products"
/dockmaster        → "Optimize my Dockerfile"
/kubecrafter       → "Write a Deployment manifest with HPA"
```

### Find the right skill

```bash
npx @workingpayload/agent-skills route "review my Python code"
# → codesage (score: 12), python-master (score: 12)

npx @workingpayload/agent-skills route "design database schema"
# → dataweaver (score: 20), modelsensei (score: 20)
```

---

## 🧠 CLI Commands

| Command | Description |
| --- | --- |
| `install` | Install skills to Claude or Gemini |
| `uninstall <names>` | Remove installed skills |
| `list` | List installed skills with timestamps |
| `route "<prompt>"` | Find the best skill for a task |
| `doctor` | Check health of installed skills |
| `validate` | Lint all skill files |
| `score` | Auto-score skills on quality metrics |
| `test` | Run adversarial tests on all skills |
| `build-index` | Regenerate skills.json routing index |

---

## ⚙️ Options

| Flag | Description |
| --- | --- |
| `-t, --target` | Target platform: `claude`, `gemini`, or `antigravity` |
| `-s, --skills` | Comma-separated skill names to install |
| `--force` | Overwrite existing skills |
| `--dry-run` | Preview without writing files |
| `--validate` | Validate skills before installing |
| `--json` | Machine-readable output (score, route) |
| `--interactive` | Interactive prompt mode (route) |
| `-n, --top-n` | Number of routing results (default: 3) |

---

## 🗂️ Where Skills Are Installed

```
~/.claude/commands/                # Claude Code slash commands
~/.gemini/commands/                # Gemini skills
~/.gemini/antigravity/skills/      # Google Antigravity skills (directory-based)
```

Each skill becomes a slash command (Claude/Gemini) or a directory-based skill (Antigravity):

```
~/.claude/commands/codesage.md                → /codesage
~/.claude/commands/testcrafter.md             → /testcrafter
~/.gemini/antigravity/skills/codesage/SKILL.md  → auto-triggered by Antigravity agent
```

---

## 🩺 Health Checks

```bash
npx @workingpayload/agent-skills doctor
```

Checks:
* Install directory exists
* Meta file is valid
* All tracked skills are present on disk
* Installed skills match source (stale detection)
* No orphan files
* Frontmatter is valid

---

## 📊 Quality Tooling

```bash
# Lint all skills (CI gate)
npx @workingpayload/agent-skills validate

# Auto-score on 6 measurable criteria (0-30 scale)
npx @workingpayload/agent-skills score

# Run adversarial tests
npx @workingpayload/agent-skills test

# Generate machine-readable index
npx @workingpayload/agent-skills build-index
```

### Scoring Criteria

| Criterion | What it measures |
| --- | --- |
| Tool Coverage | Named tools/commands in backticks |
| Code Examples | Fenced code blocks with real examples |
| Edge Cases | Real-world failure scenarios covered |
| Actionability | Concrete numbered workflow steps |
| Structure | Frontmatter, overview, workflow, output format |
| Conciseness | Optimal line count (80-150 lines) |

---

## 🧩 Skill Format

Every skill file follows this structure:

```md
---
name: codesage
description: Performs structured code reviews with severity-tiered findings...
---

# CodeSage

## Overview
Expert code review covering security, correctness, performance...

## Workflow
### 1. Identify Language and Context
- Detect language, framework, runtime...

### 2. Static Analysis Pass
Run: `ruff check`, `mypy --strict`, `bandit -r .`...

## Edge Cases
1. Auto-generated code (Prisma, OpenAPI) — don't flag style...
2. False positive from linter — verify before reporting...

## Output Format
- Severity tier (CRITICAL/HIGH/MEDIUM/LOW/NOTE)
- Code snippet with fix
- Verification command
```

---

## 🧠 Skills Catalog

### Code Quality

| Skill | Command | Description |
| --- | --- | --- |
| **CodeSage** | `/codesage` | Structured code reviews with severity tiers, OWASP security checks, and language-specific linters |
| **RefactorX** | `/refactorx` | Safe refactoring using Fowler's patterns, strangler fig, and cyclomatic complexity reduction |
| **LogicLens** | `/logiclens` | Analyzes complex code for cyclomatic complexity, then refactors with guard clauses and strategy pattern |
| **SpeedSmith** | `/speedsmith` | Performance optimization: caching, code splitting, image optimization, bundle size CI gating |
| **FunctionForge** | `/functionforge` | Pure, testable utility functions using FP principles — immutability, Result types, pipe/compose |

### Testing

| Skill | Command | Description |
| --- | --- | --- |
| **TestCrafter** | `/testcrafter` | Unit/integration tests with Jest, Vitest, Pytest, JUnit using AAA pattern and test pyramid |
| **FlowTester** | `/flowtester` | E2E tests with Playwright/Cypress, Page Object Model, and CI-friendly configuration |
| **CoverageMax** | `/coveragemax` | Identifies untested paths, generates tests to reach 80%+ coverage with pytest-cov, Jest, Istanbul |
| **EdgeGuard** | `/edgeguard` | Finds edge cases using boundary analysis, property-based testing, fuzzing, and mutation testing |
| **MockSmith** | `/mocksmith` | Schema-driven mock data with Faker.js/factory_boy, MSW API stubs, and edge-case datasets |

### Security

| Skill | Command | Description |
| --- | --- | --- |
| **SecureScan** | `/securescan` | SAST security auditing: OWASP Top 10, CWE mapping, Semgrep/Bandit/CodeQL |
| **SecretSniffer** | `/secretsniffer` | Scans codebases and git history for hardcoded credentials with TruffleHog/gitleaks |
| **InputShield** | `/inputshield` | Input validation and sanitization: Zod/Joi/Pydantic, XSS/SQLi prevention, CSP headers |
| **AuthCraft** | `/authcraft` | Auth systems: OAuth 2.0/PKCE, JWT lifecycle, bcrypt/Argon2, OWASP ASVS compliance |

### DevOps

| Skill | Command | Description |
| --- | --- | --- |
| **DockMaster** | `/dockmaster` | Optimized Dockerfiles with multi-stage builds, Trivy scanning, Compose, and Helm charts |
| **KubeCrafter** | `/kubecrafter` | Production-ready K8s manifests: Deployments, HPA, StatefulSets, Pod Security Standards |
| **PipelinePro** | `/pipelinepro` | CI/CD with GitHub Actions/GitLab CI, OIDC auth, blue-green/canary deploys, rollback |
| **EnvWizard** | `/envwizard` | Secure env var management: .env.example, startup validation, vault integration |
| **CronGenius** | `/crongenius` | Cron expressions, distributed job scheduling, Celery Beat, systemd timers, EventBridge |

### Frontend

| Skill | Command | Description |
| --- | --- | --- |
| **UISmith** | `/uismith` | Accessible UI components: Atomic Design, WCAG AA, ARIA, design tokens, RTL support |
| **FlexiLayout** | `/flexilayout` | CSS layout debugging: Flexbox/Grid, container queries, fluid typography, responsive design |
| **RenderBoost** | `/renderboost` | Core Web Vitals optimization: LCP, CLS, INP, lazy loading, Service Worker caching |
| **SEOMancer** | `/seomancer` | Technical SEO: JSON-LD, meta tags, Open Graph, canonical/hreflang, site migration |
| **AccessPlus** | `/accessplus` | RBAC/ABAC authorization + WCAG 2.1 accessibility with screen reader testing |

### Database

| Skill | Command | Description |
| --- | --- | --- |
| **DataWeaver** | `/dataweaver` | Schema design (1NF-3NF), EXPLAIN ANALYZE, reversible migrations with Alembic/Flyway/Prisma |
| **QueryPulse** | `/querypulse` | SQL optimization: index design, N+1 detection, deadlock diagnosis, CTE materialization |
| **DataPolish** | `/datapolish` | Data cleaning with pandas/polars/Great Expectations: profiling, dedup, type coercion |
| **ModelSensei** | `/modelsensei` | DDD data models, ORM mappings, N+1 prevention, outbox pattern, hierarchical data |

### Architecture

| Skill | Command | Description |
| --- | --- | --- |
| **Architekt AI** | `/architekt-ai` | System design: C4 model, ADRs, CQRS, event sourcing, zero-downtime DB migrations |
| **ServiceSplitter** | `/servicesplitter` | Monolith-to-microservices: DDD bounded contexts, event storming, strangler fig, sagas |
| **StackWise** | `/stackwise` | Tech stack evaluation with weighted rubric, ADR output, library health metrics |
| **TaskOrchestrator** | `/taskorchestrator` | Async task queues: Celery/BullMQ/Temporal, dead-letter queues, idempotency, backpressure |

### Documentation

| Skill | Command | Description |
| --- | --- | --- |
| **DocuGenie** | `/docugenie` | OpenAPI 3.x specs, JSDoc/TSDoc/Google-style docstrings, and developer guides |
| **ReadMeCraft** | `/readmecraft` | README files: standard-readme spec, badges, install/usage sections, multilingual |
| **ChangeScribe** | `/changescribe` | Changelogs: Keep a Changelog format, Conventional Commits, semver bump rules |

### Git & Workflow

| Skill | Command | Description |
| --- | --- | --- |
| **CommitCraft** | `/commitcraft` | Conventional Commits v1.0.0 messages from git diff analysis |
| **PRMentor** | `/prmentor` | PR reviews with severity tiers, scope checks, IaC review, and merge readiness checklist |
| **IssueForge** | `/issueforge` | Structured bug reports and feature requests for GitHub Issues and Jira |

### Debugging & Observability

| Skill | Command | Description |
| --- | --- | --- |
| **BugHunter Pro** | `/bughunter-pro` | Hypothesis-driven debugging with reproduction, isolation, and regression tests |
| **ErrorMedic** | `/errormedic` | Stack trace diagnosis, error taxonomy, source map correlation, race condition fixes |
| **TraceMind** | `/tracemind` | Distributed tracing with OpenTelemetry, structured logging, SLO-based alerting |
| **PerfDetective** | `/perfdetective` | Performance profiling: flamegraphs, py-spy, async-profiler, GC pause analysis |

### Language-Specific

| Skill | Command | Description |
| --- | --- | --- |
| **Python Master** | `/python-master` | Full Python lifecycle: ruff, mypy, pytest, uv/poetry, memory leak diagnosis |
| **React Ranger** | `/react-ranger` | React with TypeScript: hooks, RSC, Vitest/RTL, a11y, bundle analysis |
| **FastAPI Furious** | `/fastapi-furious` | FastAPI: project scaffold, Alembic, WebSockets, file uploads, BackgroundTasks |
| **Extension Extender** | `/extension-extender` | Manifest V3 browser extensions: Chrome/Firefox, CSP, storage, service workers |

### Other

| Skill | Command | Description |
| --- | --- | --- |
| **AlgoMaster** | `/algomaster` | Algorithm optimization: Big-O, DP, greedy, graph, data structure selection |
| **AutoScriptor** | `/autoscriptor` | Automation scripts in Bash/Python/PowerShell with ShellCheck and dry-run mode |
| **BoilerCore** | `/boilercore` | Project scaffolding with ecosystem conventions, CI/linter setup, Docker template |
| **FeatureSmith** | `/featuresmith` | Requirement decomposition: user stories, story points, feature flags (LaunchDarkly/Unleash) |
| **PolyglotShift** | `/polyglotshift` | Code translation between languages preserving idioms and type systems |
| **PromptForge** | `/promptforge` | LLM prompt engineering: CoT, ReAct, few-shot, multi-modal, function-calling |
| **ScrapeMaster** | `/scrapemaster` | Web scraping: Playwright/Cheerio/BeautifulSoup, robots.txt, retry/backoff |

---

## 🤖 Supported Models

* Claude (Anthropic)
* Gemini (Google)
* Google Antigravity (agent-first IDE)

---

## 🧱 Create Your Own Skill

1. Create a directory with a `skill.md` file:

```
MySkill/skill.md
```

2. Add frontmatter and content:

```md
---
name: myskill
description: Describe what this skill does in 50+ characters...
---

# MySkill

## Overview
What this skill specializes in...

## Workflow
### 1. First Step
Concrete instructions with named tools...

## Edge Cases
1. Real-world failure scenario...

## Output Format
How results should be structured...
```

3. Validate and install:

```bash
npx @workingpayload/agent-skills validate
npx @workingpayload/agent-skills install --force
```

---

## 💥 Why This Exists

Prompt engineering is repetitive.

Agent Skills turns prompts into:

* reusable skills with named tools and concrete steps
* installable CLI commands for Claude and Gemini
* quality-gated, version-tracked AI workflows

---

## 🚀 Roadmap

* [x] 54 expert-level skills with edge case coverage
* [x] CLI with install, route, doctor, score commands
* [x] Quality tooling (linter, scorer, adversarial tests)
* [x] Machine-readable skill index (skills.json)
* [x] GitHub Actions CI pipeline
* [ ] Skill marketplace
* [ ] Web UI playground
* [ ] Skill chaining
* [ ] Embedding-based semantic routing

---

## 🤝 Contributing

PRs welcome!

1. Fork repo
2. Add or improve a skill
3. Run `npx @workingpayload/agent-skills validate` to check quality
4. Submit PR — CI will score your skill automatically

---
