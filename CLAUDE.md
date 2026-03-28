# Agent Skills

## Project Overview
This is a collection of 54 AI-powered developer skills for Claude and Gemini. Each skill is a markdown file in its own directory that instructs an AI agent how to perform a specific task (code review, debugging, testing, etc.).

## Repository Structure
- Each skill lives in its own directory (e.g., `CodeSage/skill.md`)
- Skills use frontmatter format with `name` and `description` fields
- The `scripts/` directory contains quality tooling

## Skill Format
Every skill file must have:
- YAML frontmatter with `name` (lowercase) and `description` (50+ chars)
- Overview section explaining the skill's purpose
- Numbered workflow steps with concrete instructions
- Named tools with exact commands
- Edge cases section (2-3 real-world failure scenarios)
- Output format section

## Quality Standards
- Target line count: 80-150 lines
- No generic filler phrases ("Apply the core logic", "Strive for flawless")
- Every claim must name a specific tool, framework, or standard
- Code examples must be runnable, not pseudocode

## Scripts
- `python scripts/validate.py` — Lint all skills (CI gate)
- `python scripts/score.py` — Auto-score skills (quality tracking)
- `python scripts/build_index.py` — Generate skills.json index
- `python scripts/test_skill.py` — Adversarial test harness

## When Editing Skills
1. Run `python scripts/validate.py` before committing
2. Keep skills under 160 lines
3. Add frontmatter if missing
4. Include at least 3 edge cases per skill
5. Name specific tools — never say "use appropriate tools"
