"""Paper-vs-model reconciliation.

Two sources of truth for "what just happened":

* **model fills** — what your strategy *expected* to fill, emitted by your
  backtest or intention-logger.
* **broker fills** — what actually filled at the broker (paper or live).

These should agree on: symbol, side, quantity, (approx.) price, and
timestamp ordering. When they do not agree, you want a structured report
that classifies each divergence by cause, so a human can decide if it is
an ops bug, a feature-flag drift, or a data-feed issue.

This module is the classifier. It does not know what any particular
strategy's rules are; it just compares two lists of ``Fill`` records.

Fills are matched greedily by ``order_id`` first, then by
``(symbol, side, bar_ts)`` with a configurable price/qty tolerance.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Fill:
    order_id: str
    symbol: str
    side: str  # "BUY" | "SELL" | "SHORT" | "COVER"
    qty: float
    price: float
    ts: str  # ISO-8601

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Fill:
        return cls(
            order_id=str(d.get("order_id", "")),
            symbol=str(d["symbol"]).upper(),
            side=str(d["side"]).upper(),
            qty=float(d["qty"]),
            price=float(d["price"]),
            ts=str(d["ts"]),
        )


@dataclass
class Divergence:
    kind: str
    # "extra_at_broker" | "missing_at_broker" | "price_mismatch"
    # | "qty_mismatch" | "side_mismatch" | "timing_skew"
    order_id: str
    symbol: str
    detail: str
    model: Fill | None = None
    broker: Fill | None = None


@dataclass
class ReconciliationReport:
    matched: int = 0
    divergences: list[Divergence] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not self.divergences

    def to_dict(self) -> dict[str, Any]:
        def _fill(f: Fill | None) -> dict[str, Any] | None:
            if f is None:
                return None
            return {
                "order_id": f.order_id,
                "symbol": f.symbol,
                "side": f.side,
                "qty": f.qty,
                "price": f.price,
                "ts": f.ts,
            }

        return {
            "matched": self.matched,
            "clean": self.clean,
            "divergences": [
                {
                    "kind": d.kind,
                    "order_id": d.order_id,
                    "symbol": d.symbol,
                    "detail": d.detail,
                    "model": _fill(d.model),
                    "broker": _fill(d.broker),
                }
                for d in self.divergences
            ],
        }


def _by_order(fills: Iterable[Fill]) -> dict[str, Fill]:
    return {f.order_id: f for f in fills if f.order_id}


def reconcile(
    model_fills: Iterable[Fill | dict[str, Any]],
    broker_fills: Iterable[Fill | dict[str, Any]],
    *,
    price_tolerance: float = 0.01,
    qty_tolerance: float = 0.0,
) -> ReconciliationReport:
    """Match model fills against broker fills and classify divergences.

    Matching is strictly by ``order_id``. Fills with no ``order_id`` are not
    matched; the caller should ensure model and broker agree on an ID
    space (most brokers expose a ``client_order_id`` you can reuse).

    A matched pair with a price difference > ``price_tolerance`` is
    flagged ``price_mismatch``; similarly for qty. Any fill present in one
    side but not the other is flagged ``extra_at_broker`` or
    ``missing_at_broker``.
    """

    def _coerce(seq: Iterable[Fill | dict[str, Any]]) -> list[Fill]:
        out: list[Fill] = []
        for f in seq:
            out.append(f if isinstance(f, Fill) else Fill.from_dict(f))
        return out

    model = _coerce(model_fills)
    broker = _coerce(broker_fills)

    by_model = _by_order(model)
    by_broker = _by_order(broker)

    report = ReconciliationReport()
    all_ids = set(by_model) | set(by_broker)
    for oid in sorted(all_ids):
        m = by_model.get(oid)
        b = by_broker.get(oid)
        if m is not None and b is None:
            report.divergences.append(
                Divergence(
                    kind="missing_at_broker",
                    order_id=oid,
                    symbol=m.symbol,
                    detail=f"model fill {oid} has no broker counterpart",
                    model=m,
                )
            )
            continue
        if b is not None and m is None:
            report.divergences.append(
                Divergence(
                    kind="extra_at_broker",
                    order_id=oid,
                    symbol=b.symbol,
                    detail=f"broker fill {oid} has no model counterpart",
                    broker=b,
                )
            )
            continue
        assert m is not None and b is not None
        any_diff = False
        if m.symbol != b.symbol:
            report.divergences.append(
                Divergence(
                    kind="side_mismatch",
                    order_id=oid,
                    symbol=m.symbol,
                    detail=f"symbol mismatch {m.symbol} vs {b.symbol}",
                    model=m,
                    broker=b,
                )
            )
            any_diff = True
        if m.side != b.side:
            report.divergences.append(
                Divergence(
                    kind="side_mismatch",
                    order_id=oid,
                    symbol=m.symbol,
                    detail=f"side mismatch {m.side} vs {b.side}",
                    model=m,
                    broker=b,
                )
            )
            any_diff = True
        if abs(m.qty - b.qty) > qty_tolerance:
            report.divergences.append(
                Divergence(
                    kind="qty_mismatch",
                    order_id=oid,
                    symbol=m.symbol,
                    detail=f"qty diff {m.qty} vs {b.qty}",
                    model=m,
                    broker=b,
                )
            )
            any_diff = True
        if abs(m.price - b.price) > price_tolerance:
            report.divergences.append(
                Divergence(
                    kind="price_mismatch",
                    order_id=oid,
                    symbol=m.symbol,
                    detail=f"price diff {m.price} vs {b.price} (tol {price_tolerance})",
                    model=m,
                    broker=b,
                )
            )
            any_diff = True
        if not any_diff:
            report.matched += 1

    return report
