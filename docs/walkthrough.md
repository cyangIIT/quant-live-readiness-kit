# Walkthrough

This is a narrative walkthrough of a full paper-validation session with
the toolkit. It mirrors the commands in
[`examples/walkthrough.md`](../examples/walkthrough.md) but adds the
context of what each step means.

## Starting position

You have a strategy. You have a config file (YAML or JSON — the toolkit
does not care). You have some way of emitting fills from your engine
and getting fills back from your broker or paper account.

## Step 1 — establish a clean baseline

At the moment you believe the strategy is "good enough to start paper":

```bash
qlrk freeze --config config.yaml --out CLEAN_WINDOW_MANIFEST.json
git add CLEAN_WINDOW_MANIFEST.json && git commit -m "freeze clean baseline"
```

From here on, this file is the answer to "what was running when I
admitted this strategy into paper-validation?"

## Step 2 — every session start, freeze again and diff

```bash
qlrk freeze --config config.yaml --out logs/manifest_$(date -u +%F).json \
            --contaminated-against CLEAN_WINDOW_MANIFEST.json \
            --contamination-out logs/contamination_$(date -u +%F).json
```

Exit code 0 means today's config is admissible as promotion evidence.
Exit 2 means a blocking drift was detected — fix it before trading, or
accept that today's session does not count.

The most common drifts:

- `dirty` — you edited a file and forgot to commit. Commit or stash.
- `config.xxx` — you tuned a threshold. Was that intentional?
- `feature_flag.yyy` — you flipped a flag. Re-run the clean baseline or
  roll back.

## Step 3 — every bar / tick, run monitoring

```bash
qlrk monitor --rules monitoring.yaml --metrics live_metrics.json \
             --out logs/health.json \
             --alert-file logs/alerts.jsonl \
             --alert-state logs/alert_state.json
```

Exit code 0 = PASS, 1 = WARN, 2 = HALT. On HALT, have your engine call
`qlrk.killswitch.engage(...)` (or shell-out to your own wrapper).

## Step 4 — end of session, reconcile

Export fills from both sides into CSVs with columns
`order_id, symbol, side, qty, price, ts`:

```bash
qlrk reconcile --model model_fills.csv --broker broker_fills.csv \
               --out logs/reconciliation_$(date -u +%F).json
```

Any divergence warrants a look. If you see more than one or two, file
an incident.

## Step 5 — end of session, daily review

```bash
qlrk daily --date $(date -u +%F) \
           --manifest logs/manifest_$(date -u +%F).json \
           --contamination logs/contamination_$(date -u +%F).json \
           --reconciliation logs/reconciliation_$(date -u +%F).json \
           --health logs/health.json \
           --out logs/daily_$(date -u +%F).md
```

Commit the Markdown to your project. Over time, the `logs/daily_*.md`
folder becomes your narrative record of the validation.

## Step 6 — when something goes wrong

```bash
qlrk incident --inputs incident_inputs.json \
              --out incidents/$(date -u +%F)-slug.md
```

Structure the `inputs` JSON with the template from
`templates/incident_postmortem.md`. Commit the rendered Markdown.

## Step 7 — promotion decision

At the end of paper-validation:

```bash
qlrk gate --checklist templates/promotion_gate_checklist.md.yaml \
          --metrics aggregate_metrics.json \
          --manual operator_signoffs.yaml \
          --out logs/promotion_decision.json
```

Exit 0 = green. Any other exit = something on the checklist blocked
promotion — look at `logs/promotion_decision.json` for the per-check
breakdown.
