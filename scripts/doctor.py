#!/usr/bin/env python3
"""
doctor.py - Health check for installed Agent Skills.

Checks Claude (~/.claude/commands/) and/or Gemini (~/.gemini/commands/)
install directories for integrity, staleness, orphans, and format issues.

Usage:
    python scripts/doctor.py                   # check both targets
    python scripts/doctor.py --target claude   # check Claude only
    python scripts/doctor.py --target gemini   # check Gemini only

Exit codes:
    0 = all healthy
    1 = warnings only
    2 = errors found
"""

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SKILL_FILENAMES = {"skill.md", "SKILL.md"}
META_FILENAME = ".skills-meta.json"

INSTALL_DIRS = {
    "claude": Path.home() / ".claude" / "commands",
    "gemini": Path.home() / ".gemini" / "commands",
    "antigravity": Path.home() / ".gemini" / "antigravity" / "skills",
}


# ---------------------------------------------------------------------------
# Severity levels
# ---------------------------------------------------------------------------

OK = "OK"
WARN = "WARN"
ERROR = "ERROR"


class CheckResult:
    def __init__(self, label: str, status: str, message: str, recommendation: str = ""):
        self.label = label
        self.status = status
        self.message = message
        self.recommendation = recommendation

    @property
    def icon(self) -> str:
        return {"OK": "[OK]", "WARN": "[WARN]", "ERROR": "[ERROR]"}[self.status]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def file_hash(path: Path) -> str:
    """Return MD5 hex digest of a file's content."""
    h = hashlib.md5()
    h.update(path.read_bytes())
    return h.hexdigest()


def content_hash(text: str) -> str:
    """Return MD5 hex digest of a UTF-8 string."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def parse_frontmatter(text: str) -> dict | None:
    """
    Parse YAML frontmatter delimited by '---'.
    Returns dict of fields or None if not present.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    end = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break
    if end is None:
        return None
    fields: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields


def find_source_skill(repo_root: Path, skill_name: str) -> Path | None:
    """
    Locate the source skill file in the repo by skill name (case-insensitive
    match against directory names).
    """
    for subdir in repo_root.iterdir():
        if not subdir.is_dir():
            continue
        for fname in SKILL_FILENAMES:
            candidate = subdir / fname
            if candidate.is_file():
                # Try matching by directory name or by frontmatter name
                if subdir.name.lower() == skill_name.lower():
                    return candidate
                # Also try reading frontmatter
                try:
                    fields = parse_frontmatter(candidate.read_text(encoding="utf-8", errors="replace"))
                    if fields and fields.get("name", "").lower() == skill_name.lower():
                        return candidate
                except OSError:
                    pass
    return None


# ---------------------------------------------------------------------------
# Individual health checks
# ---------------------------------------------------------------------------

def check_install_dir(install_dir: Path) -> CheckResult:
    """Check a: install directory exists."""
    if install_dir.is_dir():
        return CheckResult(
            "Install directory",
            OK,
            f"Found: {install_dir}",
        )
    return CheckResult(
        "Install directory",
        ERROR,
        f"Missing: {install_dir}",
        recommendation="Run `python scripts/install.py` to create the install directory and install skills.",
    )


def check_meta_file(install_dir: Path) -> tuple[CheckResult, dict | None]:
    """Check b: .skills-meta.json exists and is valid JSON."""
    meta_path = install_dir / META_FILENAME
    if not meta_path.is_file():
        return (
            CheckResult(
                "Meta file",
                ERROR,
                f"Missing: {meta_path}",
                recommendation="Run `python scripts/install.py` to install skills and generate the meta file.",
            ),
            None,
        )
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        return (
            CheckResult("Meta file", OK, f"Found: {meta_path}"),
            meta,
        )
    except json.JSONDecodeError as exc:
        return (
            CheckResult(
                "Meta file",
                ERROR,
                f"Invalid JSON in {meta_path}: {exc}",
                recommendation=f"Delete {meta_path} and run `python scripts/install.py` to regenerate it.",
            ),
            None,
        )


def check_file_integrity(install_dir: Path, meta: dict) -> list[CheckResult]:
    """Check c: every skill recorded in meta still exists on disk."""
    results: list[CheckResult] = []
    # Support both formats: {"skills": {...}} (Python installer) and {name: {...}} (Node CLI)
    skills = meta.get("skills", None)
    if skills is None:
        # Node CLI format: top-level keys are skill names
        skills = {k: v for k, v in meta.items() if isinstance(v, dict)}
    if not skills:
        results.append(
            CheckResult(
                "File integrity",
                WARN,
                "Meta file contains no tracked skills.",
                recommendation="Run `python scripts/install.py` to reinstall skills.",
            )
        )
        return results

    for skill_name, info in skills.items():
        filename = info.get("filename", f"{skill_name}.md")
        skill_path = install_dir / filename
        if skill_path.is_file():
            results.append(
                CheckResult(
                    f"File integrity [{skill_name}]",
                    OK,
                    f"Present: {skill_path.name}",
                )
            )
        else:
            results.append(
                CheckResult(
                    f"File integrity [{skill_name}]",
                    ERROR,
                    f"Missing file: {skill_path}",
                    recommendation=f"Run `python scripts/install.py --force` to reinstall missing skills.",
                )
            )
    return results


