# Adapting to your strategy

This doc is for the case where you already have a working backtest and
want to drop the toolkit in without a full rewrite.

## Step 1 — commit your config

Put all of your tunable parameters into a single YAML or JSON file.
The toolkit hashes the whole thing; if you scatter parameters across
five files, every change to any of them is a drift event and you will
lose sleep. Consolidate.

Typical fields (names are yours):

- universe / symbol list
- risk / capital / position sizing parameters
- execution assumptions (slippage, max price, etc.)
- session constraints (entry window, holidays)
- feature flags — separate top-level block; surfaced specially by the
  freeze module.

## Step 2 — emit model fills from your engine

Wherever your engine *decides* to place an order, write a row to a
CSV:

```
order_id,symbol,side,qty,price,ts
```

`order_id` should be whatever ID your engine passes to the broker
(`client_order_id`, not the broker-assigned ID). This is what allows
`qlrk reconcile` to line up the two sides.

If your engine doesn't have a stable ID scheme, add one. It does not
have to be UUID-grade — monotonic `strategy-YYYYMMDD-NNN` is fine.

## Step 3 — export broker fills to the same CSV schema

Most brokers expose an activity-feed endpoint. Map its output to:

```
order_id,symbol,side,qty,price,ts
```

Timestamp format: ISO-8601 with timezone. The toolkit does not interpret
timestamps today (divergence classification is by ID) but a consistent
format makes humans able to read the diffs.

## Step 4 — define metrics you care about

Your engine likely already computes a handful of metrics each tick.
Export them to a flat JSON dict and feed it to `qlrk monitor`:

```json
{
  "max_drawdown_pct": 0.018,
  "fill_rate": 0.92,
  "order_reject_rate": 0.01,
  "open_positions": 3,
  "data_staleness_seconds": 12
}
```

Start with the ones in `templates/monitoring_thresholds.yaml`; add as
you find new failure modes.

## Step 5 — wire the kill switch into the order path

One check, one place, before every order goes out:

```python
from qlrk.killswitch import is_engaged

if is_engaged("logs/kill_switch.json"):
    return  # do not submit
```

Test it with a drill: engage, try to submit, confirm nothing goes out,
clear, try again, confirm orders flow. Write it up as a runbook step.

## Step 6 — pre-register success criteria

Copy `templates/paper_validation_plan.md` into your project. Fill in
the numbers *before* you start. Commit.

## Step 7 — run the daily loop

- Morning: `qlrk freeze` + contamination check.
- Continuously: engine computes metrics + calls `qlrk.monitoring.evaluate`.
- Evening: `qlrk reconcile` + `qlrk daily`.
- On HALT: `qlrk incident`, engage kill switch, author post-mortem.

## Step 8 — decide

At the end of the window, `qlrk gate`. Accept the verdict; do not argue
with the threshold.

## What stays yours

The strategy, the signal, the features, the universe, the parameters,
the data pipeline, the broker integration, the research process. None
of that is in this toolkit.
