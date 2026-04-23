# Paper-validation plan

_Copy this file into your project as `paper_validation_plan.md` and fill
in the sections before starting paper trading. Keep it committed —
pre-registration is a ward against moving goalposts._

## Strategy identifier

- Name / code name:
- Config path (relative to repo root):
- Clean baseline manifest path:
- Expected start date (UTC):
- Planned paper duration (calendar days):

## Hypothesis being tested

<!-- One paragraph. What must be true in paper for you to be willing to
  risk real money? This is NOT "the strategy is profitable" — it is
  "paper behaves close enough to the backtest that I believe the backtest
  is representative of what production would do". -->

## Pre-registered success criteria

All must be satisfied at the end of the window for promotion to be
considered. Do not weaken these mid-run.

- Minimum calendar days:
- Minimum trades taken (per sleeve if multi-sleeve):
- Maximum reconciliation divergences (all-time):
- Maximum WARN-state minutes per day:
- Maximum HALT incidents (strict: > 0 requires explicit re-qualification):
- Operator runbook rehearsed end-to-end at least once:

## Pre-registered failure criteria

If any of these triggers, stop the validation, do not promote, investigate
first:

- Drawdown > ___ % over any N-day window
- Reconciliation match-rate < ___ %
- Kill switch engaged more than ___ times
- Any crash of the engine process that did not self-recover

## Known risks / watch-list

<!-- What do you worry about? Data feed? Execution latency? Symbol
  universe? Be specific. -->

## Operator responsibilities

- Who is on call each day?
- Escalation path if kill switch engages outside work hours?

## Sign-off

- Author: ______ Date: ______
- Reviewer: ______ Date: ______