def check_stale(install_dir: Path, meta: dict, repo_root: Path) -> list[CheckResult]:
    """Check d: installed skill content matches source repo version."""
    results: list[CheckResult] = []
    # Support both formats
    skills = meta.get("skills", None)
    if skills is None:
        skills = {k: v for k, v in meta.items() if isinstance(v, dict)}

    for skill_name, info in skills.items():
        filename = info.get("filename", f"{skill_name}.md")
        skill_path = install_dir / filename
        if not skill_path.is_file():
            # Already flagged by file integrity check — skip
            continue

        # Use source path from meta if available (Node CLI stores it as "source")
        source_path_str = info.get("source_path") or info.get("source")
        source_path = Path(source_path_str) if source_path_str and Path(source_path_str).is_file() else find_source_skill(repo_root, skill_name)
        if source_path is None:
            results.append(
                CheckResult(
                    f"Stale check [{skill_name}]",
                    WARN,
                    f"Source skill '{skill_name}' not found in repo — cannot compare.",
                    recommendation="Verify the skill exists in the source repo or remove it from the install directory.",
                )
            )
            continue

        installed_hash = file_hash(skill_path)
        source_hash = file_hash(source_path)

        # Also compare against hash stored in meta (if present)
        meta_hash = info.get("hash", "")

        if installed_hash == source_hash:
            results.append(
                CheckResult(
                    f"Stale check [{skill_name}]",
                    OK,
                    "Up to date with source repo.",
                )
            )
        else:
            results.append(
                CheckResult(
                    f"Stale check [{skill_name}]",
                    WARN,
                    f"Installed version differs from source repo ({source_path.relative_to(repo_root)}).",
                    recommendation="Run `python scripts/install.py --force` to update stale skills.",
                )
            )

    return results


def check_orphans(install_dir: Path, meta: dict) -> list[CheckResult]:
    """Check e: files in install dir that aren't tracked in meta."""
    results: list[CheckResult] = []
    # Support both formats
    skills = meta.get("skills", None)
    if skills is None:
        skills = {k: v for k, v in meta.items() if isinstance(v, dict)}
    tracked_filenames = {
        info.get("filename", f"{name}.md") for name, info in skills.items()
    }
    # Also always ignore the meta file itself
    tracked_filenames.add(META_FILENAME)

    try:
        entries = list(install_dir.iterdir())
    except OSError:
        return results

    orphans = [
        e for e in entries
        if e.is_file() and e.name not in tracked_filenames
    ]

    if not orphans:
        results.append(
            CheckResult("Orphan detection", OK, "No untracked files found.")
        )
    else:
        for orphan in sorted(orphans):
            results.append(
                CheckResult(
                    f"Orphan [{orphan.name}]",
                    WARN,
                    f"Untracked file in install directory: {orphan.name}",
                    recommendation=(
                        f"Remove manually (`del \"{orphan}\"` on Windows / `rm \"{orphan}\"` on Unix) "
                        "or run `python scripts/install.py` to regenerate a clean install."
                    ),
                )
            )
    return results


def check_format(install_dir: Path, meta: dict) -> list[CheckResult]:
    """Check f: each installed skill has frontmatter with name and description."""
    results: list[CheckResult] = []
    # Support both formats
    skills = meta.get("skills", None)
    if skills is None:
        skills = {k: v for k, v in meta.items() if isinstance(v, dict)}

    for skill_name, info in skills.items():
        filename = info.get("filename", f"{skill_name}.md")
        skill_path = install_dir / filename
        if not skill_path.is_file():
            continue

        try:
            text = skill_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            results.append(
                CheckResult(
                    f"Format [{skill_name}]",
                    ERROR,
                    f"Cannot read file: {exc}",
                )
            )
            continue

        fields = parse_frontmatter(text)
        issues: list[str] = []
        if fields is None:
            issues.append("missing frontmatter")
        else:
            if "name" not in fields:
                issues.append("frontmatter missing 'name'")
            if "description" not in fields:
                issues.append("frontmatter missing 'description'")
            elif len(fields["description"]) < 20:
                issues.append("description is too short (< 20 chars)")

        if issues:
            results.append(
                CheckResult(
                    f"Format [{skill_name}]",
                    WARN,
                    f"Format issues: {', '.join(issues)}",
                    recommendation=(
                        "Edit the installed skill file to add valid YAML frontmatter, "
                        "or run `python scripts/install.py --force` to reinstall from source."
                    ),
                )
            )
        else:
            results.append(
                CheckResult(f"Format [{skill_name}]", OK, "Frontmatter valid.")
            )

    return results


