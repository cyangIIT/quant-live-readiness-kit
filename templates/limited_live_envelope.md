# Limited-live operating envelope

Sign this before allocating any real capital to the strategy. It is a
contract with your future self: a small set of numbers that define the
boundary of the limited-live experiment and the rules for leaving it.

## Capital

- **Maximum total capital at risk**: $ _____
- **Maximum per-position notional**: $ _____
- **Maximum concurrent positions**: _____
- **Maximum per-day loss before kill switch**: $ _____
- **Maximum per-week loss before pause + review**: $ _____

## Instrument & market constraints

- Allowed instruments:
- Explicitly excluded instruments:
- Allowed market hours:
- Blackout dates (earnings, macro, holidays):

## Behavior constraints

- New positions only during: _____
- Hard exit cutoff: _____
- Minimum time between re-entries per instrument (cooldown): _____
- Short selling allowed? yes / no / conditional
- Leverage allowed? yes / no / max _____x

## Kill-switch auto-trip conditions

_Each of these engages the kill switch automatically. The kill switch
prevents new orders; existing positions follow the engine's exit logic._

- [ ] Drawdown ≥ hard threshold over any rolling window
- [ ] Reconciliation divergences ≥ N in a single session
- [ ] Order reject rate ≥ R% over any M-minute window
- [ ] Data feed stale for ≥ S seconds
- [ ] Any unexpected exception in the order submission path
- [ ] Operator manual engage

## Kill-switch clear policy

- **Who can clear**: only the operator named below, or a designated
  second operator.
- **Prerequisite**: a completed incident post-mortem under
  `incidents/` **and** confirmation that the triggering condition is
  back within envelope.

## Exit / graduation criteria

Stay in limited-live until **all** of these are true:

- [ ] Ran for ≥ N calendar days without an unresolved HALT
- [ ] At least M actual real-money trades
- [ ] Reconciliation match rate ≥ R%
- [ ] Drawdown at all times within envelope
- [ ] Two successful end-to-end operator drills (morning start,
      scheduled kill-switch trip, kill-switch clear, evening shutdown)

## Sign-off

- Operator: ______ Date: ______
- Reviewer: ______ Date: ______
