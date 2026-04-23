# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-04-23

First public release.

### Added
- `qlrk.freeze` — generate and diff baseline manifests (config hash, git SHA,
  feature flags, dirty-tree detection).
- `qlrk.contamination` — detect divergence between a current manifest and an
  admitted-clean manifest; emits a structured reason list.
- `qlrk.reconciliation` — diff model-expected fills vs broker-reported fills;
  classify by cause (extra, missing, price_mismatch, qty_mismatch, side_mismatch,
  timing_skew).
- `qlrk.monitoring` — threshold evaluator that produces PASS / WARN / HALT
  states with transition detection.
- `qlrk.killswitch` — crash-safe kill-switch state file. Idempotent,
  survives process restart.
- `qlrk.alerting` — pluggable adapters (console, file, webhook stub); fires
  only on state transitions to avoid spam.
- `qlrk.promotion` — score a promotion gate (paper → limited-live → full-live)
  against a YAML checklist.
- `qlrk.reporting` — render Markdown incident post-mortems and daily reviews.
- `qlrk.demo` + `qlrk demo` CLI — end-to-end public demo using yfinance AAPL
  daily bars and a toy SMA-crossover strategy. Offline fallback to a bundled
  cached CSV; produces a single `demo_report.md` with all artifacts linked.
- CLI: `qlrk demo | freeze | reconcile | monitor | gate | incident | daily`.
- Bundled public market-data snapshot: `examples/sample_aapl_daily.csv`
  (real AAPL daily bars, auto-adjusted, snapshot captured 2026-04-22).
- Synthetic sample fill/config data under `examples/`.
- Templates under `templates/` for paper-validation, monitoring thresholds,
  promotion-gate checklist, incident post-mortem, limited-live envelope, and
  a full research-to-live workflow SKILL.md.
- GitHub Actions CI (lint + tests on Python 3.10/3.11/3.12).
- Community health files: LICENSE (MIT), CONTRIBUTING, SECURITY,
  CODE_OF_CONDUCT, CITATION.cff, issue and PR templates.
