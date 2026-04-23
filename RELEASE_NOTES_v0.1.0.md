# quant-live-readiness-kit v0.1.0

> First public release. Python 3.10+, MIT-licensed.

## What this is

A small, strategy-agnostic Python toolkit + CLI (`qlrk`) that gives a
systematic trading strategy the operational scaffolding it needs to
leave research and enter auditable paper / live trading:

- **Freeze manifests** — snapshot config + feature flags + git state
  + a hash. Commit one as a clean baseline; diff every future session
  against it.
- **Contamination detection** — structural diff of two manifests;
  flags every key that drifted and at what severity.
- **Reconciliation** — classify divergences between the fills your
  *model* expected and the fills your *broker* reported. JSON out;
  exit code 1 if anything diverges.
- **Monitoring** — YAML rule set → `PASS` / `WARN` / `HALT`, with
  state-transition detection so alerts don't spam.
- **Kill switch** — crash-safe, idempotent, one file on disk. Your
  order path reads it before every submission.
- **Alerting** — pluggable adapters (console, file, webhook stub);
  fires only on transitions.
- **Promotion gates** — score a YAML checklist (booleans / thresholds
  / manual sign-off) to decide if you're ready for the next stage.
- **Reporting** — render Markdown incident post-mortems and daily
  reviews from structured inputs.

Plus: a full set of operational **templates** — paper-validation
plan, monitoring thresholds, promotion-gate checklist, post-mortem,
limited-live envelope.

## What's stable in v0.1.0

- The full CLI: `qlrk demo | freeze | reconcile | monitor | gate | incident | daily`.
- The public API of every `qlrk.*` module (see CHANGELOG).
- CI on Python 3.10 / 3.11 / 3.12 (Ubuntu).
- 54 unit + CLI tests covering every module, including the end-to-end
  demo.
- Sample data under `examples/` that every tutorial uses.

## What is intentionally missing (and why)

- **No strategy / alpha.** The only strategy in the repo is the toy
  SMA crossover used by `qlrk demo`. It is not a validated strategy.
- **No backtester.** Bring your own (Backtrader, Zipline, vectorbt,
  custom — the toolkit only ingests CSVs / JSON).
- **No broker SDK dependencies.** Reconciliation takes two CSVs.
- **No ML or parameter optimization.**

## The fastest demo

```bash
git clone https://github.com/cyangIIT/quant-live-readiness-kit.git
cd quant-live-readiness-kit
pip install -e ".[demo]"
qlrk demo
# → .qlrk_state/demo/demo_report.md
```

Offline variant (uses the bundled cached public-market CSV — no
network, no yfinance install required):

```bash
pip install -e .
qlrk demo --offline
```

## Known limitations

- **Windows path handling** has been exercised during development but
  has had less coverage in CI — please file issues with reproducers if
  you hit path-related edge cases.
- **Reconciliation matching is strictly by `order_id`.** If your
  broker strips or rewrites order IDs you will need to pre-process the
  CSVs to restore them. A `(symbol, side, ts)` fallback matcher is on
  the roadmap.
- **The webhook alerting adapter is a stub.** It POSTs JSON but does
  not retry or sign requests; swap in a real HTTP client before using
  in production.
- **No HTML report renderer yet.** Markdown only (by design — reviews
  in PRs, commits in `incidents/`).
- **The `demo` strategy is TOY.** It is a 10/30 SMA crossover on AAPL
  daily bars — illustrative only. Do not trade it.

## Roadmap (after v0.1.0)

- Slack / PagerDuty / Discord alerting adapters.
- `(symbol, side, ts)` reconciliation fallback matcher.
- Optional HTML renderer for daily reviews.
- `qlrk incident new` scaffolder that drops a template into
  `incidents/<date>-<slug>.md`.
- Example integrations with common backtesting engines.

## Thanks

This repo is a scrubbed, generic extraction of operational patterns
that have been rebuilt many times, by many people, across the
systematic-trading community. If you find a better way to do any of
these primitives, a PR is the highest-leverage way to say so.

— the quant-live-readiness-kit contributors
