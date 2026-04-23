# Example walkthrough

This directory contains synthetic data you can run the toolkit against
without any real credentials, tickers, or history. Everything starts
with `DEMO*` so it is obviously not a real universe.

All commands run from the repo root.

## 1. Freeze a manifest and check it against the clean baseline

```bash
qlrk freeze \
  --config examples/config.example.yaml \
  --out .qlrk_state/manifest_today.json \
  --contaminated-against examples/clean_window_manifest.example.json \
  --contamination-out .qlrk_state/contamination.json
```

On a clean repo this should exit 0 (admissible). Edit
`examples/config.example.yaml` — flip `auto_confirm_entries` to `false` —
and rerun; you will get a structured `feature_flag` finding and exit 2.

## 2. Reconcile model fills vs broker fills

```bash
qlrk reconcile \
  --model examples/sample_model_fills.csv \
  --broker examples/sample_broker_fills.csv \
  --out .qlrk_state/reconciliation.json
```

The synthetic data contains intentional divergences:

- `ord-0001` price mismatch (100.00 vs 100.02 at 0.01 tolerance — edge)
- `ord-0005` qty mismatch (15 vs 14)
- `ord-0006` price mismatch (74.20 vs 74.80)
- `ord-0007` missing at broker
- `ord-0008` extra at broker

Exit code is 1 when any divergence is found. Useful in CI or a cron
post-session check.

## 3. Evaluate monitoring rules

```bash
qlrk monitor \
  --rules examples/monitoring_rules.example.yaml \
  --metrics examples/sample_metrics.json \
  --out .qlrk_state/health.json \
  --alert-file .qlrk_state/alerts.jsonl \
  --alert-state .qlrk_state/alert_state.json
```

Exit code: 0 for PASS, 1 for WARN, 2 for HALT. A CI job can gate on
this.

## 4. Score a promotion gate

```bash
qlrk gate \
  --checklist examples/promotion_gate.example.yaml \
  --metrics examples/sample_metrics.json \
  --manual examples/manual_overrides.example.yaml \
  --out .qlrk_state/gate.json
```

Returns 0 if every check passes; 1 otherwise, with a per-check breakdown
in the JSON output.

## 5. Render an incident post-mortem

```bash
qlrk incident \
  --inputs examples/incident_inputs.example.json \
  --out .qlrk_state/incident_demo.md
```

The resulting Markdown is a ready-to-commit post-mortem with sections
pre-populated from the JSON inputs.

## 6. Render a daily review

```bash
qlrk daily \
  --date 2026-01-02 \
  --manifest .qlrk_state/manifest_today.json \
  --contamination .qlrk_state/contamination.json \
  --reconciliation .qlrk_state/reconciliation.json \
  --health .qlrk_state/health.json \
  --out .qlrk_state/daily_2026-01-02.md
```

## End-to-end demo script

See `scripts/run_example.sh` for a one-shot demo that runs all six
commands against the sample data.
