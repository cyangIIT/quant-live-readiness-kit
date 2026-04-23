# quant-live-readiness-kit

> **A practical toolkit for turning a systematic trading strategy from a
> research backtest into an auditable paper/live-ready system.**
>
> Freeze manifests · contamination detection · paper-vs-model
> reconciliation · monitoring & kill switches · promotion gates ·
> incident/runbook templates.

[![ci](https://github.com/cyangIIT/quant-live-readiness-kit/actions/workflows/ci.yml/badge.svg)](./.github/workflows/ci.yml)
[![license: MIT](https://img.shields.io/badge/license-MIT-informational)](LICENSE)
![python: 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)

---

## First 60 seconds

```bash
git clone https://github.com/cyangIIT/quant-live-readiness-kit.git
cd quant-live-readiness-kit
pip install -e ".[demo]"
qlrk demo
```

`qlrk demo` pulls real AAPL daily bars from yfinance, runs a **toy
SMA-crossover example** on top of them, and pipes the result through
the toolkit's freeze → reconcile → monitor → gate → review pipeline.
You get a single Markdown report at `.qlrk_state/demo/demo_report.md`
that links every artifact the toolkit produced.

> The SMA-crossover strategy is **toy / demo / educational only** — it
> is not alpha, not validated, and not investment advice. The AAPL
> price data is real public market data. The slippage and broker-fill
> divergences the demo surfaces are synthetic, clearly marked in the
> generated CSVs.

No network? Add `--offline` to use the bundled cached CSV:

```bash
qlrk demo --offline
```

## Why this exists

Research produces a strategy. Live trading requires **operations**:
freeze what is running, detect drift, reconcile every fill, watch the
metrics that could bankrupt you, have a kill switch, have a runbook,
have a post-mortem template.

Every systematic trader eventually rebuilds a version of this. Here is
an opinionated, generic version, extracted from real paper-to-live
experience and scrubbed of any strategy content.

## What this is

A small Python package + CLI (`qlrk`) that gives you:

- **Freeze manifests** — one JSON per session snapshotting config, git
  state, feature flags, and a hash. Commit one as your "clean baseline"
  and every future session can be diffed against it.
- **Contamination detection** — structural diff between a current
  manifest and the clean baseline. Tells you exactly which field
  drifted and at what severity.
- **Paper-vs-model reconciliation** — classify divergences between the
  fills your strategy *expected* and the fills your broker *reported*.
  Outputs structured JSON; exit code 1 if anything diverges.
- **Monitoring** — evaluate arbitrary metrics against YAML-defined rules,
  return PASS / WARN / HALT, detect state transitions so alerts don't
  spam.
- **Kill switch** — crash-safe on-disk flag with idempotent
  engage/clear. Your order path reads one file before every submission.
- **Alerting** — pluggable adapters (console, file, webhook stub);
  fires only on state transitions.
- **Promotion gates** — score a checklist (booleans, thresholds, manual
  sign-off) to decide if you are ready for the next stage.
- **Reporting** — render Markdown incident post-mortems and daily
  reviews from structured inputs.
- **Templates** — paper-validation plan, monitoring thresholds,
  promotion-gate checklist, post-mortem template, limited-live
  operating envelope.

## What this is NOT

- **Not a strategy or alpha.** No signal logic, no features, no
  thresholds that encode edge. The only strategy that ships is a
  deliberately-trivial SMA crossover used to make the demo work.
- **Not a backtester.** Bring your own engine (Backtrader, Zipline,
  vectorbt, custom — it does not matter).
- **Not a broker integration.** No Alpaca, IBKR, or anything else.
  Reconciliation takes two CSVs.
- **Not an ML or optimization framework.**
- **Not a performance-claim machine.** Nothing in this repo says a
  strategy works.

## Who it's for

- **Solo quants** with a promising backtest who have never run a paper
  account end-to-end and want to start without reinventing the wheel.
- **Small systematic-trading teams** who want shared operational
  hygiene that outlives a specific strategy.
- **Advanced retail / prop traders** who need an auditable path between
  *"my model said this"* and *"the broker did that"*.

## Install

```bash
# Minimal: just the toolkit + CLI (no demo dependencies)
pip install quant-live-readiness-kit

# With the public demo
pip install "quant-live-readiness-kit[demo]"

# From a source checkout
pip install -e ".[dev]"
```

Verify:

```bash
qlrk --version
qlrk --help
```

## Running the demo

```bash
qlrk demo
```

Produces under `.qlrk_state/demo/`:

```
bars.csv                 # real AAPL daily bars used by the demo
signals.csv              # toy SMA-crossover signals
model_fills.csv          # what the toy strategy expected to fill
broker_fills.csv         # simulated broker CSV (slippage + one drop)
config.yaml              # snapshot of the demo run config
manifest.json            # freeze manifest (qlrk freeze)
contamination.json       # drift check result (qlrk freeze)
reconciliation.json      # classified model-vs-broker divergences
health.json              # PASS/WARN/HALT monitoring report
gate.json                # promotion-gate evaluation
alerts.jsonl             # alert router log
demo_report.md           # ← open this first
```

The `demo_report.md` is the single entry point — it summarises every
step and links to every artifact.

## Using each subcommand directly

```bash
qlrk freeze --config examples/config.example.yaml \
            --out out/manifest.json \
            --contaminated-against examples/clean_window_manifest.example.json \
            --contamination-out out/contamination.json

qlrk reconcile --model examples/sample_model_fills.csv \
               --broker examples/sample_broker_fills.csv \
               --out out/recon.json

qlrk monitor --rules examples/monitoring_rules.example.yaml \
             --metrics examples/sample_metrics.json \
             --out out/health.json

qlrk gate --checklist examples/promotion_gate.example.yaml \
          --metrics examples/sample_metrics.json \
          --manual examples/manual_overrides.example.yaml \
          --out out/gate.json

qlrk incident --inputs examples/incident_inputs.example.json \
              --out out/incident.md

qlrk daily --date 2026-01-02 \
           --manifest out/manifest.json \
           --contamination out/contamination.json \
           --reconciliation out/recon.json \
           --health out/health.json \
           --out out/daily_review.md
```

See [`examples/walkthrough.md`](examples/walkthrough.md) for the full
guided walkthrough.

## Example workflow

```
  backtest
     │
     ▼
  qlrk freeze   ──── CLEAN_WINDOW_MANIFEST.json (commit this)
     │
     ▼
  paper-validation  ──── every session:
                        • qlrk freeze + contamination check
                        • qlrk monitor (alerts on transition)
                        • qlrk reconcile at EOD
                        • kill switch honored in order path
     │
     ▼
  qlrk gate     ──── paper → limited-live checklist
     │
     ▼
  limited-live (small real capital, documented envelope)
     │
     ▼
  qlrk gate     ──── limited-live → full-live
     │
     ▼
  full-live
```

## Architecture overview

```
src/qlrk/
├── freeze.py           # manifest snapshot, atomic write, hash
├── contamination.py    # structural diff of two manifests
├── reconciliation.py   # fill-level diff, classifier
├── monitoring.py       # threshold evaluator, transition detector
├── killswitch.py       # crash-safe persistent flag
├── alerting.py         # pluggable adapters + transition router
├── promotion.py        # YAML-driven gate scorer
├── reporting.py        # Markdown incident / daily renderers
├── demo.py             # public demo (yfinance + SMA toy)
├── io_utils.py         # safe I/O, hash helpers
└── cli.py              # `qlrk` argparse entry
```

Each module is self-contained, strategy-agnostic, and tested.

## Sample output preview

Excerpt from a real `demo_report.md`:

```markdown
# qlrk demo report — AAPL

> TOY / DEMO / EDUCATIONAL ONLY.

## Inputs
- ticker: AAPL
- data source: yfinance (400 bars, 2024-09-17 → 2026-04-22)
- toy strategy: SMA(10) × SMA(30) crossover

## Toolkit pipeline
- freeze       : 8dc32ac637ab… → manifest.json
- contamination: admissible = True
- reconcile    : matched = 11, divergences = 1
- monitor      : state = WARN
- gate         : passed = True (stage=demo_promotion)
```

## Docs

- [Concepts](docs/concepts.md)
- [Installation](docs/installation.md)
- [Walkthrough](docs/walkthrough.md)
- [Config reference](docs/config_reference.md)
- [Extension guide](docs/extension_guide.md)
- [Adapting to your strategy](docs/adapting_to_your_strategy.md)

## Templates

Under [`templates/`](templates/):

- `paper_validation_plan.md`
- `monitoring_thresholds.yaml`
- `promotion_gate_checklist.md`
- `incident_postmortem.md`
- `limited_live_envelope.md`
- `SKILL.md` — the full research-to-live workflow as a reusable skill

## Roadmap

- Additional alerting adapters (Slack, PagerDuty, Discord)
- Richer reconciliation matching (by `(symbol, side, ts)` fallback when
  order IDs are missing)
- Optional HTML renderer for daily reviews
- Incident CLI scaffold (create `incidents/` entry from a template)
- Example integrations with common backtesting engines

## FAQ

**Does this come with a strategy?**
No. The only strategy in the repo is the deliberately-trivial SMA
crossover used to make `qlrk demo` run end-to-end. It is not alpha.

**Will it tell me if my backtest overfit?**
No — that's a modelling question. This is the layer *around* the model.

**Does it need a broker SDK?**
No. Reconciliation takes two CSVs (model fills, broker fills). Export
from whatever you use.

**Can I use it with [insert backtesting library]?**
Yes. The toolkit is IO-agnostic.

**Is the yfinance dependency required?**
Only for the `demo` subcommand. The core toolkit depends on PyYAML
only. Install extras with `pip install "quant-live-readiness-kit[demo]"`
to run the demo.

**Why MIT?**
Friction should be low. If you ship a fork or a service, just keep the
notice.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Scope is narrow on purpose:
operational infrastructure only. Strategy / alpha PRs will be declined.

## Code of Conduct

We follow the [Contributor Covenant 2.1](CODE_OF_CONDUCT.md).

## Security

See [SECURITY.md](SECURITY.md). Report vulnerabilities privately via
GitHub's Security tab. Never commit real credentials, real trade logs,
or real tickers in pull requests.

## Citation

If this toolkit is useful in your research or engineering work, please
cite it via [CITATION.cff](CITATION.cff) or:

> quant-live-readiness-kit contributors. _quant-live-readiness-kit:
> operational infrastructure for taking systematic trading strategies
> from research to auditable paper/live readiness._ 2026.
> <https://github.com/cyangIIT/quant-live-readiness-kit>

## License

MIT — see [LICENSE](LICENSE).
