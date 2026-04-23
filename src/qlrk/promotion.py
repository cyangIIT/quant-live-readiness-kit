"""Promotion gate.

A promotion gate scores a candidate stage transition (paper -> limited
live -> full live) against a YAML checklist. Each check is one of:

* ``boolean`` — must be True (e.g., "freeze manifest exists")
* ``threshold`` — a numeric metric must satisfy an operator+threshold
* ``manual`` — operator sign-off required, defaults to False

The result is a ``GateResult`` with a pass/fail summary and the list of
failed checks. The gate does *not* know which strategy you are running
or what a "good" number looks like — you provide the checklist, the
toolkit tells you which items are green.

See ``templates/promotion_gate_checklist.md`` and
``examples/promotion_gate.example.yaml`` for a starting point.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .io_utils import load_yaml


@dataclass
class CheckResult:
    name: str
    kind: str  # "boolean" | "threshold" | "manual"
    passed: bool
    detail: str


@dataclass
class GateResult:
    stage: str
    passed: bool
    checks: list[CheckResult] = field(default_factory=list)

    def failed(self) -> list[CheckResult]:
        return [c for c in self.checks if not c.passed]

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "passed": self.passed,
            "checks": [
                {
                    "name": c.name,
                    "kind": c.kind,
                    "passed": c.passed,
                    "detail": c.detail,
                }
                for c in self.checks
            ],
        }


def _eval_threshold(value: Any, op: str, threshold: float) -> bool:
    if value is None:
        return False
    try:
        v = float(value)
    except (TypeError, ValueError):
        return False
    t = float(threshold)
    return {
        "<": v < t,
        "<=": v <= t,
        ">": v > t,
        ">=": v >= t,
        "==": v == t,
        "!=": v != t,
    }[op]


def score(
    checklist: dict[str, Any] | str,
    metrics: dict[str, Any] | None = None,
    *,
    manual_overrides: dict[str, bool] | None = None,
) -> GateResult:
    """Score a checklist against current ``metrics`` and operator input.

    ``checklist`` may be either a dict (already parsed) or a path to a
    YAML file with this shape:

        stage: limited_live
        checks:
          - name: freeze_manifest_exists
            kind: boolean
            value_key: freeze_manifest_exists
          - name: max_drawdown
            kind: threshold
            metric: max_drawdown_pct
            op: "<"
            threshold: 0.05
          - name: operator_signoff
            kind: manual
    """
    if isinstance(checklist, str):
        checklist = load_yaml(checklist)
    metrics = metrics or {}
    manual_overrides = manual_overrides or {}

    stage = str(checklist.get("stage", "unspecified"))
    raw_checks = checklist.get("checks", [])
    results: list[CheckResult] = []
    for raw in raw_checks:
        name = str(raw["name"])
        kind = str(raw.get("kind", "boolean"))
        if kind == "boolean":
            key = str(raw.get("value_key", name))
            val = bool(metrics.get(key, False))
            results.append(
                CheckResult(
                    name=name,
                    kind=kind,
                    passed=val,
                    detail=f"{key}={val}",
                )
            )
        elif kind == "threshold":
            metric = str(raw["metric"])
            op = str(raw["op"])
            threshold = float(raw["threshold"])
            value = metrics.get(metric)
            ok = _eval_threshold(value, op, threshold)
            results.append(
                CheckResult(
                    name=name,
                    kind=kind,
                    passed=ok,
                    detail=f"{metric}={value} {op} {threshold}",
                )
            )
        elif kind == "manual":
            ok = bool(manual_overrides.get(name, raw.get("default", False)))
            results.append(
                CheckResult(
                    name=name,
                    kind=kind,
                    passed=ok,
                    detail=f"manual sign-off: {ok}",
                )
            )
        else:
            results.append(
                CheckResult(
                    name=name,
                    kind=kind,
                    passed=False,
                    detail=f"unknown check kind {kind!r}",
                )
            )

    passed = all(c.passed for c in results)
    return GateResult(stage=stage, passed=passed, checks=results)
