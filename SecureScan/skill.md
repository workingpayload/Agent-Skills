---
name: securescan
description: Performs static application security testing (SAST) to identify OWASP Top 10 vulnerabilities, CWE weaknesses, and insecure coding patterns. Use when asked to security audit code, find vulnerabilities, run SAST analysis, or recommend secure coding fixes.
---

# SecureScan

## Overview

Runs SAST analysis using Semgrep, Bandit (Python), or CodeQL to identify vulnerabilities mapped to OWASP Top 10 2021 and CWE categories. Produces severity-rated findings with taint-tracking paths and concrete remediation guidance — not generic advice.

## Workflow

### 1. Tool Selection by Language

| Language | Primary Tool | Secondary |
|----------|-------------|-----------|
| Python | Bandit (`bandit -r . -f json`) + Semgrep | Safety (deps) |
| JavaScript/TypeScript | Semgrep (`semgrep --config=p/javascript`) | ESLint security plugin |
| Java | CodeQL (`codeql database analyze --format=sarif-latest`) | SpotBugs + FindSecBugs |
| Go | Semgrep (`semgrep --config=p/golang`) | gosec |
| Ruby | Brakeman (`brakeman -f json`) | Semgrep |
| PHP | Semgrep + PHPCS Security Audit | |
| Multi-language | Semgrep with `--config=p/owasp-top-ten` | CodeQL |

Always run `semgrep --config=p/secrets` alongside SAST for defense-in-depth.

### 2. Vulnerability Categories to Check

Map every finding to OWASP Top 10 2021 and CWE:

| OWASP Category | CWE | What to Look For |
|----------------|-----|------------------|
| A01 Broken Access Control | CWE-284, CWE-639 | Missing authz checks, IDOR patterns, path traversal |
| A02 Cryptographic Failures | CWE-327, CWE-330 | Weak algos (MD5/SHA1 for passwords, DES/RC4), hardcoded IV, non-random nonces |
| A03 Injection | CWE-89, CWE-78, CWE-917 | SQL/NoSQL/LDAP/OS command injection; unsanitized user input in queries |
| A05 Security Misconfiguration | CWE-16 | Debug mode enabled, permissive CORS (`*`), missing security headers |
| A07 Auth Failures | CWE-287, CWE-798 | Hardcoded creds, weak session tokens, missing MFA enforcement |
| A08 SSRF | CWE-918 | User-controlled URLs in HTTP requests without allowlist |
| A09 Logging Failures | CWE-778, CWE-532 | Sensitive data in logs, missing audit trails for auth events |

### 3. Taint Tracking Analysis

For injection vulnerabilities, trace the full taint path:
1. **Source**: Where does untrusted input enter? (HTTP params, headers, file uploads, env vars, DB reads from external systems)
2. **Propagation**: Does the value flow through transformations that could neutralize it? (sanitize functions, parameterized queries)
3. **Sink**: Where does the tainted value land? (SQL execute, `subprocess.run`, `eval`, `innerHTML`, file write)

Document taint path in findings:
```
TAINT PATH: request.args['user_id'] → format string → db.execute()
  File: app/routes.py, line 47 → line 53
  CWE-89 (SQL Injection), OWASP A03
```

### 4. Severity Rating

Use CVSS v3.1 base score guidance:

- **CRITICAL (9.0-10.0)**: Unauthenticated RCE, SQLi in auth bypass, hardcoded admin credentials.
- **HIGH (7.0-8.9)**: Authenticated SQLi/RCE, SSRF with internal network access, broken object-level authorization.
- **MEDIUM (4.0-6.9)**: Reflected XSS, insecure deserialization without direct code exec, weak crypto for non-password data.
- **LOW (0.1-3.9)**: Missing security headers, verbose error messages, non-sensitive info disclosure.
- **INFORMATIONAL**: Style issues, defense-in-depth recommendations.

### 5. Output Format

Produce a structured findings report:

