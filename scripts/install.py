#!/usr/bin/env python3
"""
install.py - Install Agent Skills to Claude or Gemini commands directories.

Usage:
    python scripts/install.py                          # install all skills (auto-detect target)
    python scripts/install.py --target claude          # install to Claude
    python scripts/install.py --target gemini          # install to Gemini
    python scripts/install.py --skills CodeSage,UISmith  # install specific skills
    python scripts/install.py --force                  # overwrite existing installs
    python scripts/install.py --dry-run                # preview without writing
    python scripts/install.py --validate               # validate before installing
    python scripts/install.py --list-installed         # show installed skills
    python scripts/install.py --uninstall CodeSage     # remove specific skills
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SKILL_FILENAMES = ("skill.md", "SKILL.md")
META_FILE = ".skills-meta.json"

INSTALL_DIRS = {
    "claude": Path.home() / ".claude" / "commands",
    "gemini": Path.home() / ".gemini" / "commands",
}

POST_INSTALL_INSTRUCTIONS = {
    "claude": "Use skills by typing /skill-name in Claude Code",
    "gemini": "Skills are available in your Gemini context",
}

# ---------------------------------------------------------------------------
# Repo helpers
# ---------------------------------------------------------------------------

def repo_root() -> Path:
    """Return the root of this repository (parent of this script's directory)."""
    return Path(__file__).resolve().parent.parent


def find_all_skill_dirs(root: Path) -> dict[str, Path]:
    """
    Scan repo root for directories containing a skill file.
    Returns {skill_name: skill_file_path}.
    Skill name is derived from the directory name (lowercased, spaces→hyphens).
    """
    skills: dict[str, Path] = {}
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        # Skip hidden dirs and the scripts dir itself
        if d.name.startswith(".") or d.name == "scripts":
            continue
        for filename in SKILL_FILENAMES:
            candidate = d / filename
            if candidate.is_file():
                skill_name = d.name.lower().replace(" ", "-")
                skills[skill_name] = candidate
                break
    return skills


def git_hash(path: Path) -> str:
    """Return the git object hash for a file, or a content SHA256 fallback."""
    try:
        result = subprocess.run(
            ["git", "hash-object", str(path)],
            capture_output=True,
            text=True,
            cwd=str(path.parent),
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        pass  # git not available
    # Fallback: SHA256 of file content
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest[:16]}"


# ---------------------------------------------------------------------------
# Meta file helpers
# ---------------------------------------------------------------------------

def load_meta(install_dir: Path) -> dict:
    meta_path = install_dir / META_FILE
    if meta_path.is_file():
        try:
            return json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_meta(install_dir: Path, meta: dict) -> None:
    install_dir.mkdir(parents=True, exist_ok=True)
    meta_path = install_dir / META_FILE
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Validation helper (delegates to scripts/validate.py if available)
# ---------------------------------------------------------------------------

def validate_skill(skill_file: Path) -> tuple[bool, str]:
    """
    Run a lightweight inline validation on a single skill file.
    Returns (passed, message).
    """
    try:
        text = skill_file.read_text(encoding="utf-8")
    except OSError as exc:
        return False, f"Cannot read file: {exc}"

    lines = text.splitlines()
    if len(lines) < 10:
        return False, f"Too short ({len(lines)} lines)"

    # Check for frontmatter
    if not lines or lines[0].strip() != "---":
        return False, "Missing YAML frontmatter (file must start with ---)"

    # Extract frontmatter fields
    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return False, "Unclosed YAML frontmatter"

    fm_text = "\n".join(lines[1:end_idx])
    if "name:" not in fm_text:
        return False, "Frontmatter missing 'name' field"
    if "description:" not in fm_text:
        return False, "Frontmatter missing 'description' field"

    return True, "OK"


# ---------------------------------------------------------------------------
# Auto-detect target
# ---------------------------------------------------------------------------

def auto_detect_target() -> str | None:
    """Return 'claude' or 'gemini' based on which install dirs already exist."""
    for target, path in INSTALL_DIRS.items():
        if path.exists():
            return target
    # Fall back to claude as the primary target
    return "claude"


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------

def list_installed(install_dir: Path) -> None:
    meta = load_meta(install_dir)
    if not meta:
        print("No skills installed.")
        return

    print(f"Installed skills in {install_dir}:\n")
    header = f"{'Skill':<30} {'Version':<20} {'Installed At'}"
    print(header)
    print("-" * len(header))
    for name, info in sorted(meta.items()):
        version = info.get("version", "unknown")[:12]
        installed_at = info.get("installed_at", "unknown")
        print(f"{name:<30} {version:<20} {installed_at}")


def uninstall_skills(names: list[str], install_dir: Path, dry_run: bool) -> None:
    meta = load_meta(install_dir)
    removed, missing = 0, 0

    for name in names:
        dest = install_dir / f"{name}.md"
        if dest.exists():
            print(f"  {'[dry-run] ' if dry_run else ''}Removing {dest}")
            if not dry_run:
                dest.unlink()
            removed += 1
        else:
            print(f"  Skill not installed: {name}")
            missing += 1

        if name in meta and not dry_run:
            del meta[name]

    if not dry_run:
        save_meta(install_dir, meta)

    print(f"\nUninstall summary: {removed} removed, {missing} not found.")


def install_skills(
    skill_map: dict[str, Path],
    install_dir: Path,
    target: str,
    force: bool,
    dry_run: bool,
    do_validate: bool,
) -> None:
    install_dir.mkdir(parents=True, exist_ok=True)
    meta = load_meta(install_dir)

    installed_count = 0
    skipped_count = 0
    failed_count = 0

    for skill_name, skill_file in sorted(skill_map.items()):
        dest = install_dir / f"{skill_name}.md"

        # Validation gate
        if do_validate:
            passed, msg = validate_skill(skill_file)
            if not passed:
                print(f"  FAIL  {skill_name}: validation error — {msg}")
                failed_count += 1
                continue

        # Skip if already installed and not forcing
        if dest.exists() and not force:
            print(f"  SKIP  {skill_name} (already installed; use --force to overwrite)")
            skipped_count += 1
            continue

        action = "Would install" if dry_run else "Installing"
        print(f"  {action}  {skill_name}")
        print(f"         src : {skill_file}")
        print(f"         dest: {dest}")

        if not dry_run:
            shutil.copy2(str(skill_file), str(dest))
            meta[skill_name] = {
                "name": skill_name,
                "version": git_hash(skill_file),
                "installed_at": datetime.now(timezone.utc).isoformat(),
                "source_path": str(skill_file),
            }

        installed_count += 1

    if not dry_run:
        save_meta(install_dir, meta)

    prefix = "[dry-run] " if dry_run else ""
    print(
        f"\n{prefix}Summary: {installed_count} installed, "
        f"{skipped_count} skipped (already exists), "
        f"{failed_count} failed."
    )

    if not dry_run and installed_count > 0:
        instruction = POST_INSTALL_INSTRUCTIONS.get(target, "")
        print(f"\nHow to use your skills ({target}):")
        if target == "claude":
            print(f"  {instruction}")
            print(f"  Example: /codesage, /uismith, /bugHunter-pro")
        else:
            print(f"  {instruction}")
        print(f"\nInstall directory: {install_dir}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install Agent Skills to Claude or Gemini commands directories.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--target", "-t",
        choices=["claude", "gemini"],
        default=None,
        help="Target platform (default: auto-detect based on existing directories).",
    )
    parser.add_argument(
        "--skills", "-s",
        default=None,
        help="Comma-separated skill names to install (default: all).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing installed skills.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making any changes.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run validation on each skill before installing; skip invalid skills.",
    )
    parser.add_argument(
        "--list-installed",
        action="store_true",
        help="Show currently installed skills with version info.",
    )
    parser.add_argument(
        "--uninstall",
        metavar="NAMES",
        default=None,
        help="Comma-separated skill names to uninstall.",
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    # Resolve target platform
    target = args.target or auto_detect_target()
    install_dir = INSTALL_DIRS[target]

    print(f"Target : {target}")
    print(f"Install: {install_dir}")
    print()

    # --list-installed
    if args.list_installed:
        list_installed(install_dir)
        return 0

    # --uninstall
    if args.uninstall:
        names = [n.strip().lower().replace(" ", "-") for n in args.uninstall.split(",") if n.strip()]
        print(f"Uninstalling {len(names)} skill(s) from {install_dir}:\n")
        uninstall_skills(names, install_dir, dry_run=args.dry_run)
        return 0

    # Discover all skills in the repo
    root = repo_root()
    all_skills = find_all_skill_dirs(root)

    if not all_skills:
        print("ERROR: No skill files found in the repository.")
        return 1

    # Filter to requested skills if --skills was given
    if args.skills:
        requested = {
            n.strip().lower().replace(" ", "-")
            for n in args.skills.split(",")
            if n.strip()
        }
        unknown = requested - all_skills.keys()
        if unknown:
            print(f"WARNING: Unknown skill(s): {', '.join(sorted(unknown))}")
        skill_map = {k: v for k, v in all_skills.items() if k in requested}
        if not skill_map:
            print("ERROR: No matching skills found.")
            return 1
    else:
        skill_map = all_skills

    print(f"Skills to process: {len(skill_map)}")
    if args.dry_run:
        print("[DRY RUN — no files will be written]\n")
    print()

    install_skills(
        skill_map=skill_map,
        install_dir=install_dir,
        target=target,
        force=args.force,
        dry_run=args.dry_run,
        do_validate=args.validate,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