def check_source_repo(repo_root: Path) -> CheckResult:
    """Check g: source repo is accessible from the current directory."""
    marker_candidates = [
        repo_root / "skills.json",
        repo_root / "scripts" / "validate.py",
        repo_root / "scripts" / "install.py",
    ]
    # Count how many markers exist
    found = [p for p in marker_candidates if p.exists()]

    if len(found) >= 1:
        skill_dirs = [
            d for d in repo_root.iterdir()
            if d.is_dir() and any((d / f).is_file() for f in SKILL_FILENAMES)
        ]
        return CheckResult(
            "Source repo",
            OK,
            f"Accessible at {repo_root} ({len(skill_dirs)} skill(s) found).",
        )
    return CheckResult(
        "Source repo",
        WARN,
        f"Source repo markers not found under {repo_root}.",
        recommendation=(
            "Run doctor.py from inside the Agent-Skills repository root, "
            "or verify the repo directory is correct."
        ),
    )


# ---------------------------------------------------------------------------
# Per-target runner
# ---------------------------------------------------------------------------

def run_checks_for_target(target: str, install_dir: Path, repo_root: Path) -> list[CheckResult]:
    """Run all health checks for one target (claude or gemini)."""
    results: list[CheckResult] = []

    # (a) Install directory exists
    dir_result = check_install_dir(install_dir)
    results.append(dir_result)
    if dir_result.status == ERROR:
        # Nothing else to check if the directory is absent
        return results

    # (b) Meta file exists
    meta_result, meta = check_meta_file(install_dir)
    results.append(meta_result)
    if meta is None:
        # Cannot run remaining per-skill checks without meta
        return results

    # (c) File integrity
    results.extend(check_file_integrity(install_dir, meta))

    # (d) Stale check
    results.extend(check_stale(install_dir, meta, repo_root))

    # (e) Orphan detection
    results.extend(check_orphans(install_dir, meta))

    # (f) Format validation
    results.extend(check_format(install_dir, meta))

    return results


# ---------------------------------------------------------------------------
# Output / reporting
# ---------------------------------------------------------------------------

def print_section(title: str, results: list[CheckResult]) -> tuple[int, int, int]:
    """Print a section of results. Returns (ok, warnings, errors)."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")

    ok = warn = err = 0
    for r in results:
        print(f"  {r.icon:<9} {r.label}: {r.message}")
        if r.recommendation:
            print(f"           -> {r.recommendation}")
        if r.status == OK:
            ok += 1
        elif r.status == WARN:
            warn += 1
        else:
            err += 1

    return ok, warn, err


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Health check for installed Agent Skills."
    )
    parser.add_argument(
        "--target", "-t",
        choices=["claude", "gemini", "antigravity"],
        default=None,
        help="Which install target to check (default: all).",
    )
    args = parser.parse_args()

    targets = [args.target] if args.target else ["claude", "gemini", "antigravity"]

    repo_root = Path(__file__).resolve().parent.parent

    total_ok = total_warn = total_err = 0

    # (g) Source repo check — done once, shown at top
    print("\nAgent Skills Doctor")
    print("=" * 70)
    source_result = check_source_repo(repo_root)
    print(f"  {source_result.icon:<9} {source_result.label}: {source_result.message}")
    if source_result.recommendation:
        print(f"           -> {source_result.recommendation}")
    if source_result.status == OK:
        total_ok += 1
    elif source_result.status == WARN:
        total_warn += 1
    else:
        total_err += 1

    for target in targets:
        install_dir = INSTALL_DIRS[target]
        results = run_checks_for_target(target, install_dir, repo_root)
        ok, warn, err = print_section(
            f"Target: {target.upper()}  ({install_dir})",
            results,
        )
        total_ok += ok
        total_warn += warn
        total_err += err

    # Summary
    print(f"\n{'=' * 70}")
    print(f"  SUMMARY")
    print(f"{'=' * 70}")
    print(f"  Checks run : {total_ok + total_warn + total_err}")
    print(f"  [OK]       : {total_ok}")
    print(f"  [WARN]     : {total_warn}")
    print(f"  [ERROR]    : {total_err}")
    print()

    if total_err == 0 and total_warn == 0:
        print("  All skills are healthy.")
    elif total_err == 0:
        print("  Skills have warnings — review recommendations above.")
    else:
        print("  Skills have errors — action required.")

    print()

    if total_err > 0:
        return 2
    if total_warn > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
