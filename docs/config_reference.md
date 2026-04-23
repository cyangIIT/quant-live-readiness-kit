# Config reference

## Strategy config (`--config`)

Any YAML or JSON. The toolkit hashes the whole structure. Keys are
arbitrary; the only one with meaning is `feature_flags` (top-level),
which is lifted out of `config` and placed into a dedicated manifest
field so that flag changes are visible separately from ordinary config
drift.

Minimal example:

```yaml
universe:
  - A
  - B
risk:
  max_position_pct: 0.2
feature_flags:
  some_flag: true
```

## Monitoring rules (`--rules`)

```yaml
rules:
  - name: drawdown_halt          # human label
    metric: max_drawdown_pct     # key in your metrics JSON
    op: ">"                      # < | <= | > | >= | == | !=
    threshold: 0.07              # numeric
    severity: HALT               # WARN | HALT
    message: "..."               # optional free text
```

Rules fire when `metrics[metric] op threshold` is true and the metric
is numeric. Missing metrics do not trigger (they are silent, not an
error — this is intentional so a new metric can be rolled out without
breaking old rules).

## Metrics (`--metrics`)

A flat JSON dict of numbers / booleans. Keys are arbitrary; they must
match whatever your rules and gate reference.

## Promotion gate (`--checklist`)

```yaml
stage: limited_live

checks:
  - name: freeze_manifest_exists
    kind: boolean
    value_key: freeze_manifest_exists   # metrics[value_key] must be truthy

  - name: max_drawdown
    kind: threshold
    metric: max_drawdown_pct
    op: "<"
    threshold: 0.05

  - name: operator_signoff
    kind: manual
    default: false                      # overridden via --manual YAML
```

## Manual overrides (`--manual`)

```yaml
manual:
  operator_signoff: true
```

## Kill-switch state file

Written by `qlrk.killswitch.engage`. You don't edit it by hand, but its
schema:

```json
{
  "engaged": true,
  "reason": "...",
  "engaged_at": "2026-01-02T15:34:00+00:00",
  "operator": "alice",
  "metadata": {}
}
```

## Alert state file

Used by `AlertRouter` to suppress duplicate-severity alerts. Schema is
one key: `{"last_severity": "WARN"}`. Delete the file to reset.
