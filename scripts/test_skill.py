#!/usr/bin/env python3
"""
Adversarial test harness for Agent-Skills skill files.

Usage (from repo root):
    python scripts/test_skill.py

Exit code 0 if overall pass rate >= 80%, exit code 1 otherwise.
"""

import sys
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Repository root is one level above this script's directory
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Category definitions  {skill_folder_name: category_key}
# ---------------------------------------------------------------------------
CATEGORIES = {
    "security": ["AuthCraft", "SecureScan", "SecretSniffer", "InputShield"],
    "testing":  ["TestCrafter", "FlowTester", "CoverageMax", "EdgeGuard", "MockSmith"],
    "devops":   ["DockMaster", "KubeCrafter", "PipelinePro", "EnvWizard"],
    "frontend": ["UISmith", "FlexiLayout", "RenderBoost", "SEOMancer"],
    "database": ["DataWeaver", "QueryPulse", "DataPolish"],
}

# All skills that should receive category-specific tests (flat set for lookups)
ALL_CATEGORISED_SKILLS: set[str] = {s for skills in CATEGORIES.values() for s in skills}


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def text_contains_any(text: str, *patterns: str) -> bool:
    """Return True if any pattern (regex) matches the lowercased text."""
    lower = text.lower()
    for pattern in patterns:
        if re.search(pattern, lower):
            return True
    return False


def count_named_tools(text: str) -> int:
    """
    Heuristic: count capitalised proper-noun tool names (CamelCase or
    ALL-CAPS abbreviations) or well-known lowercase tool names.
    We look for a curated list of tool/framework/library names.
    """
    known_tools = [
        # Languages / runtimes
        r"\bpython\b", r"\bnode\.?js\b", r"\bjava\b", r"\brust\b", r"\bgo\b",
        r"\bruby\b", r"\bphp\b", r"\bkotlin\b", r"\bswift\b", r"\belixir\b",
        r"\btypescript\b", r"\bjavascript\b",
        # Test frameworks
        r"\bjest\b", r"\bvitest\b", r"\bpytest\b", r"\bjunit\b", r"\bmocha\b",
        r"\bcypress\b", r"\bplaywright\b", r"\bselenium\b", r"\btestcontainers\b",
        r"\bspec\b",
        # Security tools
        r"\bowasp\b", r"\bsnyk\b", r"\bbankrup\b", r"\btrivy\b", r"\bsemgrep\b",
        r"\bburp\b", r"\bnessus\b", r"\bnmap\b", r"\bhashicorp\b", r"\bvault\b",
        r"\bzap\b",
        # DevOps / infra
        r"\bdocker\b", r"\bkubernetes\b", r"\bhelm\b", r"\bterraform\b",
        r"\bansible\b", r"\bargocd\b", r"\bgithub actions\b", r"\bgitlab ci\b",
        r"\bcircleci\b", r"\bjenkins\b", r"\bprometheus\b", r"\bgrafana\b",
        r"\bdatadog\b", r"\bopen ?telemetry\b",
        # Cloud providers / platforms
        r"\baws\b", r"\bgcp\b", r"\bazure\b", r"\bheroku\b", r"\bvercel\b",
        r"\bcloudflare\b", r"\bflyio\b", r"\brailway\b",
        # Databases
        r"\bpostgresql\b", r"\bpostgres\b", r"\bmysql\b", r"\bsqlite\b",
        r"\bmongodb\b", r"\bredis\b", r"\belasticsearch\b", r"\bcockroachdb\b",
        r"\bsupabase\b", r"\bneon\b",
        # Auth / crypto libs
        r"\bargon2\b", r"\bbcrypt\b", r"\bscrypt\b", r"\bjwt\b", r"\bopenssl\b",
        # Frontend frameworks
        r"\breact\b", r"\bvue\b", r"\bangular\b", r"\bsvelte\b", r"\bnext\.?js\b",
        r"\btailwind\b", r"\bwebpack\b", r"\bvite\b",
        # Linters / formatters
        r"\beslint\b", r"\bprettier\b", r"\bruff\b", r"\bblack\b", r"\bmypy\b",
        # Other common tools
        r"\bgit\b", r"\bnginx\b", r"\bapache\b", r"\bkafka\b", r"\brabbitmq\b",
        r"\bcelery\b", r"\bsqlalchemy\b", r"\bprisma\b", r"\bdrizzle\b",
        r"\bstorybook\b", r"\bfigma\b",
    ]
    lower = text.lower()
    return sum(1 for pattern in known_tools if re.search(pattern, lower))


