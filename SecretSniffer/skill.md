---
name: secretsniffer
description: Audits codebases and git history for hardcoded credentials, API keys, and sensitive data exposures. Use when asked to scan for secrets, check for leaked credentials, or set up pre-commit secret detection.
---

# SecretSniffer

## Overview

Scans source code and git history for hardcoded secrets using industry-standard tools (TruffleHog, Gitleaks, detect-secrets). Classifies findings by severity, maps to secret type, and produces SARIF-compatible output suitable for GitHub Advanced Security or CI gatekeeping.

## Workflow

### 1. Scope & Tool Selection

- Determine scan target: working tree only, staged files (pre-commit), or full git history.
- Select tool based on scope:
  - **TruffleHog v3** (`trufflehog git file://. --json`): deep entropy + regex, best for git history.
  - **Gitleaks** (`gitleaks detect --source . --report-format sarif --report-path findings.sarif`): fast, SARIF output, good for CI.
  - **detect-secrets** (`detect-secrets scan > .secrets.baseline`): baseline-based, low false-positive rate for pre-commit hooks.
- For pre-commit integration, install via `pre-commit` framework using `gitleaks` or `detect-secrets` hooks.

### 2. Pattern Coverage

Ensure the scan config covers these high-priority secret types:

| Secret Type | Regex / Entropy Signal |
|-------------|------------------------|
| AWS Access Key | `AKIA[0-9A-Z]{16}` |
| AWS Secret Key | 40-char base62, high entropy adjacent to "aws_secret" |
| JWT | `eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+` |
| PEM private key | `-----BEGIN (RSA\|EC\|OPENSSH) PRIVATE KEY-----` |
| GCP Service Account | `"type": "service_account"` in JSON |
| GitHub PAT | `gh[pousr]_[A-Za-z0-9]{36,}` |
| Generic high-entropy string | Shannon entropy > 4.5 over 20+ char alphanumeric strings |
| DB connection string | `(postgres\|mysql\|mongodb)://[^@]+:[^@]+@` |

For custom patterns, add to `.gitleaks.toml` under `[[rules]]` or extend the `detect-secrets` plugin list.

### 3. Severity Classification

Assign severity using this rubric:

- **CRITICAL**: Private keys (PEM/PKCS8), cloud provider master credentials (AWS root, GCP service accounts with `roles/owner`), database passwords in production configs.
- **HIGH**: Active API keys for third-party services (Stripe, Twilio, SendGrid), OAuth client secrets, JWT signing secrets.
- **MEDIUM**: Tokens that may be expired or test-only, internal service credentials.
- **LOW**: Patterns matching secret formats but confirmed test/placeholder values (e.g., `test_`, `dummy_`, `example_`).

### 4. Git History Deep Scan

When scanning history:
```bash
trufflehog git file://. --since-commit HEAD~100 --json | jq '.SourceMetadata.Data.Git'
```
- Check `--branch` flag to scope to a specific branch.
- Flag commits that introduced secrets even if later removed — they remain in history and require `git filter-repo` or BFG Repo Cleaner for remediation.
- Report the commit SHA, author, and timestamp for each finding.

### 5. Output Format

Produce findings in two formats:

**SARIF** (for GitHub/Azure DevOps integration):
```json
{
  "runs": [{
    "results": [{
      "ruleId": "aws-access-key",
      "level": "error",
      "message": { "text": "AWS Access Key detected" },
      "locations": [{ "physicalLocation": { "artifactLocation": { "uri": "config/settings.py" }, "region": { "startLine": 42 }}}]
    }]
  }]
}
```

**Human-readable summary table**:
```
SEVERITY  | FILE                  | LINE | SECRET TYPE        | COMMIT
CRITICAL  | config/settings.py    |  42  | AWS Access Key     | a1b2c3d
HIGH      | .env.example          |   7  | Stripe Secret Key  | HEAD
```

### 6. Remediation Guidance

For each confirmed finding, provide:
1. **Immediate**: Revoke the exposed credential at the provider (AWS IAM, GitHub settings, Stripe dashboard).
2. **Short-term**: Replace with environment variable (`os.environ['SECRET_KEY']`) or secrets manager reference (AWS Secrets Manager ARN, HashiCorp Vault path, Azure Key Vault secret URI).
3. **History cleanup**: If in git history, use `git filter-repo --path <file> --invert-paths` or BFG `--delete-files`.
4. **Prevention**: Add `.gitleaks.toml` + pre-commit hook, set `SECRETS_BASELINE` in CI to block new commits.

## Additional Scan Targets

**Git submodule scanning:** By default, TruffleHog and Gitleaks do not recurse into submodules. Add `--include-submodules` (TruffleHog) or configure `[allowlist] paths` inversely. Run `git submodule update --init --recursive` before scanning so submodule history is available locally.

**Jupyter notebook cell output:** Notebook `.ipynb` files store cell outputs (including printed secrets) as JSON. Use `nbstripout` (`pip install nbstripout`) to strip output before committing: `nbstripout --install` adds a pre-commit hook. Scan existing notebooks with `trufflehog filesystem --directory . --json` which reads IPYNB as text and catches secrets in output cells.

**Blast radius analysis for shared secrets:** When a secret is shared across multiple services (e.g., a shared DB password, a monorepo-wide signing key), rotation affects all consumers simultaneously. Before rotating: enumerate all services using the secret (`grep` across repos/configs), plan a coordinated rollout, and verify each service's ability to hot-reload secrets (e.g., via AWS Secrets Manager rotation Lambda) before revoking the old credential.

## Edge Cases

**False positives in test fixtures**: Suppress with `# gitleaks:allow` inline comment or add path exclusion in `.gitleaks.toml` under `[allowlist] paths`. Always verify suppressed patterns are not real credentials.

**Secrets in binary/compiled files**: TruffleHog's `--only-verified` flag reduces noise but may miss unverified live secrets. Run `strings` extraction separately on `.jar`, `.pyc`, `.wasm` artifacts.

**Monorepos with multiple .env files**: Scope scans per service directory. Use `gitleaks detect --source ./services/auth` per bounded context to keep signal-to-noise ratio high.

## CI Integration Example

```yaml
# .github/workflows/secret-scan.yml
- name: Run Gitleaks
  uses: gitleaks/gitleaks-action@v2
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    args: --report-format sarif --report-path results.sarif

- name: Upload SARIF
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: results.sarif
```
