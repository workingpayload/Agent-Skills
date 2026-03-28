"""
build_index.py — Generate skills.json and skills-routing.json indexes.

Run from the repo root:
    python scripts/build_index.py
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_FILENAMES = {"skill.md", "SKILL.md"}

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "security": [
        "security", "vulnerabilit", "owasp", "sast", "cve", "pentest",
        "exploit", "injection", "xss", "csrf", "auth", "encryption",
        "secret", "credential", "scan", "audit",
    ],
    "testing": [
        "test", "coverage", "jest", "pytest", "junit", "vitest",
        "mock", "assertion", "tdd", "bdd", "e2e", "integration test",
        "unit test", "fixture",
    ],
    "frontend": [
        "react", "vue", "angular", "svelte", "ui", "ux", "css",
        "html", "component", "frontend", "browser", "dom", "tailwind",
        "design system", "layout", "animation", "rendering", "client-side",
        "web app",
    ],
    "devops": [
        "docker", "kubernetes", "k8s", "ci/cd", "pipeline", "deploy",
        "containeriz", "helm", "terraform", "ansible", "devops",
        "infra", "infrastructure", "cloud", "aws", "gcp", "azure",
        "cron", "workflow", "automation",
    ],
    "database": [
        "database", "sql", "nosql", "postgresql", "mysql", "mongo",
        "redis", "query", "schema", "migration", "orm", "index",
        "data model", "db ",
    ],
    "architecture": [
        "architect", "microservice", "monolith", "design pattern",
        "system design", "ddd", "event-driven", "cqrs", "saga",
        "service mesh", "api design", "rest", "graphql", "grpc",
        "scalab", "distributed",
    ],
    "docs": [
        "document", "readme", "changelog", "wiki", "api doc",
        "openapi", "swagger", "comment", "annotation", "spec",
        "write", "writing",
    ],
    "git": [
        "git", "commit", "pull request", "pr ", "branch", "merge",
        "rebase", "diff", "repository", "version control",
    ],
    "performance": [
        "performance", "optim", "profil", "speed", "latency",
        "throughput", "cache", "benchmark", "memory", "cpu",
        "bottleneck", "render boost", "faster",
    ],
    "ai/ml": [
        "machine learning", "ml", "model", "neural", "llm",
        "ai ", "nlp", "embedding", "training", "inference",
        "prompt", "rag", "vector", "dataset",
    ],
}


# ---------------------------------------------------------------------------
# Frontmatter parser (stdlib only — no PyYAML)
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Return (frontmatter_dict, body_text). Handles only simple key: value pairs."""
    fm: dict[str, str] = {}
    body = text

    if text.startswith("---"):
        # Find the closing ---
        end = text.find("\n---", 3)
        if end != -1:
            fm_block = text[3:end].strip()
            body = text[end + 4:].lstrip("\n")
            for line in fm_block.splitlines():
                if ":" in line:
                    key, _, value = line.partition(":")
                    fm[key.strip().lower()] = value.strip()

    return fm, body


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

def extract_triggers(description: str) -> list[str]:
    """Pull keywords from the phrase after 'Use when' in a description."""
    triggers: list[str] = []

    # Match "Use when <phrase>" — may end at period, comma, or end of string
    match = re.search(r"[Uu]se when\s+(.+?)(?:\.|$)", description)
    if not match:
        return triggers

    phrase = match.group(1)

    # Strip common stop-words and split into meaningful tokens
    stop_words = {
        "a", "an", "the", "to", "is", "in", "on", "of", "or", "and",
        "for", "with", "that", "this", "are", "be", "it", "as", "by",
        "at", "from", "up", "asked", "asks", "needs", "need", "wants",
        "want", "user", "users", "how", "has", "have", "set",
    }

    # Extract individual words; also keep short multi-word tech terms
    words = re.findall(r"[a-z][a-z0-9+#\-\.]*", phrase.lower())
    for w in words:
        if len(w) >= 3 and w not in stop_words:
            triggers.append(w)

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for t in triggers:
        if t not in seen:
            seen.add(t)
            unique.append(t)

    return unique


def auto_categorize(description: str) -> list[str]:
    """Return category labels whose keyword lists match the description."""
    desc_lower = description.lower()
    matched: list[str] = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in desc_lower for kw in keywords):
            matched.append(category)
    return matched


def extract_tools(body: str) -> list[str]:
    """Return unique tool/command names found inside backticks."""
    # Match `something` — filter out multi-line code fences
    raw = re.findall(r"`([^`\n]+)`", body)
    tools: list[str] = []
    seen: set[str] = set()
    for item in raw:
        item = item.strip()
        # Keep plausible tool names: short, no spaces (or simple flags/paths)
        if item and len(item) <= 60 and item not in seen:
            seen.add(item)
            tools.append(item)
    return tools


# ---------------------------------------------------------------------------
# Per-file processing
# ---------------------------------------------------------------------------

def process_skill_file(skill_file: Path) -> dict:
    """Parse a single skill.md / SKILL.md and return a record dict."""
    text = skill_file.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    line_count = len(lines)
    has_code_examples = "```" in text

    fm, body = parse_frontmatter(text)

    directory = skill_file.parent.name
    name = fm.get("name") or directory
    description = fm.get("description", "")

    # Relative path uses forward slashes for portability
    rel_path = skill_file.relative_to(REPO_ROOT).as_posix()

    triggers = extract_triggers(description)
    categories = auto_categorize(description)
    tools_mentioned = extract_tools(body)

    return {
        "name": name,
        "description": description,
        "path": rel_path,
        "directory": directory,
        "triggers": triggers,
        "categories": categories,
        "line_count": line_count,
        "has_code_examples": has_code_examples,
        "tools_mentioned": tools_mentioned,
    }


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def find_skill_files(root: Path) -> list[Path]:
    """Find all skill.md / SKILL.md files under root (one level of subdirs)."""
    found: list[Path] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        # Skip hidden dirs and scripts/
        if child.name.startswith(".") or child.name == "scripts":
            continue
        for fname in SKILL_FILENAMES:
            candidate = child / fname
            if candidate.is_file():
                found.append(candidate)
                break  # take only the first match per directory
    return found


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    skill_files = find_skill_files(REPO_ROOT)

    if not skill_files:
        print("WARNING: No skill files found under", REPO_ROOT, file=sys.stderr)

    skills = [process_skill_file(f) for f in skill_files]
    skills.sort(key=lambda s: s["name"].lower())

    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # --- Full index ---
    full_index = {
        "version": "1.0",
        "generated_at": timestamp,
        "skill_count": len(skills),
        "skills": skills,
    }

    full_path = REPO_ROOT / "skills.json"
    full_path.write_text(
        json.dumps(full_index, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Written: {full_path}  ({len(skills)} skills)")

    # --- Compact routing index ---
    routing_skills = [
        {
            "name": s["name"],
            "description": s["description"],
            "categories": s["categories"],
            "triggers": s["triggers"],
        }
        for s in skills
    ]

    routing_index = {
        "version": "1.0",
        "generated_at": timestamp,
        "skill_count": len(skills),
        "skills": routing_skills,
    }

    routing_path = REPO_ROOT / "skills-routing.json"
    routing_path.write_text(
        json.dumps(routing_index, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Written: {routing_path}")


if __name__ == "__main__":
    main()