def count_edge_cases(text: str) -> int:
    """Count mentions of edge-case keywords."""
    patterns = [
        r"\bedge case\b", r"\bcorner case\b", r"\bboundary\b", r"\bnull\b",
        r"\bempty\b", r"\bzero[-\s]?length\b", r"\boverflow\b", r"\bunderflow\b",
        r"\binvalid input\b", r"\bmalformed\b", r"\bconcurren", r"\brace condition\b",
        r"\btimeout\b", r"\bretry\b", r"\bfallback\b", r"\bgraceful degrad\b",
        r"\bmax\b.{0,20}\blimit\b", r"\bmin\b.{0,20}\blimit\b",
        r"\boff-by-one\b", r"\btruncati\b", r"\bspecial character\b",
        r"\bunicode\b", r"\butf-?8\b", r"\blarge file\b", r"\bempty list\b",
        r"\bnegative\b", r"\bwhen .{1,40} is (empty|null|missing|invalid|zero)",
    ]
    lower = text.lower()
    return sum(1 for p in patterns if re.search(p, lower))


def has_code_example(text: str) -> bool:
    """Return True if the file contains a fenced code block."""
    return bool(re.search(r"```", text))


def has_numbered_workflow(text: str) -> bool:
    """Return True if there are at least 3 numbered steps (e.g., '1. ' '2. ' '3. ')."""
    steps = re.findall(r"^\s*\d+\.", text, re.MULTILINE)
    return len(steps) >= 3


# ---------------------------------------------------------------------------
# Category-specific test suites
# ---------------------------------------------------------------------------

def tests_security(text: str) -> list[tuple[str, bool, str]]:
    results = []

    # OWASP mention
    ok = text_contains_any(text, r"\bowasp\b")
    results.append(("mentions OWASP", ok, "" if ok else "No mention of OWASP"))

    # CVE or CWE number
    ok = bool(re.search(r"\b(CVE|CWE)-\d+", text))
    results.append(("mentions CVE/CWE number", ok,
                    "" if ok else "No specific CVE/CWE reference found"))

    # At least 2 named security tools
    security_tools = [
        r"\bsnyk\b", r"\btrivy\b", r"\bsemgrep\b", r"\bbanndit\b", r"\bsafety\b",
        r"\bburp\b", r"\bnessus\b", r"\bnmap\b", r"\bzap\b", r"\bsonarqube\b",
        r"\bvault\b", r"\bargon2\b", r"\bbcrypt\b", r"\bscrypt\b",
        r"\bopenssl\b", r"\blibsodium\b", r"\bcryptojs\b",
    ]
    lower = text.lower()
    found = [t for t in security_tools if re.search(t, lower)]
    ok = len(found) >= 2
    results.append(("names >= 2 security tools", ok,
                    "" if ok else f"Only found: {found or ['none']}"))

    return results


