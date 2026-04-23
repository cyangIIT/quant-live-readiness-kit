# Incident post-mortem template

_Commit completed post-mortems under `incidents/YYYY-MM-DD-<slug>.md`._

## Summary

- **Title**:
- **Detected at** (UTC):
- **Resolved at** (UTC):
- **Severity**: WARN | HALT
- **Author**:
- **Reviewer**:

One paragraph: what happened, what was the user-visible effect, what fixed it.

## Timeline

| Time (UTC) | Event |
|------------|-------|
| ...        | ...   |

Include: detection, first mitigation, escalation, resolution, all-clear.

## What we saw

### Manifest / contamination
- `git_sha`:
- `config_hash`:
- Any contamination findings at detection time:

### Reconciliation
- Model fills in the affected window:
- Broker fills in the affected window:
- Divergences (by kind):

### Monitoring
- Rule(s) that fired:
- Metrics at fire time:
- Any rules that *should* have fired but did not:

## Root cause

<!-- Be specific. "Data feed was slow" is not a root cause; "connection
  pool exhausted because X concurrent requests and pool size was 4" is. -->

## What worked

<!-- What saved us? Any monitoring rule / runbook step / safety net that
  earned its keep? Keep these. -->

## What did not work

<!-- What had to be done manually that should have been automatic?
  What surprised us? -->

## Action items

- [ ] **code** — _(owner, by-date)_
- [ ] **monitoring** — add / tighten rule — _(owner, by-date)_
- [ ] **runbook** — update step — _(owner, by-date)_
- [ ] **test** — regression test for this path — _(owner, by-date)_
- [ ] **communication** — inform stakeholders / users — _(owner, by-date)_

## Lessons

<!-- One or two bullets. Post-mortems that don't change anything are a
  bad sign. -->
