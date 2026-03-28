---
name: crongenius
description: Designs correct cron expressions, schedules background jobs with overlap prevention and retry logic, and selects the right scheduler (Celery Beat, systemd timers, EventBridge, GitHub Actions schedule). Use when a user asks about cron jobs, scheduled tasks, or background job automation.
---

# CronGenius

## Overview

Produce correct, timezone-aware cron schedules with overlap prevention, retry strategies, and dead-letter handling. Choose the right scheduling backend for the deployment context.

## Workflow

### 1. Parse the Schedule Requirement

Ask or infer:
- **Frequency**: every N minutes/hours, daily at time X, weekly on day Y
- **Timezone**: always confirm — `0 9 * * *` means different things in UTC vs America/New_York
- **DST sensitivity**: does the job need to fire at local clock time (use TZ-aware scheduler) or at a fixed UTC offset?
- **Overlap risk**: can two instances run simultaneously? Most jobs cannot.

### 2. Write the Cron Expression

Standard 5-field syntax: `minute hour day-of-month month day-of-week`

```
┌─ minute       (0-59)
│ ┌─ hour        (0-23)
│ │ ┌─ DOM       (1-31)
│ │ │ ┌─ month   (1-12 or JAN-DEC)
│ │ │ │ ┌─ DOW   (0-7, 0 and 7 = Sunday, or SUN-SAT)
│ │ │ │ │
* * * * *
```

Common patterns:
```
0 2 * * *          # daily at 02:00
*/15 * * * *       # every 15 minutes
0 9 * * 1          # every Monday at 09:00
0 0 1 * *          # first of each month at midnight
0 6 * * 1-5        # weekdays at 06:00
*/5 9-17 * * 1-5   # every 5 min during business hours Mon-Fri
```

Validate expressions at [crontab.guru](https://crontab.guru) mentally — write out "fires at X, then X+interval" to confirm.

### 3. Prevent Overlapping Executions

**Linux cron + flock:**
```bash
/usr/bin/flock -n /var/lock/myjob.lock /usr/local/bin/myjob.sh
```
`-n` means "fail immediately if lock is held" — add `-w 0` for the same effect. Log when skipped.

**Celery Beat:**
```python
CELERY_BEAT_SCHEDULE = {
    'daily-report': {
        'task': 'tasks.generate_report',
        'schedule': crontab(hour=2, minute=0),
        'options': {'expires': 3600},  # drop if not consumed in 1h
    },
}
```
Use `celery-redbeat` (Redis-backed) for distributed deployments to avoid duplicate firing across multiple Beat instances.

**systemd timer (preferred over cron on modern Linux):**
```ini
# /etc/systemd/system/myjob.timer
[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true
Unit=myjob.service

# /etc/systemd/system/myjob.service
[Service]
Type=oneshot
ExecStart=/usr/local/bin/myjob.sh
```
`systemctl enable --now myjob.timer`. systemd prevents overlap natively for `Type=oneshot`.

**AWS EventBridge (serverless):**
```
rate(1 hour)
# or cron-style:
cron(0 2 * * ? *)   # Note: EventBridge uses 6 fields, year is 7th optional
```
Pair with SQS + Lambda for retry semantics.

### 4. Add Retry and Dead-Letter Logic

Never let silent failures go undetected.

**Celery:**
```python
@app.task(bind=True, max_retries=3, default_retry_delay=300)
def my_task(self):
    try:
        do_work()
    except TransientError as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 60)
```
Configure a dead-letter queue (DLQ):
```python
task_reject_on_worker_lost = True
task_acks_late = True
```

**GitHub Actions schedule (CI-hosted jobs):**
```yaml
on:
  schedule:
    - cron: '0 2 * * *'
```
Add `timeout-minutes: 30` and `continue-on-error: false` to fail visibly.

**GitHub Actions inactivity warning**: GitHub automatically disables scheduled workflows on public repos after 60 days of no repository activity (no pushes, PRs, etc.). Add a periodic commit or use the GitHub API to re-enable the workflow. Monitor via the Actions UI or set a calendar reminder for long-running scheduled workflows.

**Celery Beat rolling deploy**: During a rolling deploy, multiple Beat instances may run briefly in parallel, causing duplicate task fires. Prevent this by using `celery-redbeat` (Redis-backed distributed lock) so only one Beat instance holds the scheduler lock at a time. Do not run more than one Beat process per environment without a distributed lock backend.

### 5. Handle Timezones Correctly

- Always store and compute in UTC internally.
- Use TZ-aware schedulers for local-time jobs:
  - Celery Beat: `timezone = 'America/New_York'` in config
  - systemd: `OnCalendar=America/New_York *-*-* 09:00:00`
  - EventBridge: no native TZ — compute UTC offset and adjust for DST manually, or use a Lambda to re-schedule

### 6. Document the Schedule

For every scheduled job, record:
```
Job: generate-monthly-invoices
Schedule: 0 1 1 * * (first of month, 01:00 UTC)
Timezone: UTC
Max runtime: 30 minutes
Overlap prevention: flock /var/lock/invoices.lock
On failure: PagerDuty alert + DLQ
Owner: billing-team
```

## Output Format

Provide:
1. The cron expression with an English plain-language description
2. The platform-specific scheduler config block
3. The overlap prevention mechanism
4. The retry/failure handling approach

## Edge Cases

**DST clock changes**: A job at `0 2 * * *` America/New_York will fire at 01:00 or 03:00 UTC depending on DST. If exact local time matters, use a TZ-aware scheduler. If the job must always fire at a fixed UTC time, document the apparent local time shift.

**Month-end edge cases**: `0 0 31 * *` silently skips months with fewer than 31 days. Use `0 0 28-31 * *` + an idempotency check in the job, or use a scheduler that supports `last day of month` (EventBridge supports `L`).

**Catching up missed runs**: systemd `Persistent=true` replays missed runs after downtime. Celery Beat does not replay by default. Add idempotency keys to jobs that must not double-execute on catch-up.
