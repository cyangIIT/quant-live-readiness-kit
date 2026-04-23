# Extension guide

The toolkit is small on purpose. If you need something that is not
there, here is where it goes.

## Add a new alert adapter

Implement the `Adapter` protocol in `qlrk.alerting`:

```python
from qlrk.alerting import Alert

class SlackAdapter:
    def __init__(self, webhook_url: str):
        self.url = webhook_url

    def emit(self, alert: Alert) -> None:
        # ... POST to Slack webhook ...
        ...
```

Then wire it into the router:

```python
from qlrk.alerting import AlertRouter, ConsoleAdapter

router = AlertRouter(
    adapters=[ConsoleAdapter(), SlackAdapter("https://hooks.slack.com/...")],
    state_path="logs/alert_state.json",
)
```

Please contribute adapters back if they are general-purpose. Keep the
adapter self-contained (no cross-module dependencies).

## Add a new promotion-gate check kind

In `qlrk.promotion.score`, extend the `kind` dispatch. New kinds should
follow the same `(name, kind, passed, detail)` contract. Keep the
semantics strict — "unknown" kinds should fail closed (return
`passed=False`), not pass through.

## Add a new reconciliation divergence kind

Extend the `Divergence.kind` docstring and add a classification branch
in `reconcile`. Keep the set small; adding kinds makes downstream
handling harder.

## Plug the kill switch into your engine

In your order-submission code path:

```python
from qlrk.killswitch import is_engaged

KILL_PATH = "logs/kill_switch.json"

def submit_order(order):
    if is_engaged(KILL_PATH):
        log.warning("kill switch engaged; refusing %s", order)
        return None
    return broker.submit(order)
```

In your monitoring loop:

```python
from qlrk import killswitch, monitoring

health = monitoring.evaluate(metrics, rules)
if health.state == "HALT":
    killswitch.engage(
        KILL_PATH,
        reason="; ".join(t.describe() for t in health.triggered),
        operator="auto-monitor",
    )
```

## Emit fills in the reconciliation CSV format

Your model-side CSV needs: `order_id,symbol,side,qty,price,ts`. The
simplest pattern is to log the intent at the moment of submission:

```python
import csv

with open("model_fills.csv", "a", newline="") as fh:
    w = csv.writer(fh)
    w.writerow([order.client_id, order.symbol, order.side,
                order.qty, order.limit_price, order.ts.isoformat()])
```

On the broker side, export via the broker's account-activity endpoint
with the same schema.

## Guidance

- Keep new modules under 400 lines. Split if they grow.
- Default behaviour should not need a config file. The toolkit must
  work out of the box on the samples.
- No performance claims in code comments, docstrings, or READMEs.
- Synthetic sample data only. Never commit real tickers, real fills, or
  real credentials.
