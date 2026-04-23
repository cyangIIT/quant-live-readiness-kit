# Concepts

## Freeze manifest

A *freeze manifest* is a single JSON artifact that answers the question
"**what was running when I decided this was good?**"

It captures:

- the full strategy config (you hand it a dict, it hashes it)
- named feature flags (booleans or enums that guard behaviour)
- the current git commit SHA
- whether the working tree is dirty (and which files are modified)
- the Python version
- a SHA-256 over everything above, canonicalised

You emit one at the start of each session and keep one as the
**clean baseline** (the admitted-good snapshot at the end of paper
validation). Contamination detection diffs any subsequent manifest
against the clean baseline.

## Contamination

"Contamination" in this toolkit is the structural answer to: "can
today's session count as evidence toward promotion, or has something
drifted?" The check is purely structural — no business judgement.

The module returns a ``ContaminationReport`` with per-key findings of
severity `warn` or `block`. The report is `admissible` iff there are no
`block` findings.

Policy decisions (git SHA change = block or warn? feature flag change =
block or warn?) are passed as function arguments, so a team can adopt
whatever convention fits them.

## Paper-vs-model reconciliation

Two lists of fills:

- **model fills** — what the strategy *intended* to do. Emit them from
  your backtest replay or your intention-logger at the same moment the
  engine places an order.
- **broker fills** — what the broker actually reported. Export from your
  paper or live account.

`reconcile(model, broker)` matches by `order_id` and classifies any
divergence. Any divergence is a signal worth looking at — some are
benign (1-cent price differences within tolerance), others are ops bugs
(missing fills, wrong sides, quantity splits).

Divergence kinds:

- `missing_at_broker` — model expected a fill, broker has none.
- `extra_at_broker` — broker has a fill the model did not intend.
- `price_mismatch` — matched pair exceeds `price_tolerance`.
- `qty_mismatch` — matched pair exceeds `qty_tolerance`.
- `side_mismatch` — BUY vs SELL (or symbol) disagrees.
- `timing_skew` — reserved for future use.

## Monitoring

`evaluate(metrics, rules)` → `HealthReport`. Each rule is
`metric op threshold` with severity WARN or HALT; the report's `state`
is the worst triggered severity, or PASS.

The module is a pure function; it does no I/O and does not side-effect.
Pair it with `qlrk.alerting.AlertRouter` to turn state transitions into
notifications, and `qlrk.killswitch` to turn a HALT into a blocked
order path.

## Kill switch

A kill switch is one on-disk JSON flag. Your order-submission code path
reads it before every order. Engage / clear is idempotent and crash-safe.

It does **not** close positions. Exits follow whatever logic your engine
already has. The kill switch only prevents *new* orders.

## Alerting

`AlertRouter` forwards `Alert` objects to any number of adapters. The
router persists the last severity it dispatched and suppresses
duplicates — you get an alert on WARN→HALT or HALT→PASS, not on every
tick while a rule stays red.

Bundled adapters: `ConsoleAdapter`, `FileAdapter`, `WebhookAdapter`. Add
your own by implementing a single `emit(alert)` method.

## Promotion gate

A YAML checklist of checks. Each check is:

- `boolean` — reads a metric key expected to be truthy
- `threshold` — reads a metric key, compares to a threshold with an op
- `manual` — requires an explicit override (operator sign-off)

`score(checklist, metrics)` → `GateResult`. Every check must pass for
`result.passed` to be True. The per-check breakdown tells you exactly
what blocked promotion.

## Reporting

Two Markdown renderers:

- `render_incident(...)` — a complete post-mortem from structured input.
- `render_daily_review(...)` — an end-of-session summary.

Markdown commits cleanly in an `incidents/` folder and reviews well in
pull requests.
