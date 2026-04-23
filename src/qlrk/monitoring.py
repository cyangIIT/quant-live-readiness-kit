"""Monitoring: turn raw metrics into a PASS / WARN / HALT state.

You supply:

* a dict of current metric values (``{"drawdown_pct": 0.012, ...}``)
* a list of ``Rule`` definitions that map metric -> threshold -> severity

This module returns a ``HealthReport`` with the worst state across all
rules, plus the list of triggering rules. Pair with ``qlrk.alerting`` to
notify only on state transitions.

The module is deliberately not opinionated about *which* metrics to watch.
That is a strategy-specific decision; ``templates/monitoring_thresholds.yaml``
has example rules you can copy.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

SEVERITY_ORDER = {"PASS": 0, "WARN": 1, "HALT": 2}


@dataclass
class Rule:
    name: str
    metric: str
    op: str  # "<" | "<=" | ">" | ">=" | "==" | "!="
    threshold: float
    severity: str  # "WARN" | "HALT"
    message: str = ""

    def evaluate(self, value: float | None) -> bool:
        if value is None:
            return False
        ops: dict[str, Callable[[float, float], bool]] = {
            "<": lambda a, b: a < b,
            "<=": lambda a, b: a <= b,
            ">": lambda a, b: a > b,
            ">=": lambda a, b: a >= b,
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
        }
        fn = ops.get(self.op)
        if fn is None:
            raise ValueError(f"unknown comparison op: {self.op!r}")
        return fn(float(value), float(self.threshold))

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Rule:
        return cls(
            name=str(d["name"]),
            metric=str(d["metric"]),
            op=str(d["op"]),
            threshold=float(d["threshold"]),
            severity=str(d["severity"]).upper(),
            message=str(d.get("message", "")),
        )


@dataclass
class Triggered:
    rule: Rule
    value: float | None

    def describe(self) -> str:
        base = self.rule.message or self.rule.name
        return f"{base} (metric={self.rule.metric}, value={self.value}, op={self.rule.op}, threshold={self.rule.threshold}, severity={self.rule.severity})"


@dataclass
class HealthReport:
    state: str  # "PASS" | "WARN" | "HALT"
    triggered: list[Triggered] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "triggered": [
                {
                    "name": t.rule.name,
                    "metric": t.rule.metric,
                    "op": t.rule.op,
                    "threshold": t.rule.threshold,
                    "severity": t.rule.severity,
                    "value": t.value,
                    "message": t.describe(),
                }
                for t in self.triggered
            ],
            "metrics": self.metrics,
        }


def evaluate(metrics: dict[str, Any], rules: list[Rule]) -> HealthReport:
    """Evaluate ``metrics`` against ``rules`` and return the worst state."""
    triggered: list[Triggered] = []
    worst = "PASS"
    for rule in rules:
        value = metrics.get(rule.metric)
        if rule.evaluate(value if isinstance(value, (int, float)) else None):
            triggered.append(Triggered(rule=rule, value=value))
            if SEVERITY_ORDER.get(rule.severity, 0) > SEVERITY_ORDER[worst]:
                worst = rule.severity
    return HealthReport(state=worst, triggered=triggered, metrics=dict(metrics))


def transition(prev_state: str | None, new_state: str) -> str | None:
    """Return a human-readable transition label, or None if no transition.

    Examples: "PASS->WARN", "WARN->HALT", "HALT->PASS".
    """
    if prev_state == new_state:
        return None
    return f"{prev_state or 'INIT'}->{new_state}"
