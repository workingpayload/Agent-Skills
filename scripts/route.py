#!/usr/bin/env python3
"""
route.py — Skill router for Agent-Skills repository.

Routes a user prompt to the best-matching skill using TF-IDF-like keyword
matching against skills-routing.json. No external dependencies required.

Usage:
    python scripts/route.py "review my code"
    python scripts/route.py "fix my Docker build" --top-n 5
    python scripts/route.py "write unit tests" --json
    python scripts/route.py --interactive
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Stop words — common English words that carry no signal for skill matching
# ---------------------------------------------------------------------------
STOP_WORDS = frozenset(
    [
        "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "must", "shall", "can", "need",
        "i", "me", "my", "we", "our", "you", "your", "it", "its", "they",
        "them", "their", "this", "that", "these", "those", "what", "which",
        "who", "how", "when", "where", "why", "not", "no", "so", "if",
        "then", "than", "as", "up", "out", "about", "into", "through",
        "help", "please", "want", "need", "like", "just", "some", "any",
        "all", "new", "get", "make", "use", "using", "used",
    ]
)

# Minimum score to consider a match meaningful
SCORE_THRESHOLD = 1.0


def tokenize(text: str) -> list[str]:
    """
    Lowercase the text, split on non-alphanumeric characters (preserving
    hyphens within words), and remove stop words.
    """
    # Replace hyphens surrounded by word chars with a placeholder so
    # "big-o" stays as one token, then split on remaining punctuation.
    tokens = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", text.lower())
    return [t for t in tokens if t not in STOP_WORDS]


def find_index(index_path: str | None) -> Path:
    """Locate skills-routing.json, falling back to the repo root."""
    if index_path:
        p = Path(index_path)
        if not p.exists():
            sys.exit(f"Error: index file not found: {index_path}")
        return p

    # Walk up from this script's location to find the repo root
    here = Path(__file__).resolve().parent
    candidates = [
        here / "skills-routing.json",
        here.parent / "skills-routing.json",
    ]
    for c in candidates:
        if c.exists():
            return c

    sys.exit(
        "Error: could not find skills-routing.json. "
        "Pass --index <path> to specify its location."
    )


def load_index(path: Path) -> list[dict[str, Any]]:
    """Load and return the list of skill entries from the index file."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    skills = data.get("skills")
    if not isinstance(skills, list):
        sys.exit("Error: skills-routing.json must contain a top-level 'skills' list.")
    return skills


def score_skill(
    prompt_tokens: list[str], skill: dict[str, Any]
) -> tuple[float, list[str]]:
    """
    Compute a relevance score for one skill given the prompt tokens.

    Weights:
        trigger match  → 4x per token
        name match     → 3x per token
        category match → 2x per token
        description match (exact word) → 2x per token
        description match (substring)  → 1x per token

    Returns (score, matched_keywords).
    """
    name: str = skill.get("name", "")
    description: str = skill.get("description", "")
    categories: list[str] = skill.get("categories", [])
    triggers: list[str] = skill.get("triggers", [])

    name_tokens = set(tokenize(name))
    desc_tokens = set(tokenize(description))
    # Flatten categories into a single token set
    cat_tokens: set[str] = set()
    for cat in categories:
        cat_tokens.update(tokenize(cat))
    trigger_tokens = set(triggers)  # triggers are already lowercase words

    desc_lower = description.lower()

    score = 0.0
    matched: list[str] = []

    for token in set(prompt_tokens):  # deduplicate prompt tokens for scoring
        hit = False

        # Trigger match (4x)
        if token in trigger_tokens:
            score += 4.0
            matched.append(f"{token} (trigger)")
            hit = True

        # Name match (3x)
        if token in name_tokens:
            score += 3.0
            if not hit:
                matched.append(f"{token} (name)")
            hit = True

        # Category match (2x)
        if token in cat_tokens:
            score += 2.0
            if not hit:
                matched.append(f"{token} (category)")
            hit = True

        # Description exact-word match (2x)
        if token in desc_tokens:
            score += 2.0
            if not hit:
                matched.append(f"{token} (description)")
            hit = True

        # Description substring match (1x) — only if not already matched above
        if not hit and token in desc_lower:
            score += 1.0
            matched.append(f"{token} (partial)")

    return score, matched


