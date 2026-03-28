#!/usr/bin/env node

const { execSync, spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const os = require("os");

// ── Resolve paths ──────────────────────────────────────────────────
const PKG_ROOT = path.resolve(__dirname, "..");
const SCRIPTS_DIR = path.join(PKG_ROOT, "scripts");
const HOME = os.homedir();

const TARGETS = {
  claude: path.join(HOME, ".claude", "commands"),
  gemini: path.join(HOME, ".gemini", "commands"),
  antigravity: path.join(HOME, ".gemini", "antigravity", "skills"),
};

// ── Helpers ────────────────────────────────────────────────────────
function hasPython() {
  for (const cmd of ["python3", "python"]) {
    try {
      execSync(`${cmd} --version`, { stdio: "ignore" });
      return cmd;
    } catch (_) {}
  }
  return null;
}

function runPythonScript(scriptName, args = []) {
  const py = hasPython();
  if (!py) {
    console.error("Error: Python 3 is required but not found in PATH.");
    console.error("Install Python 3: https://python.org/downloads/");
    process.exit(1);
  }
  const scriptPath = path.join(SCRIPTS_DIR, scriptName);
  if (!fs.existsSync(scriptPath)) {
    console.error(`Error: Script not found: ${scriptPath}`);
    process.exit(1);
  }
  const result = spawnSync(py, [scriptPath, ...args], {
    stdio: "inherit",
    cwd: PKG_ROOT,
  });
  process.exit(result.status || 0);
}

function findSkillFiles() {
  const skills = [];
  const entries = fs.readdirSync(PKG_ROOT, { withFileTypes: true });
  for (const entry of entries) {
    if (!entry.isDirectory() || entry.name.startsWith(".") || entry.name === "node_modules" || entry.name === "bin" || entry.name === "scripts") continue;
    const dir = path.join(PKG_ROOT, entry.name);
    for (const fname of ["skill.md", "SKILL.md"]) {
      const fpath = path.join(dir, fname);
      if (fs.existsSync(fpath)) {
        skills.push({ name: entry.name, file: fname, fullPath: fpath, dir: entry.name });
        break;
      }
    }
  }
  return skills;
}

function slugify(name) {
  return name.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "");
}