def tests_testing(text: str) -> list[tuple[str, bool, str]]:
    results = []

    # Specific testing framework
    frameworks = [r"\bjest\b", r"\bvitest\b", r"\bpytest\b", r"\bjunit\b",
                  r"\bmocha\b", r"\bcypress\b", r"\bplaywright\b", r"\bselenium\b",
                  r"\brspec\b", r"\bgocheck\b", r"\bspec\b"]
    ok = text_contains_any(text, *frameworks)
    results.append(("mentions a testing framework", ok,
                    "" if ok else "No named testing framework found"))

    # AAA pattern or equivalent (BDD Given/When/Then)
    ok = text_contains_any(text,
                           r"\barrange\b.{0,200}\bact\b.{0,200}\bassert\b",
                           r"\bAAA\b",
                           r"\bgiven\b.{0,200}\bwhen\b.{0,200}\bthen\b",
                           r"arrange.*act.*assert",
                           r"# arrange", r"# act", r"# assert")
    results.append(("mentions AAA / GWT pattern", ok,
                    "" if ok else "No AAA (Arrange-Act-Assert) or Given/When/Then pattern found"))

    # CI integration
    ok = text_contains_any(text,
                           r"\bci\b", r"\bcontinuous integration\b",
                           r"\bgithub actions\b", r"\bgitlab ci\b",
                           r"\bcircleci\b", r"\bjenkins\b", r"\bpipeline\b")
    results.append(("mentions CI integration", ok,
                    "" if ok else "No CI/pipeline integration mentioned"))

    return results


def tests_devops(text: str) -> list[tuple[str, bool, str]]:
    results = []

    # Cloud provider or platform
    ok = text_contains_any(text,
                           r"\baws\b", r"\bgcp\b", r"\bazure\b", r"\bheroku\b",
                           r"\bvercel\b", r"\bcloudflare\b", r"\bflyio\b",
                           r"\brailway\b", r"\bdigitalocean\b", r"\beks\b",
                           r"\bgke\b", r"\baks\b")
    results.append(("mentions cloud provider/platform", ok,
                    "" if ok else "No cloud provider or platform mentioned"))

    # Security hardening
    ok = text_contains_any(text,
                           r"\bharden\b", r"\bsecurity\b", r"\bprincipl.{0,10}least privilege\b",
                           r"\brbac\b", r"\bnetwork polic\b", r"\bsecret\b",
                           r"\bencrypt\b", r"\btls\b", r"\bssl\b", r"\bvault\b",
                           r"\bscan\b")
    results.append(("mentions security hardening", ok,
                    "" if ok else "No security hardening concepts found"))

    # Rollback / recovery
    ok = text_contains_any(text,
                           r"\brollback\b", r"\brecovery\b", r"\bdr\b",
                           r"\bdisaster\b", r"\bundeploy\b", r"\bcanary\b",
                           r"\bblue.?green\b", r"\bfailover\b", r"\bbackup\b")
    results.append(("mentions rollback/recovery", ok,
                    "" if ok else "No rollback or recovery strategy mentioned"))

    return results


def tests_frontend(text: str) -> list[tuple[str, bool, str]]:
    results = []

    # WCAG / accessibility
    ok = text_contains_any(text,
                           r"\bwcag\b", r"\baccessibility\b", r"\ba11y\b",
                           r"\baria\b", r"\bscreen reader\b", r"\balt text\b",
                           r"\bkeyboard nav\b")
    results.append(("mentions WCAG/accessibility", ok,
                    "" if ok else "No accessibility or WCAG reference found"))

    # Specific browser or tooling
    ok = text_contains_any(text,
                           r"\bchrome\b", r"\bfirefox\b", r"\bsafari\b", r"\bedge\b",
                           r"\blighthouse\b", r"\bwebpack\b", r"\bvite\b",
                           r"\bdevtools\b", r"\bpuppeteer\b", r"\bplaywright\b")
    results.append(("mentions specific browser or tool", ok,
                    "" if ok else "No specific browser or front-end tooling mentioned"))

    # Performance metrics
    ok = text_contains_any(text,
                           r"\bcore web vitals\b", r"\blcp\b", r"\bfid\b",
                           r"\bcls\b", r"\bttfb\b", r"\bfcp\b",
                           r"\bperformance metric\b", r"\bpagespeed\b",
                           r"\btime to (first|interactive)\b", r"\bperformance\b")
    results.append(("mentions performance metrics", ok,
                    "" if ok else "No performance metrics mentioned"))

    return results


