"""
score.py - Auto-scores all skill files in the Agent-Skills repo.

Usage:
    python scripts/score.py          # Human-readable output
    python scripts/score.py --json   # JSON output

Criteria (each 0-5):
  1. Tool Coverage   - named tools/commands in backticks
  2. Code Examples   - fenced code blocks
  3. Edge Cases      - items in edge-case sections
  4. Actionability   - numbered/ordered workflow steps
  5. Structure       - presence of key sections
  6. Conciseness     - total line count
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_skill_files(repo_root: Path) -> list[Path]:
    """Return all skill.md / SKILL.md files under repo_root."""
    files: list[Path] = []
    for p in sorted(repo_root.iterdir()):
        if not p.is_dir():
            continue
        # skip hidden dirs and the scripts dir itself
        if p.name.startswith(".") or p.name == "scripts":
            continue
        for name in ("skill.md", "SKILL.md"):
            candidate = p / name
            if candidate.exists():
                files.append(candidate)
                break
    return files


# ---------------------------------------------------------------------------
# Scoring functions
# ---------------------------------------------------------------------------

def score_tool_coverage(text: str) -> int:
    """Count distinct backtick-delimited tokens that look like tool/command names."""
    # Match inline code spans: `something`
    # Exclude purely numeric tokens, plain words with spaces (prose), or very long strings
    raw = re.findall(r"`([^`\n]{1,80})`", text)
    tools: set[str] = set()
    for item in raw:
        item = item.strip()
        # Keep items that look like commands, flags, functions, or identifiers
        # Exclude JSON keys/values (contain quotes or colons with spaces)
        if re.search(r'[a-zA-Z]', item) and not re.search(r'^\s*["\'{]', item):
            tools.add(item)
    count = len(tools)
    if count == 0:
        return 0
    elif count <= 2:
        return 1
    elif count <= 5:
        return 2
    elif count <= 10:
        return 3
    elif count <= 15:
        return 4
    else:
        return 5


def score_code_examples(text: str) -> int:
    """Count fenced code blocks (``` ... ```)."""
    # Match opening fences with optional language tag
    count = len(re.findall(r"^```", text, re.MULTILINE))
    # Each block uses two fences; divide to get block count
    blocks = count // 2
    return min(blocks, 5)


def _edge_case_section(text: str) -> str:
    """Extract text of edge-case section(s), or empty string if none."""
    # Match sections whose heading contains 'edge case' (case-insensitive)
    pattern = re.compile(
        r"^#{1,4}\s+[^\n]*edge\s+case[s]?[^\n]*\n(.*?)(?=^#{1,4}\s|\Z)",
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    matches = pattern.findall(text)
    return "\n".join(matches)


def score_edge_cases(text: str) -> int:
    """Score based on edge-case section depth and quality."""
    section = _edge_case_section(text)
    if not section:
        return 0

    # Count list items (bullet or numbered)
    items = re.findall(r"^\s*[-*+\d]+[.)]\s+\S", section, re.MULTILINE)
    base_count = len(items)

    if base_count == 0:
        base = 0
    elif base_count == 1:
        base = 1
    elif base_count == 2:
        base = 2
    else:
        base = 3

    bonus = 0
    # Bonus: edge-case section contains a code example
    if re.search(r"```", section):
        bonus += 1
    # Bonus: names specific failure modes (error, fail, exception, timeout, invalid, corrupt, overflow, race)
    if re.search(
        r"\b(error|fail|exception|timeout|invalid|corrupt|overflow|race\s+condition|deadlock|nil|null|empty|missing)\b",
        section,
        re.IGNORECASE,
    ):
        bonus += 1

    return min(base + bonus, 5)


def score_actionability(text: str) -> int:
    """Count numbered/ordered workflow steps."""
    # Match lines like '1.', '2)', '### 1.', '**1.**' etc.
    # We look for explicit numbered list items at any indent level
    steps = re.findall(r"^\s*(?:#{1,4}\s+)?\d+[.)]\s+\S", text, re.MULTILINE)
    count = len(steps)
    if count == 0:
        return 0
    elif count <= 2:
        return 1
    elif count <= 5:
        return 2
    elif count <= 8:
        return 3
    elif count <= 12:
        return 4
    else:
        return 5


def score_structure(text: str) -> int:
    """Score based on presence of key structural elements."""
    score = 0
    # Frontmatter: YAML block at top
    if re.match(r"^\s*---\s*\n", text):
        score += 1
    # Overview / Domain Scope section
    if re.search(r"^#{1,3}\s+(overview|domain\s+scope|about|introduction)", text, re.IGNORECASE | re.MULTILINE):
        score += 1
    # Workflow section
    if re.search(r"^#{1,3}\s+workflow", text, re.IGNORECASE | re.MULTILINE):
        score += 1
    # Output format section
    if re.search(r"^#{1,3}\s+.*(output|format|response\s+format|deliverable)", text, re.IGNORECASE | re.MULTILINE):
        score += 1
    # Edge cases section
    if re.search(r"^#{1,4}\s+[^\n]*edge\s+case[s]?", text, re.IGNORECASE | re.MULTILINE):
        score += 1
    return score


def score_conciseness(lines: list[str]) -> int:
    """Score based on total line count."""
    count = len(lines)
    if 80 <= count <= 120:
        return 5
    elif (60 <= count < 80) or (120 < count <= 150):
        return 4
    elif (50 <= count < 60) or (150 < count <= 170):
        return 3
    elif 170 < count <= 200:
        return 2
    else:
        return 1


# ---------------------------------------------------------------------------
# Per-file scorer
# ---------------------------------------------------------------------------

CRITERIA = [
    "tool_coverage",
    "code_examples",
    "edge_cases",
    "actionability",
    "structure",
    "conciseness",
]

CRITERIA_LABELS = {
    "tool_coverage": "Tool Coverage",
    "code_examples": "Code Examples",
    "edge_cases":    "Edge Cases",
    "actionability": "Actionability",
    "structure":     "Structure",
    "conciseness":   "Conciseness",
}


def score_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    scores = {
        "tool_coverage": score_tool_coverage(text),
        "code_examples": score_code_examples(text),
        "edge_cases":    score_edge_cases(text),
        "actionability": score_actionability(text),
        "structure":     score_structure(text),
        "conciseness":   score_conciseness(lines),
    }
    total = sum(scores.values())
    return {
        "skill": path.parent.name,
        "file": str(path),
        "line_count": len(lines),
        "scores": scores,
        "total": total,
    }


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

COL_W = 14   # width for each criterion column
NAME_W = 22  # width for skill name


def _fmt_header() -> str:
    parts = [f"{'Skill':<{NAME_W}}"]
    for c in CRITERIA:
        label = CRITERIA_LABELS[c][:COL_W]
        parts.append(f"{label:>{COL_W}}")
    parts.append(f"{'Total':>{COL_W}}")
    return "  ".join(parts)


def _fmt_row(result: dict) -> str:
    name = result["skill"][:NAME_W]
    parts = [f"{name:<{NAME_W}}"]
    for c in CRITERIA:
        parts.append(f"{result['scores'][c]:>{COL_W}}")
    parts.append(f"{result['total']:>{COL_W}}")
    return "  ".join(parts)


def _separator(char: str = "-") -> str:
    total_width = NAME_W + (COL_W + 2) * (len(CRITERIA) + 1)
    return char * total_width


def print_histogram(results: list[dict]) -> None:
    totals = [r["total"] for r in results]
    max_total = 30
    bin_size = 5
    bins: dict[int, int] = {}
    for t in totals:
        b = (t // bin_size) * bin_size
        bins[b] = bins.get(b, 0) + 1

    print("\nScore Distribution:")
    bar_max = max(bins.values()) if bins else 1
    bar_scale = 30  # max bar width in chars
    for b in range(0, max_total + 1, bin_size):
        count = bins.get(b, 0)
        bar_len = int(count / bar_max * bar_scale) if bar_max else 0
        bar = "#" * bar_len
        label = f"{b:2d}-{b+bin_size-1:2d}"
        print(f"  {label} | {bar:<{bar_scale}} {count}")


def print_results(results: list[dict]) -> None:
    sorted_results = sorted(results, key=lambda r: r["total"])

    print(_separator("="))
    print("Agent-Skills Scorer  (max 30 points per skill)")
    print(_separator("="))
    print()
    print(_fmt_header())
    print(_separator())

    for r in sorted_results:
        print(_fmt_row(r))

    print(_separator())

    totals = [r["total"] for r in results]
    avg = sum(totals) / len(totals) if totals else 0
    mn = min(totals) if totals else 0
    mx = max(totals) if totals else 0

    print(f"\nSkills scored : {len(results)}")
    print(f"Average score : {avg:.1f} / 30")
    print(f"Min score     : {mn} / 30  ({next(r['skill'] for r in results if r['total'] == mn)})")
    print(f"Max score     : {mx} / 30  ({next(r['skill'] for r in sorted_results[::-1] if r['total'] == mx)})")

    print_histogram(sorted_results)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Score all skill files in the Agent-Skills repo."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of a human-readable table.",
    )
    args = parser.parse_args()

    # Resolve repo root: script lives at <repo>/scripts/score.py
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent

    skill_files = find_skill_files(repo_root)
    if not skill_files:
        print("No skill files found.", file=sys.stderr)
        sys.exit(1)

    results = [score_file(f) for f in skill_files]

    if args.json:
        totals = [r["total"] for r in results]
        output = {
            "repo": str(repo_root),
            "skills_scored": len(results),
            "summary": {
                "average": round(sum(totals) / len(totals), 2) if totals else 0,
                "min": min(totals) if totals else 0,
                "max": max(totals) if totals else 0,
            },
            "results": sorted(results, key=lambda r: r["total"]),
        }
        print(json.dumps(output, indent=2))
    else:
        print_results(results)


if __name__ == "__main__":
    main()
