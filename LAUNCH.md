# Launch pack

Copy/paste-ready materials for making `quant-live-readiness-kit` public.

---

## GitHub repo description (one line, ≤ 160 chars)

> Operational toolkit for taking a systematic trading strategy from
> research backtest to auditable paper/live readiness — freeze
> manifests, reconciliation, monitoring, kill switches, promotion
> gates.

Alternate shorter:

> The operations layer your backtest needs before real money.

---

## GitHub topics / tags

```
quant  trading  systematic-trading  algorithmic-trading
paper-trading  live-trading  risk-management
operations  devops  observability
python  cli  reconciliation  monitoring  kill-switch
runbook  post-mortem  promotion-gate
```

---

## README hero section

Already in `README.md`. Preview:

```
# quant-live-readiness-kit
> A practical toolkit for turning a systematic trading strategy from a
> research backtest into an auditable paper/live-ready system.
>
> Freeze manifests · contamination detection · paper-vs-model
> reconciliation · monitoring & kill switches · promotion gates ·
> incident/runbook templates.
```

Screenshots / badges are already placed and point at
`github.com/cyangIIT/quant-live-readiness-kit`.

---

## LinkedIn — short post draft (≤ 1300 chars)

```
I open-sourced the infrastructure layer I wish existed when I started
running a systematic strategy in paper.

Not the strategy. Not the signal. Not the alpha. The unglamorous plumbing
that sits around it:

• Freeze manifests — snapshot config + git state + feature flags, hash
  it, diff every future session against the clean baseline.
• Contamination detection — a structured "what drifted?" report.
• Paper-vs-model reconciliation — classify every divergence between
  what your model intended and what your broker filled.
• Monitoring with PASS / WARN / HALT transitions.
• A kill switch that survives process restart.
• A promotion-gate checklist between paper → limited-live → full-live.
• Markdown renderers for incident post-mortems and daily reviews.

It's called quant-live-readiness-kit. Written in Python, MIT-licensed,
works with any backtester and any broker. Everything is runnable against
synthetic sample data — you can try it in under 10 minutes.

Repo: github.com/cyangIIT/quant-live-readiness-kit
Feedback, adapters (Slack, PagerDuty, Discord), and issue reports all
welcome.
```

---

## LinkedIn — longer post draft (≤ 3000 chars)

```
I've been running a systematic trading strategy end-to-end — from
backtest to paper to a tiny bit of real money — for long enough that
the question "is this strategy profitable?" stopped being the
interesting one.

The interesting question turned out to be: "do I actually know what's
running right now?"

Because the answer was often: not really.

* Somebody (me) tuned a parameter and forgot to commit.
* A feature flag flipped during testing and stayed flipped.
* The broker filled at a different price than the backtest assumed and
  the model's P&L drifted away from reality without anyone noticing.
* The "kill switch" was a comment saying "TODO: kill switch".

Every systematic trader rebuilds a version of this operational layer.
Most of us do it badly, incrementally, and late.

So I extracted mine, scrubbed out every strategy-specific bit, and
open-sourced it: quant-live-readiness-kit. It ships with:

• qlrk freeze — snapshot config + git SHA + feature flags + hash,
  detect contamination vs a clean baseline.
• qlrk reconcile — diff model fills vs broker fills, classify every
  divergence by cause (missing, extra, price mismatch, qty mismatch,
  side mismatch).
• qlrk monitor — evaluate arbitrary metrics against YAML rules, return
  PASS / WARN / HALT, fire alerts on state transitions.
• qlrk killswitch — crash-safe, idempotent, survives restart; your
  order path reads one file before every submission.
• qlrk gate — score a promotion checklist (paper → limited-live →
  full-live).
• qlrk incident — render a Markdown post-mortem from structured input.
• qlrk daily — render an end-of-session review.

Plus templates for: paper-validation plan, monitoring thresholds,
promotion-gate checklist, incident post-mortem, limited-live operating
envelope.

No strategy, no signal, no broker SDK, no ML. Bring your own of each.
Python 3.10+, MIT-licensed, runnable against synthetic data in <10 min.

If you've got a backtest you believe in and you're about to flip it to
paper, this is the scaffolding I wish someone had handed me.

Would love feedback, especially on:
• additional alerting adapters (Slack, PagerDuty, Discord)
• integrations with specific backtesting libraries
• the exact shape of the promotion-gate checklist

Repo: github.com/cyangIIT/quant-live-readiness-kit
```

---

## Demo / screenshot ideas

1. **Terminal recording** — one session of `bash scripts/run_example.sh`
   showing each subcommand's output in turn, ending with the
   `.qlrk_state/` listing. Use `asciinema` or a plain `script` recording.
2. **Split-pane screenshot** — `qlrk reconcile` output JSON on the left,
   the rendered Markdown daily review on the right. Makes the "structured
   → human" story visible in one image.
3. **Diagram** — the `backtest → paper → limited-live → full-live`
   pipeline from the README with `qlrk` subcommands annotated at each
   transition. Mermaid is fine; SVG export into `docs/img/`.

---

## "What I learned building this" post outline

```
# What I learned extracting operational infrastructure from a private
# quant system

1. The edge is not the interesting part
   - Operations was where I kept losing money, not signal weakness.
   - Scars: contamination you didn't notice, fills you didn't reconcile,
     kill switches that were comments.

2. Every drift is an event worth classifying
   - A "tiny parameter tune you forgot to commit" is qualitatively the
     same as a "someone pushed bad config".
   - Both invalidate today's session as evidence.
   - Making this legible is 80% of the value.

3. Reconciliation is the single best bug-finder
   - Ops bugs surface first as paper-model divergences.
   - If your paper matches your model to the cent, 90% of the usual
     surprises are already precluded.

4. The kill switch earns its keep in drills
   - Engage it in a drill, try to submit, confirm nothing goes out, clear.
   - Do it quarterly. The first drill usually finds a bug.

5. Promotion gates are the least glamorous, most important part
   - "Should I go live yet?" gets answered better by a checklist than
     a feeling.
   - Writing the checklist before the experiment is the hard part.

6. Extracting the toolkit was a useful exercise by itself
   - Half the value was deciding, per file, "is this infrastructure or is
     this alpha?" Forcing that decision cleaned up the original codebase.

# What I'd change
- I would separate intention-logging from order placement earlier.
- I would pre-register the gate checklist before touching paper.
- I would default to `git status` refusing to run the engine on a dirty
  tree, not warning.
```

---

## Call to action

Optional CTA for the public launch:

> Running or about to run a systematic strategy in paper? I'd love to
> hear what's missing. File an issue, send a PR for an adapter, or DM
> me if you want a hand wiring it into an existing engine — I'll take
> a small batch of feedback engagements.
