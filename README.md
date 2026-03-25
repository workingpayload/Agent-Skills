# 🧠 Agent Skills

> Install and run AI-powered developer skills across Claude and Gemini.

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

* 🧠 50+ prebuilt developer skills
* 🤖 Multi-LLM support (Claude, Gemini)
* 📦 CLI-first workflow
* 🔄 Sync & versioning system
* 🎯 Selective install support
* 🧩 File-based skill architecture

---

## 📦 Installation

### Use instantly (recommended)

```bash
npx agent-skills install
```

### Or install globally

```bash
npm install -g agent-skills
```

---

## 🧪 Usage

### Run a skill

```bash
Use CodeSage to explain the code
```

---

## 🧠 CLI Commands

| Command | Description                              |
| ------- | ---------------------------------------- |
| install | Install skills (auto-detect environment) |
| sync    | Update skills                            |
| list    | List all available skills                |
| doctor  | Show install paths                       |
| run     | Execute a skill                          |

---

## ⚙️ Options

| Flag    | Description          |
| ------- | -------------------- |
| -gemini | Use Gemini           |
| -claude | Use Claude           |
| --force | Overwrite existing   |

---

## 🗂️ Where Skills Are Installed

```
~/.gemini/skills/
~/.claude/skills/
```

Each skill:

```
CodeSage/
  skill.md
```

---

## 🧩 Example Skill

```md
# CodeSage

## Description
Explains code clearly

## Prompt
Explain the following code:
{{code}}
```

---

## 🔄 Versioning & Sync

Each install creates:

```
~/.gemini/skills/.meta.json
```

Update anytime:

```bash
agent-skills sync
```

---


