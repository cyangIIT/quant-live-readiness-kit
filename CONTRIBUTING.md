# Contributing

Thanks for your interest in contributing to `quant-live-readiness-kit`.

This project is deliberately **scope-narrow**: operational infrastructure for
moving a systematic trading strategy from research to auditable paper/live
readiness. It is not an alpha framework, not a backtesting engine, and not a
broker integration.

## Scope

Contributions in scope:

- Bug fixes in existing modules
- Additional report/diff formats
- New pluggable alerting adapters (Slack, Discord, PagerDuty, email)
- Better CLI ergonomics
- Platform coverage (Windows path handling, etc.)
- Documentation improvements and additional templates

Contributions **out of scope** — these will be declined:

- Strategy/signal/alpha logic
- Specific broker SDKs as hard dependencies
- ML models, parameter optimizers
- Any content that implies a performance claim

## Ground rules

1. Every new module must work on the sample synthetic data under `examples/`.
2. Every new module must ship with unit tests.
3. No real broker credentials, real trade logs, or real tickers in examples.
4. No performance claims anywhere in the repo.
5. If your change adds a dependency, justify it in the PR description.

## Dev setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

## Style

- `ruff` for lint. Run `ruff check src tests` before submitting.
- Type hints on public functions. Dataclasses preferred over ad hoc dicts.
- Keep modules single-purpose. If a file grows past ~400 lines, split.

## PR checklist

- [ ] Tests pass locally: `pytest`
- [ ] Lint passes: `ruff check src tests`
- [ ] `CHANGELOG.md` updated under `## [Unreleased]`
- [ ] No real data, no credentials, no performance claims
- [ ] If new CLI subcommand, `docs/walkthrough.md` updated

## Security

See [SECURITY.md](SECURITY.md) for reporting vulnerabilities. Do not open a
public issue for security reports.