def route(
    prompt: str,
    skills: list[dict[str, Any]],
    top_n: int,
) -> list[dict[str, Any]]:
    """
    Score every skill against the prompt and return top-N results,
    sorted by descending score.

    Each result dict has keys: rank, name, score, matched_keywords.
    """
    prompt_tokens = tokenize(prompt)

    if not prompt_tokens:
        return []

    scored: list[tuple[float, list[str], dict[str, Any]]] = []
    for skill in skills:
        score, matched = score_skill(prompt_tokens, skill)
        if score > 0:
            scored.append((score, matched, skill))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for rank, (score, matched, skill) in enumerate(scored[:top_n], start=1):
        results.append(
            {
                "rank": rank,
                "name": skill.get("name", ""),
                "score": round(score, 2),
                "matched_keywords": matched,
            }
        )
    return results


def format_text(results: list[dict[str, Any]], prompt: str) -> str:
    """Render results as a human-readable ranked list."""
    lines: list[str] = []

    if not results:
        lines.append(
            "No matching skill found for your prompt.\n"
            "Try describing your task more specifically — for example:\n"
            '  • "review my Python code for security issues"\n'
            '  • "write unit tests for my REST API"\n'
            '  • "fix a Docker build error"'
        )
        return "\n".join(lines)

    top_score = results[0]["score"]
    if top_score < SCORE_THRESHOLD:
        lines.append(
            f"No confident match found (best score: {top_score}). "
            "Try describing your task differently, e.g.:\n"
            '  • "write unit tests" → testcrafter\n'
            '  • "review my code" → codesage\n'
            '  • "fix a Docker build" → dockmaster'
        )
        return "\n".join(lines)

    lines.append(f'Routing: "{prompt}"\n')
    lines.append(f"{'Rank':<5} {'Skill':<25} {'Score':<8} Why it matched")
    lines.append("-" * 72)
    for r in results:
        keywords = ", ".join(r["matched_keywords"]) if r["matched_keywords"] else "—"
        lines.append(
            f"{r['rank']:<5} {r['name']:<25} {r['score']:<8.2f} {keywords}"
        )

    return "\n".join(lines)


def format_json(results: list[dict[str, Any]], prompt: str) -> str:
    """Render results as JSON."""
    payload = {
        "prompt": prompt,
        "results": results,
        "no_match": not results or results[0]["score"] < SCORE_THRESHOLD,
    }
    return json.dumps(payload, indent=2)


def run_once(
    prompt: str,
    skills: list[dict[str, Any]],
    top_n: int,
    as_json: bool,
) -> None:
    results = route(prompt, skills, top_n)
    if as_json:
        print(format_json(results, prompt))
    else:
        print(format_text(results, prompt))


def interactive_loop(
    skills: list[dict[str, Any]],
    top_n: int,
    as_json: bool,
) -> None:
    print("Agent-Skills Router — interactive mode (Ctrl-C or 'quit' to exit)\n")
    while True:
        try:
            prompt = input("prompt> ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if prompt.lower() in {"quit", "exit", "q"}:
            break
        if not prompt:
            continue

        run_once(prompt, skills, top_n, as_json)
        print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="route.py",
        description="Route a user prompt to the best-matching Agent-Skills skill.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/route.py "review my code"
  python scripts/route.py "fix my Docker build" --top-n 5
  python scripts/route.py "write unit tests" --json
  python scripts/route.py "design a REST API" -n 3
  python scripts/route.py --interactive
""",
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default=None,
        help="The user prompt/query to route (omit when using --interactive).",
    )
    parser.add_argument(
        "--top-n", "-n",
        type=int,
        default=3,
        dest="top_n",
        metavar="N",
        help="Number of top results to display (default: 3).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output results as JSON.",
    )
    parser.add_argument(
        "--index",
        default=None,
        metavar="PATH",
        help="Path to skills-routing.json (default: auto-detect from repo root).",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Start an interactive prompt loop.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.interactive and args.prompt is None:
        parser.error("A prompt argument is required unless --interactive is used.")

    index_path = find_index(args.index)
    skills = load_index(index_path)

    if args.top_n < 1:
        parser.error("--top-n must be at least 1.")

    if args.interactive:
        interactive_loop(skills, args.top_n, args.as_json)
    else:
        run_once(args.prompt, skills, args.top_n, args.as_json)


if __name__ == "__main__":
    main()
