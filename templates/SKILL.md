# SKILL: research-to-live readiness workflow

Use `quant-live-readiness-kit` templates to take a new or existing strategy
through four operational stages. Each stage has an artifact this repo
generates or stores; each gate has explicit criteria.

```
backtest  →  paper-validation  →  limited-live  →  full-live
            (≥ 30 days)         (small capital)   (full capital)
```

## Stage 1 — Pre-paper freeze

**Entry criteria**: a backtest you believe in; a config file committed to
git; the repo is clean.

**Artifacts**:

1. `config.yaml` — your strategy config (the toolkit does not care what
   the keys are; it hashes and diffs).
2. Baseline manifest — produced by `qlrk freeze --config config.yaml
   --out logs/clean_baseline.json`. Rename the result to
   `CLEAN_WINDOW_MANIFEST.json` and commit it. This is the "what was
   running when I decided this was good" snapshot.
3. `templates/paper_validation_plan.md` filled in with your pre-registered
   success criteria.

## Stage 2 — Paper-validation

**Entry criteria**: clean baseline committed, kill switch file path
decided, monitoring rules written.

**During the stage**:

- Every session start: `qlrk freeze` and diff against `CLEAN_WINDOW_MANIFEST.json`.
  Any block-severity finding means today's session is not admissible
  evidence toward promotion.
- Every session end: `qlrk reconcile` your model fills vs broker fills.
  File any divergence > `X` in the incident log.
- Every minute or bar: `qlrk monitor`. On WARN/HALT transitions, alert.
  On HALT, engage kill switch.
- Incident hits? `qlrk incident` and commit the resulting Markdown under
  `incidents/YYYY-MM-DD-<slug>.md`.

**Exit criteria** (from `templates/promotion_gate_checklist.md`):
- N days paper, M trades minimum
- zero unresolved HALT incidents
- reconciliation divergences ≤ threshold
- operator can re-run the whole workflow from scratch in < 10 minutes

Run `qlrk gate --checklist templates/promotion_gate_checklist.md ...` and
require a **green** result before proceeding.

## Stage 3 — Limited-live

**Entry criteria**: gate green, clean baseline re-freezed with live
credentials only, explicit operating envelope signed off
(`templates/limited_live_envelope.md`).

**Constraints**: real money but small. Envelope specifies the hard ceiling
on position size, per-day loss, per-week loss, max active positions, and
the kill-switch auto-trip conditions. Violations trip the kill switch
immediately and must be investigated before resuming.

## Stage 4 — Full-live

**Entry criteria**: limited-live ran for its planned window with no
violations and gate metrics all green, plus operator sign-off.

## Re-use

To adapt the workflow to a different strategy, copy this folder. Edit
`promotion_gate_checklist.md` thresholds, the monitoring rules, and the
operating envelope. The toolkit code does not change.
