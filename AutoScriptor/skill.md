---
name: autoscriptor
description: Generates production-grade automation scripts in Bash, Python, and PowerShell with idempotency, dry-run mode, error handling, and ShellCheck compliance. Use when a user needs a cron job, deployment script, file processing utility, system automation, or any CLI tool for repetitive developer or ops tasks.
---

# AutoScriptor

## Domain Scope

Shell scripts (Bash/POSIX sh), Python CLI tools (argparse/click/typer), PowerShell automation, cron/systemd timer scheduling, and CI/CD pipeline scripts. Focus on correctness, idempotency, and operability.

---

## Workflow

### 1. Gather Script Requirements
Before writing, confirm:
- **Target OS/shell**: Bash on Linux/macOS, POSIX sh for portability, PowerShell 7+ for Windows/cross-platform.
- **Idempotency requirement**: Can the script be run twice safely without side effects?
- **Dry-run requirement**: Should `--dry-run` print what would happen without executing?
- **Input sources**: args, env vars, config file, stdin?
- **Error handling**: fail-fast, retry, or continue-on-error?

### 2. Bash Script Standards

**Mandatory header**:
```bash
#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'
```
- `set -e`: exit on error; `set -u`: unset vars are errors; `set -o pipefail`: pipe fails if any stage fails.

**`set -e` pitfall**: Commands that legitimately return non-zero (e.g., `grep` returning 1 when no match, `diff` returning 1 when files differ) will abort the script. Guard them:
```bash
grep "pattern" file || true          # ignore non-zero exit
if diff file1 file2 > /dev/null; then echo "same"; fi   # use if guard
```

**Dry-run pattern**:
```bash
DRY_RUN=false
run() { [[ "$DRY_RUN" == true ]] && echo "[DRY-RUN] $*" || "$@"; }
run rm -rf "$TMP_DIR"
```

**Idempotency patterns**:
- `[[ -d "$DIR" ]] || mkdir -p "$DIR"`
- `command -v jq &>/dev/null || apt-get install -y jq`
- Use migration tables for DB scripts to track applied steps.

### 3. ShellCheck Compliance
- Run `shellcheck script.sh` before finalizing. Zero warnings is the target.
- Quote all variables: `"$VAR"`. Use `[[ ]]` over `[ ]`. Use `$()` over backticks.

### 4. Python CLI Scripts

```python
#!/usr/bin/env python3
import click
from pathlib import Path

@click.command()
@click.option("--input", "-i", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--dry-run", is_flag=True, default=False)
def main(input: Path, dry_run: bool) -> None:
    """Process INPUT file."""
    # Use sys.exit(1) on failure; never silently catch Exception
```

**Large file streaming** — avoid loading entire files into memory:
```python
import csv, itertools

# Stream CSV rows
with open("big.csv") as f:
    reader = csv.reader(f)
    for row in itertools.islice(reader, 1000):  # process first 1000
        process(row)

# pandas chunked reading
for chunk in pd.read_csv("big.csv", chunksize=10_000):
    process(chunk)
```

- Use `pathlib.Path` over `os.path`. Atomic writes: write to temp file, then `Path.rename()`.

### 5. Docker Volume UID/GID Mapping
When mounting host volumes into containers, file permission mismatches occur if the container user UID differs from the host file owner:
```dockerfile
# Match container user UID to host developer UID
ARG UID=1000
RUN adduser -u $UID -S app
USER app
```
Build with: `docker build --build-arg UID=$(id -u) .`
For rootless compose: set `user: "${UID}:${GID}"` in `docker-compose.yml` and export `UID`/`GID` in the shell. Alternatively, use named volumes (Docker manages ownership) rather than bind mounts to avoid UID conflicts in CI.

### 6. Scheduling

**Crontab**: `30 2 * * * /opt/scripts/backup.sh >> /var/log/backup.log 2>&1` — always use full paths and redirect stderr.

**systemd timer** (preferred):
```ini
[Timer]
OnCalendar=*-*-* 02:30:00 UTC
Persistent=true
```
Enable: `systemctl enable --now backup.timer`.

### 7. PowerShell Standards
```powershell
#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
param([Parameter(Mandatory)][string]$TargetPath, [switch]$DryRun)
try { Write-Host "Starting (DryRun=$DryRun)" } catch { Write-Host $_.Exception.Message; exit 1 }
```

---

## Output Artifacts

- Complete script with shebang, set flags, logging, arg parsing, dry-run, and trap/cleanup.
- ShellCheck result (0 warnings) or accepted deviations with justification.
- Cron/systemd unit file if scheduling is required.
- Example invocations (normal, dry-run, verbose).

---

## Edge Cases

1. **Script fails partway through**: Use `flock` for locking and `trap cleanup EXIT` for rollback. Write completed steps to a state file so re-runs skip them.

2. **File paths with spaces/special characters**: Always quote variables. Use `find -print0 | xargs -0`. In Python, always use `subprocess.run(["cmd", arg])` list form — never f-string shell injection.

3. **Unexpected environments (CI, Docker, restricted PATH)**: Do not rely on `~/.bashrc`. Set `PATH` explicitly. Check dependencies at startup: `for cmd in jq aws; do command -v "$cmd" >/dev/null || die "$cmd not found"; done`.