function copyDirSync(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDirSync(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

// ── Commands ───────────────────────────────────────────────────────

function cmdInstall(args) {
  const flags = parseFlags(args, { target: "t", skills: "s", force: null, "dry-run": null, validate: null });

  // Detect target
  let target = flags.target;
  if (!target) {
    if (fs.existsSync(TARGETS.claude)) target = "claude";
    else if (fs.existsSync(TARGETS.antigravity)) target = "antigravity";
    else if (fs.existsSync(TARGETS.gemini)) target = "gemini";
    else target = "claude"; // default
  }
  if (!TARGETS[target]) {
    console.error(`Unknown target: ${target}. Use "claude", "gemini", or "antigravity".`);
    process.exit(1);
  }

  const installDir = TARGETS[target];
  const dryRun = flags["dry-run"] || false;
  const force = flags.force || false;

  // Ensure install directory
  if (!dryRun) {
    fs.mkdirSync(installDir, { recursive: true });
  }

  // Find skills
  let skills = findSkillFiles();
  if (flags.skills) {
    const wanted = new Set(flags.skills.split(",").map(s => s.trim().toLowerCase()));
    skills = skills.filter(s => wanted.has(s.name.toLowerCase()) || wanted.has(slugify(s.name)));
  }

  console.log(`Target : ${target}`);
  console.log(`Install: ${installDir}`);
  console.log(`Skills : ${skills.length}`);
  if (dryRun) console.log("[DRY RUN — no files will be written]\n");
  else console.log();

  let installed = 0, skipped = 0, failed = 0;
  const meta = loadMeta(installDir);

  for (const skill of skills) {
    const slug = slugify(skill.name);
    const dest = path.join(installDir, `${slug}.md`);

    const existsAlready = target === "antigravity"
      ? fs.existsSync(path.join(installDir, slug, "SKILL.md"))
      : fs.existsSync(dest);
    if (existsAlready && !force) {
      if (!dryRun) console.log(`  SKIP  ${slug} (already exists, use --force to overwrite)`);
      skipped++;
      continue;
    }

    if (flags.validate) {
      const content = fs.readFileSync(skill.fullPath, "utf8");
      const issues = validateSkill(content);
      if (issues.length > 0) {
        console.log(`  FAIL  ${slug} — validation errors:`);
        issues.forEach(i => console.log(`         - ${i}`));
        failed++;
        continue;
      }
    }

    if (target === "antigravity") {
      // Antigravity uses directory-based skills: each skill is a directory with SKILL.md
      const skillDir = path.join(installDir, slug);
      const destFile = path.join(skillDir, "SKILL.md");

      if (dryRun) {
        console.log(`  Would install ${slug}`);
        console.log(`    src : ${skill.fullPath}`);
        console.log(`    dest: ${destFile}`);
      } else {
        try {
          fs.mkdirSync(skillDir, { recursive: true });
          fs.copyFileSync(skill.fullPath, destFile);
          // Copy optional assets (scripts/, references/) if they exist in source
          const srcDir = path.dirname(skill.fullPath);
          for (const subdir of ["scripts", "references", "assets"]) {
            const srcSub = path.join(srcDir, subdir);
            if (fs.existsSync(srcSub) && fs.statSync(srcSub).isDirectory()) {
              copyDirSync(srcSub, path.join(skillDir, subdir));
            }
          }
          meta[slug] = {
            name: slug,
            source: skill.fullPath,
            installed_at: new Date().toISOString(),
            directory: skill.dir,
          };
          installed++;
          console.log(`  OK    ${slug}`);
        } catch (err) {
          console.log(`  FAIL  ${slug} — ${err.message}`);
          failed++;
        }
      }
    } else {
      if (dryRun) {
        console.log(`  Would install ${slug}`);
        console.log(`    src : ${skill.fullPath}`);
        console.log(`    dest: ${dest}`);
      } else {
        try {
          fs.copyFileSync(skill.fullPath, dest);
          meta[slug] = {
            name: slug,
            source: skill.fullPath,
            installed_at: new Date().toISOString(),
            directory: skill.dir,
          };
          installed++;
          console.log(`  OK    ${slug}`);
        } catch (err) {
          console.log(`  FAIL  ${slug} — ${err.message}`);
          failed++;
        }
      }
    }
  }

  if (!dryRun) {
    saveMeta(installDir, meta);
  }

  console.log(`\n${installed} installed, ${skipped} skipped, ${failed} failed.`);

  if (!dryRun && installed > 0) {
    console.log(`\n  How to use:`);
    if (target === "claude") {
      console.log(`  In Claude Code, type /<skill-name> to invoke a skill.`);
      console.log(`  Examples: /codesage, /testcrafter, /dockmaster, /python-master`);
    } else if (target === "antigravity") {
      console.log(`  Skills are now available in Google Antigravity.`);
      console.log(`  The agent will automatically match skills to your tasks via semantic triggering.`);
      console.log(`  Installed to: ${installDir}`);
    } else {
      console.log(`  Skills are now available in your Gemini context.`);
    }
  }
}

function cmdUninstall(args) {
  const flags = parseFlags(args, { target: "t" });
  const target = flags.target || "claude";
  const installDir = TARGETS[target];
  const names = flags._.filter(n => n !== "uninstall");

  if (names.length === 0) {
    console.error("Usage: agent-skills uninstall <skill-name> [<skill-name>...] [-t claude|gemini|antigravity]");
    process.exit(1);
  }

  const meta = loadMeta(installDir);
  let removed = 0;

  for (const name of names) {
    const slug = slugify(name);
    const dest = path.join(installDir, `${slug}.md`);
    if (fs.existsSync(dest)) {
      fs.unlinkSync(dest);
      delete meta[slug];
      console.log(`  Removed ${slug}`);
      removed++;
    } else {
      console.log(`  Not found: ${slug}`);
    }
  }

  saveMeta(installDir, meta);
  console.log(`\n${removed} skill(s) removed.`);
}

function cmdList(args) {
  const flags = parseFlags(args, { target: "t" });
  const target = flags.target || "claude";
  const installDir = TARGETS[target];

  if (!fs.existsSync(installDir)) {
    console.log(`No skills installed for ${target} (${installDir} does not exist).`);
    return;
  }

  const meta = loadMeta(installDir);
  const entries = Object.values(meta);

  if (entries.length === 0) {
    console.log(`No skills installed for ${target}.`);
    return;
  }

  console.log(`Installed skills (${target}): ${entries.length}\n`);
  console.log("  Name                          Installed At");
  console.log("  " + "-".repeat(60));
  for (const e of entries.sort((a, b) => a.name.localeCompare(b.name))) {
    const date = e.installed_at ? e.installed_at.slice(0, 19).replace("T", " ") : "unknown";
    console.log(`  ${e.name.padEnd(30)} ${date}`);
  }
}

function cmdDoctor(args) {
  runPythonScript("doctor.py", args);
}

function cmdRoute(args) {
  runPythonScript("route.py", args);
}

function cmdValidate(args) {
  runPythonScript("validate.py", args);
}

function cmdScore(args) {
  runPythonScript("score.py", args);
}

function cmdTest(args) {
  runPythonScript("test_skill.py", args);
}

function cmdBuildIndex(args) {
  runPythonScript("build_index.py", args);
}

function cmdHelp() {
  console.log(`
agent-skills — AI-powered developer skills for Claude, Gemini, and Antigravity

Usage:
  agent-skills <command> [options]

Commands:
  install              Install skills to Claude, Gemini, or Antigravity
    -t, --target       Target: "claude", "gemini", or "antigravity" (default: auto-detect)
    -s, --skills       Comma-separated skill names (default: all)
    --force            Overwrite existing skills
    --dry-run          Preview without writing files
    --validate         Validate skills before installing

  uninstall <names>    Remove installed skills
    -t, --target       Target: "claude", "gemini", or "antigravity"

  list                 List installed skills
    -t, --target       Target: "claude", "gemini", or "antigravity"

  route "<prompt>"     Find the best skill for a task
    -n, --top-n        Number of results (default: 3)
    --json             Output as JSON
    --interactive      Interactive prompt mode

  doctor               Check health of installed skills
    -t, --target       Target: "claude", "gemini", or "antigravity" (default: all)

  validate             Lint all skill files
    --fix              Auto-fix known issues

  score                Score all skills on quality metrics
    --json             Output as JSON

  test                 Run adversarial tests on all skills

  build-index          Regenerate skills.json and skills-routing.json

Examples:
  npx agent-skills install                      # Install all to Claude
  npx agent-skills install -t gemini -s CodeSage,TestCrafter
  npx agent-skills install -t antigravity       # Install all to Google Antigravity
  npx agent-skills route "review my Python code"
  npx agent-skills doctor
  npx agent-skills list
  npx agent-skills score --json > report.json
`);
}

// ── Utilities ──────────────────────────────────────────────────────

function parseFlags(args, aliases = {}) {
  const result = { _: [] };
  let i = 0;
  while (i < args.length) {
    const arg = args[i];
    if (arg.startsWith("--")) {
      const key = arg.slice(2);
      if (i + 1 < args.length && !args[i + 1].startsWith("-")) {
        result[key] = args[++i];
      } else {
        result[key] = true;
      }
    } else if (arg.startsWith("-") && arg.length === 2) {
      const short = arg.slice(1);
      const long = Object.entries(aliases).find(([, v]) => v === short)?.[0];
      const key = long || short;
      if (i + 1 < args.length && !args[i + 1].startsWith("-")) {
        result[key] = args[++i];
      } else {
        result[key] = true;
      }
    } else {
      result._.push(arg);
    }
    i++;
  }
  return result;
}

function validateSkill(content) {
  const issues = [];
  if (!content.startsWith("---")) issues.push("Missing frontmatter (---)");
  if (!content.match(/^#{1}\s/m)) issues.push("No H1 heading found");
  if (!content.match(/^#{2}\s/m)) issues.push("No H2 section found");
  if (!content.includes("```")) issues.push("No code examples found");
  if (content.length < 500) issues.push("Content too short (< 500 chars)");
  return issues;
}

function loadMeta(installDir) {
  const metaPath = path.join(installDir, ".skills-meta.json");
  if (fs.existsSync(metaPath)) {
    try { return JSON.parse(fs.readFileSync(metaPath, "utf8")); } catch (_) {}
  }
  return {};
}

function saveMeta(installDir, meta) {
  const metaPath = path.join(installDir, ".skills-meta.json");
  fs.writeFileSync(metaPath, JSON.stringify(meta, null, 2) + "\n");
}

// ── Main ───────────────────────────────────────────────────────────

const [, , command, ...args] = process.argv;

switch (command) {
  case "install":     cmdInstall(args); break;
  case "uninstall":   cmdUninstall(args); break;
  case "list":        cmdList(args); break;
  case "route":       cmdRoute(args); break;
  case "doctor":      cmdDoctor(args); break;
  case "validate":    cmdValidate(args); break;
  case "score":       cmdScore(args); break;
  case "test":        cmdTest(args); break;
  case "build-index": cmdBuildIndex(args); break;
  case "help":
  case "--help":
  case "-h":
  case undefined:     cmdHelp(); break;
  default:
    console.error(`Unknown command: ${command}\nRun "agent-skills help" for usage.`);
    process.exit(1);
}