def tests_database(text: str) -> list[tuple[str, bool, str]]:
    results = []

    # EXPLAIN or query plans
    ok = text_contains_any(text,
                           r"\bexplain\b", r"\bquery plan\b", r"\bexecution plan\b",
                           r"\banalyze\b", r"\bslow query\b", r"\bindex scan\b",
                           r"\bseq scan\b")
    results.append(("mentions EXPLAIN/query plans", ok,
                    "" if ok else "No mention of EXPLAIN or query plan analysis"))

    # Migrations
    ok = text_contains_any(text,
                           r"\bmigrat\b", r"\balembic\b", r"\bflyway\b",
                           r"\bliquibase\b", r"\bschema change\b")
    results.append(("mentions migrations", ok,
                    "" if ok else "No mention of database migrations"))

    # Specific DB engine
    ok = text_contains_any(text,
                           r"\bpostgresql\b", r"\bpostgres\b", r"\bmysql\b",
                           r"\bmariadb\b", r"\bsqlite\b", r"\bmongodb\b",
                           r"\bcassandra\b", r"\bredis\b", r"\bdynamodb\b",
                           r"\bcockroachdb\b", r"\bspanner\b")
    results.append(("mentions specific DB engine", ok,
                    "" if ok else "No specific database engine mentioned"))

    return results


CATEGORY_TEST_FNS = {
    "security": tests_security,
    "testing":  tests_testing,
    "devops":   tests_devops,
    "frontend": tests_frontend,
    "database": tests_database,
}


# ---------------------------------------------------------------------------
# General tests (apply to every skill)
# ---------------------------------------------------------------------------

def general_tests(text: str) -> list[tuple[str, bool, str]]:
    results = []

    edge_count = count_edge_cases(text)
    ok = edge_count >= 3
    results.append(("has >= 3 edge cases", ok,
                    "" if ok else f"Only {edge_count} edge-case keyword(s) detected"))

    ok = has_code_example(text)
    results.append(("has >= 1 code example", ok,
                    "" if ok else "No fenced code block (```) found"))

    ok = has_numbered_workflow(text)
    results.append(("has structured numbered workflow", ok,
                    "" if ok else "Fewer than 3 numbered list items found"))

    tool_count = count_named_tools(text)
    ok = tool_count >= 5
    results.append(("names >= 5 specific tools", ok,
                    "" if ok else f"Only {tool_count} tool name(s) detected"))

    return results


# ---------------------------------------------------------------------------
# Skill discovery
# ---------------------------------------------------------------------------

def find_skill_file(skill_name: str) -> Path | None:
    """
    Search for skill.md or SKILL.md under a directory whose name matches
    the skill name (case-insensitive).
    """
    for directory in REPO_ROOT.iterdir():
        if not directory.is_dir():
            continue
        if directory.name.lower().replace(" ", "") == skill_name.lower().replace(" ", ""):
            for fname in ("skill.md", "SKILL.md"):
                candidate = directory / fname
                if candidate.exists():
                    return candidate
    return None


