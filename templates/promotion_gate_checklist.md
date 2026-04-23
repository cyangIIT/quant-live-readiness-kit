# Promotion gate — paper → limited-live

This is the human-readable counterpart to `promotion_gate.example.yaml`.
Copy both into your project and keep them in sync. The YAML drives the
machine check; this Markdown drives the conversation you will have with
yourself or your reviewer before flipping the switch.

## Gate stages

| From             | To               | Required outcome |
|------------------|------------------|------------------|
| backtest         | paper-validation | plan signed off  |
| paper-validation | limited-live    | gate green + operator sign-off |
| limited-live     | full-live       | envelope respected + gate green |

## Evidence required for paper → limited-live

- [ ] **Freeze manifest exists** for today's session and matches the clean
      baseline except where drift was pre-authorised.
- [ ] **Contamination admissible** — no block-severity findings.
- [ ] **Minimum paper days** met.
- [ ] **Minimum paper trades** met (total and per sleeve if relevant).
- [ ] **Drawdown within envelope** — max observed < your hard limit.
- [ ] **Fill rate acceptable** — at or above the paper-validation target.
- [ ] **Reconciliation clean** — unresolved divergences below threshold.
- [ ] **Kill switch works** — you engaged it at least once in a drill and
      confirmed the engine refused to submit new orders.
- [ ] **Alert channel tested** — at least one WARN alert was received by
      the on-call operator in the past week.
- [ ] **Runbook reviewed with operator** — someone else could run the
      morning startup and evening shutdown.
- [ ] **Operator sign-off** (explicit human yes).

## Gate-fail handling

If any check is red, **do not promote**. Fix the problem, or lower your
ambition for the next stage (e.g. smaller capital). Do not loosen the
checklist mid-run — write a new checklist for the next stage and let the
old one age out.

## Common failure modes

- "It's been 30 days but we only got 12 trades" — extend the paper window
  rather than promote on thin evidence.
- "Divergences are 3, threshold is 2, call it close enough" — no. Either
  raise the threshold deliberately *with a written reason* before the
  next run, or keep running.
- "The operator is me and I'm rushing" — this is when the checklist
  earns its keep.