## 🧠 Skills Catalog

  ### AccessPlus
      
  **Path:** `AccessPlus/skill.md`
      
      Perfects tasks related to designing and implementing role-based access control (RBAC), fine-grained permissions, and secure authorization workflows. Use when a user asks to handle frontend or requires assistance with accessibility..
      
  ### AlgoMaster
      
  **Path:** `AlgoMaster/skill.md`
      
      Perfects tasks related to analyzing algorithmic complexity, optimizing data structures, and providing highly efficient solutions to computational problems. Use when a user asks to handle algorithm or requires assistance with improves algorithms..
      
  ### APIForge
      
  **Path:** `APIForge/skill.md`
      
      Perfects tasks related to designing robust REST and GraphQL APIs, establishing clear contract definitions, and structuring optimal endpoints. Use when a user asks to handle api or requires assistance with design apis..
      
  ### Architekt AI
      
  **Path:** `Architekt AI/skill.md`
      
      Perfects tasks related to crafting scalable system architectures, designing microservices, and outlining high-level technical blueprints. Use when a user asks to handle architecture or requires assistance with system design..
      
  ### AuthCraft
      
  **Path:** `AuthCraft/skill.md`
      
      Perfects tasks related to building secure authentication systems, implementing OAuth, JWT, and session management with best security practices. Use when a user asks to handle security or requires assistance with auth design..
      
  ### AutoScriptor
      
  **Path:** `AutoScriptor/skill.md`
      
      Perfects tasks related to generating automation scripts, cron jobs, and utility CLI tools to streamline repetitive developer tasks. Use when a user asks to handle automation or requires assistance with scripts..
      
  ### BoilerCore
      
  **Path:** `BoilerCore/skill.md`
      
      Perfects tasks related to scaffolding project boilerplates, setting up foundational configurations, and initializing standardized project structures. Use when a user asks to handle setup, codegen or requires assistance with generates boilerplate..
      
  ### BugHunter Pro
      
  **Path:** `BugHunter Pro/skill.md`
      
      Perfects tasks related to identifying elusive logic flaws, tracing memory leaks, and diagnosing complex application bugs with precision. Use when a user asks to handle debug or requires assistance with finds bugs..
      
  ### ChangeScribe
      
  **Path:** `ChangeScribe/skill.md`
      
      Perfects tasks related to generating comprehensive, semantic changelogs, summarizing pull requests, and tracking version history. Use when a user asks to handle docs or requires assistance with changelog..
      
  ### CodeSage
      
  **Path:** `CodeSage/skill.md`
      
      Perfects tasks related to providing expert-level code reviews, suggesting idiomatic improvements, and ensuring adherence to language-specific best practices. Use when a user asks to handle code, analysis or requires assistance with explains code clearly, including purpose and logic..
      
  ### CommitCraft
      
  **Path:** `CommitCraft/skill.md`
      
      Perfects tasks related to crafting clear, conventional commit messages that accurately reflect code changes and adhere to project standards. Use when a user asks to handle git or requires assistance with commit messages..
      
  ### CoverageMax
      
  **Path:** `CoverageMax/skill.md`
      
      Perfects tasks related to identifying untested code paths, generating comprehensive unit test cases, and maximizing code coverage metrics. Use when a user asks to handle testing or requires assistance with improves coverage..
      
  ### CronGenius
      
  **Path:** `CronGenius/skill.md`
      
      Perfects tasks related to designing robust cron expressions, scheduling distributed background jobs, and handling task retries and failures. Use when a user asks to handle automation or requires assistance with cron jobs..
      
  ### DataPolish
      
  **Path:** `DataPolish/skill.md`
      
      Perfects tasks related to cleaning, formatting, and normalizing raw data structures, ensuring data integrity and consistency. Use when a user asks to handle data or requires assistance with clean data..
      
  ### DataWeaver
      
  **Path:** `DataWeaver/skill.md`
      
      Perfects tasks related to designing complex database schemas, writing optimized SQL/NoSQL queries, and managing data migrations. Use when a user asks to handle database or requires assistance with db schema design..
      
  ### DockMaster
      
  **Path:** `DockMaster/skill.md`
      
      Perfects tasks related to creating optimized Dockerfiles, managing container orchestration, and ensuring reproducible build environments. Use when a user asks to handle devops or requires assistance with dockerfile..
      
  ### DocuGenie
      
  **Path:** `DocuGenie/skill.md`
      
      Perfects tasks related to writing clear, comprehensive API documentation, inline code comments, and developer guides. Use when a user asks to handle docs or requires assistance with docs..
      
  ### EdgeGuard
      
  **Path:** `EdgeGuard/skill.md`
      
      Perfects tasks related to implementing edge computing solutions, optimizing CDN caching, and designing serverless worker logic. Use when a user asks to handle testing or requires assistance with finds edge cases..
      
  ### EnvWizard
      
  **Path:** `EnvWizard/skill.md`
      
      Perfects tasks related to managing environment variables, configuring secure secret injection, and establishing environment-specific settings. Use when a user asks to handle devops or requires assistance with env setup..
      
  ### ErrorMedic
      
  **Path:** `ErrorMedic/skill.md`
      
      Perfects tasks related to interpreting stack traces, categorizing runtime exceptions, and providing immediate, actionable fixes for application errors. Use when a user asks to handle debug, fix or requires assistance with fixes errors..
      
  ### extension-extender
      
  **Path:** `extension-extender/SKILL.md`
      
      Creates, fixes, and debugs browser extensions with efficiency and beautiful UI. Use when a user asks to build a Chrome/Firefox extension, create a browser extension popup, or debug extension manifest/scripts.
      
  ### fastapi-furious
      
  **Path:** `fastapi-furious/SKILL.md`
      
      This skill should be used when the user asks to "build FastAPI", "create FastAPI", "fix FastAPI", "debug FastAPI", or "improve FastAPI". It specializes in creating, debugging, fixing, and improving FastAPI code with high efficiency, ensuring correct, clean, and production-ready output.
      
  ### FeatureSmith
      
  **Path:** `FeatureSmith/skill.md`
      
      Perfects tasks related to breaking down product requirements into actionable engineering tasks, technical specifications, and feature flags. Use when a user asks to handle ml or requires assistance with feature engineering..
      
  ### FlexiLayout
      
  **Path:** `FlexiLayout/skill.md`
      
      Perfects tasks related to designing responsive CSS layouts, resolving Flexbox/Grid alignment issues, and creating fluid UI components. Use when a user asks to handle frontend or requires assistance with responsive design..
      
  ### FlowTester
      
  **Path:** `FlowTester/skill.md`
      
      Perfects tasks related to writing end-to-end integration tests, simulating complex user journeys, and verifying cross-service workflows. Use when a user asks to handle testing or requires assistance with integration tests..
      
  ### FunctionForge
      
  **Path:** `FunctionForge/skill.md`
      
      Perfects tasks related to writing pure, modular, and highly testable utility functions, emphasizing functional programming principles. Use when a user asks to handle codegen or requires assistance with generates functions..
      
  ### InputShield
      
  **Path:** `InputShield/skill.md`
      
      Perfects tasks related to implementing rigorous input validation, sanitization, and preventing XSS, SQL injection, and payload vulnerabilities. Use when a user asks to handle security or requires assistance with validation..
      
  ### IssueForge
      
  **Path:** `IssueForge/skill.md`
      
      Perfects tasks related to creating detailed, structured bug reports and feature requests for issue trackers like Jira or GitHub. Use when a user asks to handle git or requires assistance with issues..
      
  ### KubeCrafter
      
  **Path:** `KubeCrafter/skill.md`
      
      Perfects tasks related to writing Kubernetes manifests, configuring Helm charts, and managing cluster deployments and scaling rules. Use when a user asks to handle devops or requires assistance with k8s configs..
      
  ### LogicLens
      
  *Path:** `LogicLens/skill.md`
      
      Perfects tasks related to deconstructing complex business logic, simplifying nested conditionals, and refactoring convoluted code paths. Use when a user asks to handle code, summary or requires assistance with summarizes code functionality..
      
  ### MockSmith
      
  **Path:** `MockSmith/skill.md`
      
      Perfects tasks related to generating realistic mock data, stubbing API responses, and creating fake environments for robust frontend testing. Use when a user asks to handle testing or requires assistance with creates mock data..
      
  ### ModelSensei
      
  **Path:** `ModelSensei/skill.md`
      
      Perfects tasks related to designing domain-driven data models, ORM mappings, and enforcing strong typing across application layers. Use when a user asks to handle ml or requires assistance with model selection..
      
   ### PerfDetective
      
  **Path:** `PerfDetective/skill.md`
      
      Perfects tasks related to profiling application performance, identifying bottlenecks, and optimizing resource consumption for speed. Use when a user asks to handle performance or requires assistance with finds performance issues..
      
  ### PipelinePro
      
  **Path:** `PipelinePro/skill.md`
      
      Perfects tasks related to designing continuous integration and continuous deployment (CI/CD) pipelines, automating builds, and managing deployment strategies. Use when a user asks to handle devops or requires assistance with ci/cd..
      
  ### PolyglotShift
      
  **Path:** `PolyglotShift/skill.md`
      
      Perfects tasks related to translating code accurately between programming languages while preserving idiomatic conventions and logic. Use when a user asks to handle conversion or requires assistance with converts languages..
      
  ### PRMentor
      
  **Path:** `PRMentor/skill.md`
      
      Perfects tasks related to guiding developers through the pull request lifecycle, providing constructive feedback, and ensuring merge readiness. Use when a user asks to handle git or requires assistance with pr review..
      
  ### PromptForge
      
  **Path:** `PromptForge/skill.md`
      
      Perfects tasks related to crafting, refining, and optimizing LLM prompts to elicit highly specific, accurate, and structured AI responses. Use when a user asks to handle ai or requires assistance with prompt optimization..
      
  ### python-master
      
  **Path:** `python-master/SKILL.md`
      
      This skill should be used when the user asks to "fix code", "debug code", "build", or "create" python code. It is a comprehensive skill to efficiently build, debug, and fix Python code.
      
  ### QueryPulse
      
  **Path:** `QueryPulse/skill.md`
      
      Perfects tasks related to analyzing database query performance, optimizing indexes, and resolving slow or deadlocking database interactions. Use when a user asks to handle sql or requires assistance with optimizes sql..
      
  ### react-ranger
      
  **Path:** `react-ranger/SKILL.md`
      
      This skill should be used when the user asks to "build React", "create React", "fix React", "debug React", or "improve React". It specializes in creating, debugging, fixing, and improving React code with high efficiency, ensuring correct, clean, and production-ready output.
      
  ### ReadMeCraft
      
  **Path:** `ReadMeCraft/skill.md`
      
      Perfects tasks related to writing engaging, comprehensive README files, including setup instructions, usage examples, and contribution guidelines. Use when a user asks to handle docs or requires assistance with readme..
      
  ### RefactorX
      
  **Path:** `RefactorX/skill.md`
      
      Perfects tasks related to executing large-scale codebase refactoring, modernizing legacy systems, and improving overall maintainability. Use when a user asks to handle refactor or requires assistance with refactors code..
      
  ### RenderBoost
      
  **Path:** `RenderBoost/skill.md`
      
      Perfects tasks related to optimizing frontend rendering cycles, minimizing reflows/repaints, and improving Core Web Vitals. Use when a user asks to handle frontend or requires assistance with optimizes ui performance..
      
  ### ScrapeMaster
      
  **Path:** `ScrapeMaster/skill.md`
      
      Perfects tasks related to building resilient web scrapers, parsing DOM trees, and extracting structured data from unstructured web pages. Use when a user asks to handle automation or requires assistance with scraper..
      
  ### SecretSniffer
      
  **Path:** `SecretSniffer/skill.md`
      
      Perfects tasks related to auditing codebases for hardcoded credentials, API keys, and sensitive data exposures before commits. Use when a user asks to handle security or requires assistance with find secrets..
      
  ### SecureScan
      
  **Path:** `SecureScan/skill.md`
      
      Perfects tasks related to performing static application security testing (SAST), identifying vulnerabilities, and recommending secure coding practices. Use when a user asks to handle security or requires assistance with security audit..
      
  ### SEOMancer
      
  **Path:** `SEOMancer/skill.md`
      
      Perfects tasks related to optimizing technical SEO, managing meta tags, structured data, and improving web accessibility for search engines. Use when a user asks to handle frontend or requires assistance with seo..
      
  ### ServiceSplitter
      
  **Path:** `ServiceSplitter/skill.md`
      
      Perfects tasks related to decoupling monolithic applications into independent microservices and defining bounded contexts. Use when a user asks to handle architecture or requires assistance with microservices..
      
  ### SpeedSmith
      
  **Path:** `SpeedSmith/skill.md`
      
      Perfects tasks related to implementing aggressive caching strategies, optimizing asset delivery, and reducing application latency. Use when a user asks to handle optimization or requires assistance with optimizes code..
      
  ### StackWise
      
  **Path:** `StackWise/skill.md`
      
      Perfects tasks related to advising on technology stack selections, evaluating library trade-offs, and designing overarching technical strategies. Use when a user asks to handle architecture or requires assistance with tech stack advisor..
      
  ### TaskOrchestrator
      
  **Path:** `TaskOrchestrator/skill.md`
      
      Perfects tasks related to managing asynchronous task queues, worker pools, and orchestrating complex distributed workflows. Use when a user asks to handle agent or requires assistance with task planning..
      
  ### TestCrafter
      
  **Path:** `TestCrafter/skill.md`
      
      Perfects tasks related to writing unit and integration tests using modern testing frameworks, ensuring test reliability and speed. Use when a user asks to handle testing or requires assistance with creates unit tests..
      
  ### TraceMind
      
  **Path:** `TraceMind/skill.md`
      
      Perfects tasks related to implementing distributed tracing, structured logging, and observability tools to monitor system health. Use when a user asks to handle debug, logs or requires assistance with analyzes stack traces..
      
  ### UISmith
      
  **Path:** `UISmith/skill.md`
      
      Perfects tasks related to translating design mockups into pixel-perfect, accessible, and interactive frontend components. Use when a user asks to handle frontend or requires assistance with ui components..
      

## 🤖 Supported Models

* Claude (Anthropic)
* Gemini (Google)

---



## 🧱 Create Your Own Skill

```
skills/MySkill/skill.md
```

Then:

```bash
agent-skills sync
```

---

## 💥 Why This Exists

Prompt engineering is repetitive.

Agent Skills turns prompts into:

* reusable skills
* installable tools
* composable AI workflows

---

## 🚀 Roadmap

* [ ] Skill marketplace
* [ ] Web UI playground
* [ ] Streaming responses
* [ ] Skill chaining
* [ ] Memory system

---

## 🤝 Contributing

PRs welcome!

1. Fork repo
2. Add a skill
3. Submit PR

---