```markdown
## Finding #1
- **ID**: SS-2024-001
- **Severity**: HIGH
- **CWE**: CWE-89 (SQL Injection)
- **OWASP**: A03:2021 – Injection
- **File**: app/models/user.py, line 83
- **Description**: String interpolation used in raw SQL query with user-supplied input.
- **Vulnerable Code**:
  ```python
  query = f"SELECT * FROM users WHERE email = '{email}'"
  db.execute(query)
  ```
- **Taint Path**: `request.form['email']` → `email` parameter → `db.execute()`
- **Remediation**: Use parameterized queries: `db.execute("SELECT * FROM users WHERE email = ?", (email,))`
- **References**: CWE-89, OWASP Testing Guide v4 OTG-INPVAL-005
```

### 6. Remediation Guidance by Category

**SQL Injection**: Always use parameterized queries or ORM (SQLAlchemy, Hibernate, ActiveRecord). Never concatenate user input into query strings.

**XSS**: Use framework-native output escaping (React's JSX auto-escaping, Django's `{{ var }}`). For raw HTML insertion, use DOMPurify with strict config.

**SSRF**: Validate URLs against an allowlist of domains/IPs. Block `169.254.169.254` (AWS metadata), `::1`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`.

**Insecure Crypto**: Replace MD5/SHA1 with SHA-256+ for integrity. Use bcrypt/argon2id for passwords (never SHA for passwords). Use AES-256-GCM for symmetric encryption.

**Hardcoded Secrets**: Move to environment variables or secrets manager. See SecretSniffer skill for scanner integration.

### 7. Additional Vulnerability Categories

**Insecure deserialization (CWE-502):** Deserializing untrusted data with native mechanisms is critical-severity. Java `ObjectInputStream.readObject()` can execute arbitrary code via gadget chains (use ysoserial to test). Python `pickle.loads()` is unsafe on any external input — replace with `json` or `msgpack`. PHP `unserialize()` with user input triggers object injection — use `json_decode()` instead. Flag any deserialization of HTTP body, message queue payloads, or cookie values using these mechanisms.

**Supply chain integrity:** Verify that dependency lockfiles (`package-lock.json`, `poetry.lock`, `Cargo.lock`) are committed and pinned to exact versions, not ranges. Check for lockfile hash verification (`npm ci` vs `npm install`). For critical dependencies, verify SLSA provenance attestations (`cosign verify-attestation`). Flag packages that override dependencies of dependencies (`npm overrides`, `pip --constraint`) without hash verification.

**Triage workflow for 400+ finding sets:** When SAST produces hundreds of findings, apply this filter order: (1) deduplicate by rule ID + file path, (2) suppress test/generated/vendor directories, (3) group by CWE category and sort by CRITICAL → HIGH, (4) present the top 10 highest-confidence findings first with full taint paths, (5) provide a count summary by severity for the full set. Never present a raw unsorted 400-item list.

## Edge Cases

**Third-party library vulnerabilities**: SAST tools miss transitive dependency CVEs. Supplement with `pip-audit`, `npm audit`, `trivy fs .` for dependency scanning. Report OSV database matches separately.

**False positives in test code**: Exclude `tests/`, `spec/`, `__tests__/` directories from severity counts but still report them — test code sometimes gets copied to production. Use `# nosec` (Bandit) or `// nosemgrep` inline to suppress confirmed false positives with justification comments.

**Framework-specific sinks**: Generic Semgrep rules miss framework-specific injection points (e.g., Django's `RawSQL()`, Spring's `@Query` with native=true, Rails' `find_by_sql`). Augment with framework-specific rulesets: `semgrep --config=p/django` or `semgrep --config=p/spring`.

## CI Integration

```yaml
- name: Semgrep SAST
  uses: semgrep/semgrep-action@v1
  with:
    config: >-
      p/owasp-top-ten
      p/secrets
      p/default
  env:
    SEMGREP_APP_TOKEN: ${{ secrets.SEMGREP_APP_TOKEN }}
```

Block PRs on CRITICAL/HIGH findings. Report MEDIUM/LOW as warnings. Upload SARIF to GitHub Security tab.
