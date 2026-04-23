#!/usr/bin/env bash
# End-to-end demo against the synthetic sample data.
# Usage: bash scripts/run_example.sh
set -euo pipefail

STATE=".qlrk_state"
mkdir -p "$STATE"

echo "== 1. freeze =="
qlrk freeze \
  --config examples/config.example.yaml \
  --out "$STATE/manifest_today.json" \
  --contaminated-against examples/clean_window_manifest.example.json \
  --contamination-out "$STATE/contamination.json" || true

echo
echo "== 2. reconcile =="
qlrk reconcile \
  --model examples/sample_model_fills.csv \
  --broker examples/sample_broker_fills.csv \
  --out "$STATE/reconciliation.json" || true

echo
echo "== 3. monitor =="
qlrk monitor \
  --rules examples/monitoring_rules.example.yaml \
  --metrics examples/sample_metrics.json \
  --out "$STATE/health.json" \
  --alert-file "$STATE/alerts.jsonl" \
  --alert-state "$STATE/alert_state.json" || true

echo
echo "== 4. gate =="
qlrk gate \
  --checklist examples/promotion_gate.example.yaml \
  --metrics examples/sample_metrics.json \
  --manual examples/manual_overrides.example.yaml \
  --out "$STATE/gate.json" || true

echo
echo "== 5. incident =="
qlrk incident \
  --inputs examples/incident_inputs.example.json \
  --out "$STATE/incident_demo.md"

echo
echo "== 6. daily review =="
qlrk daily \
  --date 2026-01-02 \
  --manifest "$STATE/manifest_today.json" \
  --contamination "$STATE/contamination.json" \
  --reconciliation "$STATE/reconciliation.json" \
  --health "$STATE/health.json" \
  --out "$STATE/daily_review.md"

echo
echo "Artifacts written to $STATE/"
ls -1 "$STATE"