def get_category_for_skill(skill_name: str) -> str | None:
    for cat, skills in CATEGORIES.items():
        if skill_name in skills:
            return cat
    return None


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_tests() -> int:
    """Run all tests and print a report. Return exit code."""

    # Collect every skill to test (union of categorised + all skill dirs)
    all_skill_dirs: list[str] = []
    for directory in sorted(REPO_ROOT.iterdir()):
        if not directory.is_dir():
            continue
        if directory.name.startswith("."):
            continue
        if directory.name in ("scripts",):
            continue
        for fname in ("skill.md", "SKILL.md"):
            if (directory / fname).exists():
                all_skill_dirs.append(directory.name)
                break

    # Results storage: {category: [(skill, test_name, passed, detail), ...]}
    category_results: dict[str, list[tuple[str, str, bool, str]]] = {
        "security": [], "testing": [], "devops": [],
        "frontend": [], "database": [], "general": [],
    }

    total_tests = 0
    total_passed = 0

    skill_summaries: list[tuple[str, int, int]] = []  # (name, passed, total)

    print("=" * 72)
    print("ADVERSARIAL SKILL TEST HARNESS")
    print("=" * 72)

    for skill_name in all_skill_dirs:
        skill_file = find_skill_file(skill_name)
        if skill_file is None:
            continue

        text = skill_file.read_text(encoding="utf-8", errors="replace")
        category = get_category_for_skill(skill_name)

        print(f"\n{'-' * 72}")
        print(f"SKILL: {skill_name}")
        if category:
            print(f"Category: {category}")
        print(f"File: {skill_file.relative_to(REPO_ROOT)}")
        print()

        skill_passed = 0
        skill_total = 0

        # --- Category-specific tests ---
        if category and category in CATEGORY_TEST_FNS:
            cat_tests = CATEGORY_TEST_FNS[category](text)
            for test_name, passed, detail in cat_tests:
                status = "PASS" if passed else "FAIL"
                missing = f"  >> Missing: {detail}" if not passed else ""
                print(f"  [{status}] [{category.upper()}] {test_name}{missing}")
                category_results[category].append((skill_name, test_name, passed, detail))
                skill_total += 1
                skill_passed += passed

        # --- General tests ---
        gen_tests = general_tests(text)
        for test_name, passed, detail in gen_tests:
            status = "PASS" if passed else "FAIL"
            missing = f"  >> Missing: {detail}" if not passed else ""
            print(f"  [{status}] [GENERAL] {test_name}{missing}")
            category_results["general"].append((skill_name, test_name, passed, detail))
            skill_total += 1
            skill_passed += passed

        skill_summaries.append((skill_name, skill_passed, skill_total))
        total_tests += skill_total
        total_passed += skill_passed

    # ---------------------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------------------
    total_failed = total_tests - total_passed
    pass_rate = (total_passed / total_tests * 100) if total_tests else 0.0

    print()
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"  Total tests : {total_tests}")
    print(f"  Passed      : {total_passed}")
    print(f"  Failed      : {total_failed}")
    print(f"  Pass rate   : {pass_rate:.1f}%")
    print()

    # Category breakdown
    print("CATEGORY BREAKDOWN")
    print("-" * 72)
    for cat in ("security", "testing", "devops", "frontend", "database", "general"):
        entries = category_results[cat]
        if not entries:
            continue
        cat_total = len(entries)
        cat_passed = sum(1 for _, _, p, _ in entries if p)
        cat_rate = cat_passed / cat_total * 100 if cat_total else 0.0
        print(f"  {cat.upper():<12}  {cat_passed:>3}/{cat_total:<3}  ({cat_rate:.0f}%)")

    print()

    # Per-skill table (sorted by pass rate ascending so worst offenders surface first)
    print("PER-SKILL RESULTS (worst first)")
    print("-" * 72)
    skill_summaries.sort(key=lambda x: x[1] / x[2] if x[2] else 0)
    for name, passed, total in skill_summaries:
        rate = passed / total * 100 if total else 0.0
        bar = "#" * int(rate / 10) + "." * (10 - int(rate / 10))
        print(f"  {name:<25}  {passed:>2}/{total:<2}  {bar}  {rate:.0f}%")

    print()
    threshold = 80.0
    if pass_rate >= threshold:
        print(f"RESULT: PASS  (pass rate {pass_rate:.1f}% >= {threshold:.0f}%)")
        return 0
    else:
        print(f"RESULT: FAIL  (pass rate {pass_rate:.1f}% < {threshold:.0f}%)")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
