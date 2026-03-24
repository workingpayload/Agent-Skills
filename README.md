# 🧠 Agent Skills

> Install and run AI-powered developer skills across Claude, Gemini, and OpenAI.

⚡ Turn prompts into reusable, installable skills
⚡ Works from CLI in seconds
⚡ Built for developers

---

## 🚀 Quick Start

```bash
npx agent-skills install
agent-skills run "optimize this SQL query"
```

---

## ✨ Features

* 🧠 50+ prebuilt developer skills
* 🤖 Multi-LLM support (Claude, Gemini, OpenAI)
* ⚡ Auto skill routing (no manual selection)
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
agent-skills run "optimize this code"
```

### Explain code from file

```bash
agent-skills run "explain this code" --file app.js
```

### Use specific model

```bash
agent-skills run "design api" -gemini
agent-skills run "review this PR" -claude
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
| -openai | Use OpenAI (default) |
| --file  | Load file input      |
| --input | Load text file       |
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

## 🧠 How It Works

1. You run a query
2. Router selects best skill
3. Prompt is generated
4. LLM executes it
5. Output is returned

---

## 🤖 Supported Models

* OpenAI (GPT)
* Claude (Anthropic)
* Gemini (Google)

---

## 🛠 Programmatic Usage

```js
const { runWithOpenAI } = require("agent-skills");

const res = await runWithOpenAI(
  "optimize this code",
  { code: "for(let i=0;i<100000;i++){}" }
);

console.log(res);
```

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

