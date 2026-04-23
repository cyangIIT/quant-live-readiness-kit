"""End-to-end public demo: yfinance + SMA-crossover toy strategy.

The demo is a self-contained illustration of how the toolkit is used
around an arbitrary strategy. It:

1. Fetches public AAPL daily bars from `yfinance` (or falls back to the
   cached CSV bundled under ``examples/sample_aapl_daily.csv``).
2. Runs a trivial SMA-crossover toy strategy to produce "model" signals.
3. Emits the two fill CSVs the toolkit's reconciliation expects
   (model-expected fills + simulated broker fills with small slippage
   and one intentional divergence).
4. Builds session metrics, a freeze manifest, runs the monitor/gate,
   and renders a daily-review Markdown report.

IMPORTANT LABELING:

* The AAPL price series is **real public market data** — either fetched
  live from yfinance, or the bundled snapshot (see
  ``examples/sample_aapl_daily.csv``). It is NOT fabricated.
* The SMA-crossover strategy is a **toy, demo-only, educational
  example**. It is NOT a validated strategy, NOT alpha, NOT investment
  advice, and NOT production-ready.
* The simulated broker fills (slippage, intentional divergence) are
  **synthetic** — they exist to show the reconciliation engine doing
  something interesting. They are clearly marked as such in the
  generated ``broker_fills.csv`` header comment.

Nothing in this module represents the inner workings of any real
strategy.
"""
from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .alerting import Alert, AlertRouter, ConsoleAdapter, FileAdapter
from .contamination import detect as detect_contamination
from .freeze import Manifest, build_manifest, write_manifest
from .io_utils import atomic_write_json
from .monitoring import Rule, evaluate
from .promotion import score as score_gate
from .reconciliation import Fill, reconcile
from .reporting import render_daily_review, render_incident

log = logging.getLogger(__name__)


DEMO_TICKER = "AAPL"
DEMO_FAST = 10
DEMO_SLOW = 30
DEMO_QTY = 10
DEMO_SLIPPAGE = 0.03


@dataclass
class Bar:
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


def _cached_csv_path() -> Path:
    """Locate the bundled public market-data snapshot.

    Searched in this order:

    1. ``<repo>/examples/sample_aapl_daily.csv`` (when running from a
       source checkout — typical dev + first-run path).
    2. Package-relative fallback (only exists when the CSV is shipped
       inside the installed wheel; not currently done).
    """
    here = Path(__file__).resolve()
    for candidate in (
        here.parents[2] / "examples" / "sample_aapl_daily.csv",
        here.parent / "_data" / "sample_aapl_daily.csv",
    ):
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "bundled cached AAPL CSV not found. Expected at "
        "examples/sample_aapl_daily.csv relative to the repo root."
    )


def _fetch_bars_yfinance(ticker: str, period: str = "400d") -> list[Bar]:
    import yfinance as yf  # local import keeps yfinance optional

    df = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=True)
    if df is None or len(df) == 0:
        raise RuntimeError("yfinance returned no rows")
    # Flatten multi-index columns if present
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    bars: list[Bar] = []
    for ts, row in df.iterrows():
        bars.append(
            Bar(
                date=ts.strftime("%Y-%m-%d"),
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=float(row["Volume"]),
            )
        )
    return bars


def _load_bars_csv(path: Path) -> list[Bar]:
    bars: list[Bar] = []
    with path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            bars.append(
                Bar(
                    date=row["date"],
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                )
            )
    return bars


def load_bars(
    *,
    ticker: str = DEMO_TICKER,
    period: str = "400d",
    offline: bool = False,
) -> tuple[list[Bar], str]:
    """Return (bars, source) where source is ``"yfinance"`` or ``"cached"``."""
    if not offline:
        try:
            bars = _fetch_bars_yfinance(ticker, period)
            if len(bars) >= DEMO_SLOW + 5:
                return bars, "yfinance"
            log.warning("yfinance returned too few rows (%d); using cached CSV", len(bars))
        except Exception as exc:  # yfinance import, network, throttling, etc.
            log.warning("yfinance fetch failed (%s); using cached CSV", exc)
    cached = _cached_csv_path()
    return _load_bars_csv(cached), "cached"


def _sma(values: list[float], window: int) -> list[float | None]:
    out: list[float | None] = []
    running = 0.0
    for i, v in enumerate(values):
        running += v
        if i >= window:
            running -= values[i - window]
        out.append(running / window if i >= window - 1 else None)
    return out


@dataclass
class Signal:
    date: str
    action: str  # "BUY" | "SELL"
    price: float
    reason: str


def generate_signals(bars: list[Bar], *, fast: int = DEMO_FAST, slow: int = DEMO_SLOW) -> list[Signal]:
    """Classic SMA crossover. Toy only — flat position, one open at a time.

    Rules:

    * fast crosses above slow → BUY at bar close (enter long)
    * fast crosses below slow → SELL at bar close (exit long)

    Only emit BUYs when flat and SELLs when long — so every BUY has
    exactly one matching SELL downstream.
    """
    closes = [b.close for b in bars]
    fast_sma = _sma(closes, fast)
    slow_sma = _sma(closes, slow)

    signals: list[Signal] = []
    long_open = False
    for i in range(1, len(bars)):
        f1, s1 = fast_sma[i - 1], slow_sma[i - 1]
        f2, s2 = fast_sma[i], slow_sma[i]
        if f1 is None or s1 is None or f2 is None or s2 is None:
            continue
        crossed_up = f1 <= s1 and f2 > s2
        crossed_down = f1 >= s1 and f2 < s2
        if crossed_up and not long_open:
            signals.append(
                Signal(
                    date=bars[i].date,
                    action="BUY",
                    price=round(bars[i].close, 4),
                    reason=f"SMA({fast}) crossed above SMA({slow})",
                )
            )
            long_open = True
        elif crossed_down and long_open:
            signals.append(
                Signal(
                    date=bars[i].date,
                    action="SELL",
                    price=round(bars[i].close, 4),
                    reason=f"SMA({fast}) crossed below SMA({slow})",
                )
            )
            long_open = False
    return signals


@dataclass
class DemoTrade:
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    qty: int
    pnl: float


def build_trades(signals: list[Signal], qty: int = DEMO_QTY) -> list[DemoTrade]:
    trades: list[DemoTrade] = []
    pending: Signal | None = None
    for s in signals:
        if s.action == "BUY":
            pending = s
        elif s.action == "SELL" and pending is not None:
            trades.append(
                DemoTrade(
                    entry_date=pending.date,
                    exit_date=s.date,
                    entry_price=pending.price,
                    exit_price=s.price,
                    qty=qty,
                    pnl=round((s.price - pending.price) * qty, 2),
                )
            )
            pending = None
    return trades


def _build_model_fills(signals: list[Signal], qty: int) -> list[dict[str, Any]]:
    out = []
    for i, s in enumerate(signals, start=1):
        out.append(
            {
                "order_id": f"demo-{i:04d}",
                "symbol": DEMO_TICKER,
                "side": s.action,
                "qty": qty,
                "price": f"{s.price:.4f}",
                "ts": f"{s.date}T15:00:00+00:00",
            }
        )
    return out


def _build_broker_fills(model_fills: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Simulate a realistic broker CSV with small slippage and ONE intentional drop.

    The divergence is deliberate so the reconciliation step has something
    to classify — this is clearly synthetic and is marked as such in the
    output CSV header comment.
    """
    broker: list[dict[str, Any]] = []
    for i, m in enumerate(model_fills):
        # Intentionally drop the last fill — demonstrates "missing_at_broker".
        if i == len(model_fills) - 1 and len(model_fills) >= 3:
            continue
        # Small slippage: BUYs fill at model+0.03, SELLs at model-0.03.
        price = float(m["price"])
        slip = DEMO_SLIPPAGE if m["side"] == "BUY" else -DEMO_SLIPPAGE
        broker_price = round(price + slip, 4)
        # Timestamp a few seconds later, as real broker acks typically are.
        ts = m["ts"].replace("T15:00:00", "T15:00:04")
        broker.append(
            {
                "order_id": m["order_id"],
                "symbol": m["symbol"],
                "side": m["side"],
                "qty": m["qty"],
                "price": f"{broker_price:.4f}",
                "ts": ts,
            }
        )
    return broker


def _write_csv(path: Path, rows: list[dict[str, Any]], header_comment: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        if header_comment:
            fh.write(header_comment.rstrip("\n") + "\n")
        if not rows:
            return
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


DEMO_STARTING_CAPITAL = 10_000.0


def compute_metrics(trades: list[DemoTrade]) -> dict[str, Any]:
    """Trivial stats for the demo. Not a strategy evaluation.

    Drawdown is computed against a nominal starting capital
    (``DEMO_STARTING_CAPITAL``) so the number stays in a realistic
    percentage range when equity dips near zero.
    """
    if not trades:
        return {
            "demo_trade_count": 0,
            "demo_win_rate": 0.0,
            "demo_total_pnl": 0.0,
            "max_drawdown_pct": 0.0,
        }
    pnls = [t.pnl for t in trades]
    equity = DEMO_STARTING_CAPITAL
    peak = equity
    max_dd = 0.0
    for p in pnls:
        equity += p
        peak = max(peak, equity)
        dd = (peak - equity) / peak if peak > 0 else 0.0
        max_dd = max(max_dd, dd)
    wins = sum(1 for p in pnls if p > 0)
    return {
        "demo_trade_count": len(trades),
        "demo_win_rate": round(wins / len(trades), 4),
        "demo_total_pnl": round(sum(pnls), 2),
        "max_drawdown_pct": round(max_dd, 4),
    }


# --- demo orchestration ------------------------------------------------------


@dataclass
class DemoResult:
    source: str  # "yfinance" | "cached"
    bars_count: int
    signals_count: int
    trades_count: int
    manifest_path: Path
    reconciliation_path: Path
    health_path: Path
    gate_path: Path
    report_path: Path


def run_demo(
    state_dir: str | Path = ".qlrk_state/demo",
    *,
    ticker: str = DEMO_TICKER,
    offline: bool = False,
    repo_root: str | Path = ".",
) -> DemoResult:
    """Run the end-to-end public demo.

    Produces one folder of artifacts and a single Markdown report
    summarising what the toolkit did.
    """
    out = Path(state_dir)
    out.mkdir(parents=True, exist_ok=True)

    bars, source = load_bars(ticker=ticker, offline=offline)
    signals = generate_signals(bars)
    trades = build_trades(signals)
    metrics = compute_metrics(trades)

    # Reconciliation needs closed round-trip pairs — if the last signal is
    # a BUY with no matching SELL, drop it so the model-fill set is clean.
    effective_signals = list(signals)
    if effective_signals and effective_signals[-1].action == "BUY":
        effective_signals = effective_signals[:-1]

    model_fills = _build_model_fills(effective_signals, DEMO_QTY)
    broker_fills = _build_broker_fills(model_fills)

    bars_path = out / "bars.csv"
    signals_path = out / "signals.csv"
    model_fills_path = out / "model_fills.csv"
    broker_fills_path = out / "broker_fills.csv"
    metrics_path = out / "metrics.json"
    config_path = out / "config.yaml"
    manifest_path = out / "manifest.json"
    contamination_path = out / "contamination.json"
    recon_path = out / "reconciliation.json"
    health_path = out / "health.json"
    gate_path = out / "gate.json"
    alerts_path = out / "alerts.jsonl"
    alert_state_path = out / "alert_state.json"
    report_path = out / "demo_report.md"

    _write_csv(
        bars_path,
        [
            {
                "date": b.date,
                "open": f"{b.open:.4f}",
                "high": f"{b.high:.4f}",
                "low": f"{b.low:.4f}",
                "close": f"{b.close:.4f}",
                "volume": int(b.volume),
            }
            for b in bars
        ],
    )
    _write_csv(
        signals_path,
        [
            {"date": s.date, "action": s.action, "price": f"{s.price:.4f}", "reason": s.reason}
            for s in signals
        ],
    )
    _write_csv(
        model_fills_path,
        model_fills,
        header_comment=(
            "# Toy SMA-crossover model fills — TOY / DEMO / EDUCATIONAL ONLY. "
            "Not a validated strategy."
        ),
    )
    _write_csv(
        broker_fills_path,
        broker_fills,
        header_comment=(
            "# Simulated broker fills — SYNTHETIC for demo purposes. "
            "Small slippage is applied and one intentional 'missing_at_broker' "
            "divergence is introduced so the reconciliation engine has "
            "something to report."
        ),
    )
    atomic_write_json(metrics_path, {**metrics, "fill_rate": 0.95, "order_reject_rate": 0.0})

    gate_metrics = {
        **metrics,
        "fill_rate": 0.95,
        "order_reject_rate": 0.0,
        "reconciliation_divergences": 0,  # updated after reconcile
        "freeze_manifest_exists": True,
        "contamination_admissible": True,
        "paper_trade_count": len(trades),
        "paper_days_elapsed": max(1, _span_days(bars)),
    }

    config = {
        "universe": [ticker],
        "strategy": {
            "kind": "sma_crossover_toy",
            "fast": DEMO_FAST,
            "slow": DEMO_SLOW,
            "qty": DEMO_QTY,
        },
        "execution": {"slippage_per_share": DEMO_SLIPPAGE},
        "data_source": source,
        "note": "TOY / DEMO / EDUCATIONAL ONLY. Not a validated strategy.",
        "feature_flags": {
            "auto_confirm_entries": True,
            "use_sma_crossover_demo": True,
        },
    }
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(config, fh, sort_keys=True)

    # 1) Freeze manifest
    feature_flags = config.pop("feature_flags")
    manifest = build_manifest(
        config=config,
        feature_flags=feature_flags,
        repo_root=repo_root,
        notes="quant-live-readiness-kit public demo (SMA-crossover toy on AAPL)",
    )
    write_manifest(manifest, manifest_path)

    # 2) Contamination — diff against itself so the demo is always admissible.
    #    In real use, you'd diff against a committed clean baseline.
    clean = _self_baseline(manifest)
    cont = detect_contamination(manifest, clean)
    atomic_write_json(contamination_path, cont.to_dict())

    # 3) Reconciliation
    model_fill_objs = [Fill.from_dict(m) for m in model_fills]
    broker_fill_objs = [Fill.from_dict(b) for b in broker_fills]
    # Tolerance > DEMO_SLIPPAGE so small routine slippage doesn't swamp the
    # report; the one intentional dropped broker fill remains.
    recon_report = reconcile(model_fill_objs, broker_fill_objs, price_tolerance=0.05)
    atomic_write_json(recon_path, recon_report.to_dict())
    gate_metrics["reconciliation_divergences"] = len(recon_report.divergences)

    # 4) Monitor
    rules = [
        Rule(
            name="drawdown_warn",
            metric="max_drawdown_pct",
            op=">",
            threshold=0.25,
            severity="WARN",
            message="demo toy strategy drawdown above soft threshold",
        ),
        Rule(
            name="drawdown_halt",
            metric="max_drawdown_pct",
            op=">",
            threshold=0.60,
            severity="HALT",
            message="demo toy strategy drawdown above hard threshold",
        ),
        Rule(
            name="fill_rate_warn",
            metric="fill_rate",
            op="<",
            threshold=0.7,
            severity="WARN",
            message="fill rate below soft warning",
        ),
        Rule(
            name="reconciliation_divergence_warn",
            metric="reconciliation_divergences",
            op=">",
            threshold=0,
            severity="WARN",
            message="paper/broker divergences detected — review reconciliation.json",
        ),
    ]
    health = evaluate(gate_metrics, rules)
    atomic_write_json(health_path, health.to_dict())

    router = AlertRouter(adapters=[ConsoleAdapter(), FileAdapter(alerts_path)], state_path=alert_state_path)
    if health.state != "PASS":
        router.emit(
            Alert(
                severity=health.state,
                title="demo monitoring transition",
                message="; ".join(t.describe() for t in health.triggered),
            )
        )
    else:
        router.emit(Alert(severity="CLEAR", title="demo monitoring clear", message="all rules pass"))

    # 5) Promotion gate — demo checklist, deliberately loose so the
    #    demo shows a real gate evaluation even on a tiny dataset.
    demo_checklist = {
        "stage": "demo_promotion",
        "checks": [
            {"name": "freeze_manifest_exists", "kind": "boolean", "value_key": "freeze_manifest_exists"},
            {"name": "contamination_clean", "kind": "boolean", "value_key": "contamination_admissible"},
            {
                "name": "reconciliation_within_tolerance",
                "kind": "threshold",
                "metric": "reconciliation_divergences",
                "op": "<=",
                "threshold": 5,
            },
            {
                "name": "fill_rate_acceptable",
                "kind": "threshold",
                "metric": "fill_rate",
                "op": ">=",
                "threshold": 0.5,
            },
        ],
    }
    gate_result = score_gate(demo_checklist, gate_metrics)
    atomic_write_json(gate_path, gate_result.to_dict())

    # 6) Daily review
    review_md = render_daily_review(
        date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        manifest=manifest.to_dict(),
        contamination=cont.to_dict(),
        reconciliation=recon_report.to_dict(),
        health=health.to_dict(),
        notes=(
            "This is the public demo. The SMA-crossover strategy is TOY / "
            "DEMO / EDUCATIONAL ONLY and does not represent any production "
            "strategy."
        ),
    )
    # Optional incident narrative if divergences exist.
    incident_md = ""
    if recon_report.divergences:
        incident_md = render_incident(
            title="Demo reconciliation divergences",
            detected_at=datetime.now(timezone.utc).isoformat(),
            severity=health.state,
            summary=(
                "The demo pipeline intentionally drops one broker fill and "
                "applies small slippage so the toolkit's reconciliation "
                "engine has real divergences to classify. All divergences "
                "here are synthetic."
            ),
            health=health.to_dict(),
            reconciliation=recon_report.to_dict(),
            contamination=cont.to_dict(),
            actions_taken=[
                "Classified divergences via qlrk reconcile",
                "Raised monitoring alert via qlrk monitor",
                "Rendered this post-mortem via qlrk incident",
            ],
            followups=[
                "Replace sample data with your own model/broker fills",
                "Commit a real clean-baseline manifest",
                "Add production-realistic monitoring thresholds",
            ],
            authored_by="qlrk demo",
        )

    report = _render_demo_report(
        ticker=ticker,
        source=source,
        bars=bars,
        signals=signals,
        trades=trades,
        metrics=metrics,
        gate_metrics=gate_metrics,
        manifest=manifest,
        contamination=cont.to_dict(),
        reconciliation=recon_report.to_dict(),
        health=health.to_dict(),
        gate=gate_result.to_dict(),
        artifacts=out,
        daily_review=review_md,
        incident=incident_md,
    )
    report_path.write_text(report, encoding="utf-8")

    return DemoResult(
        source=source,
        bars_count=len(bars),
        signals_count=len(signals),
        trades_count=len(trades),
        manifest_path=manifest_path,
        reconciliation_path=recon_path,
        health_path=health_path,
        gate_path=gate_path,
        report_path=report_path,
    )


def _self_baseline(manifest: Manifest) -> Manifest:
    """Produce a Manifest identical to ``manifest`` for a no-drift demo.

    In real operation the baseline is a committed JSON from an earlier
    clean session; for the demo we construct one in memory so the
    contamination step has something admissible to compare against.
    """
    return Manifest(
        generated_at=manifest.generated_at,
        config=dict(manifest.config),
        feature_flags=dict(manifest.feature_flags),
        git_sha=manifest.git_sha,
        git_dirty=manifest.git_dirty,
        dirty_files=list(manifest.dirty_files),
        python_version=manifest.python_version,
        config_hash=manifest.config_hash,
        notes="demo-synthetic clean baseline",
    )


def _span_days(bars: list[Bar]) -> int:
    if len(bars) < 2:
        return 0
    try:
        a = datetime.fromisoformat(bars[0].date)
        b = datetime.fromisoformat(bars[-1].date)
        return (b - a).days
    except ValueError:
        return 0


def _render_demo_report(
    *,
    ticker: str,
    source: str,
    bars: list[Bar],
    signals: list[Signal],
    trades: list[DemoTrade],
    metrics: dict[str, Any],
    gate_metrics: dict[str, Any],
    manifest: Manifest,
    contamination: dict[str, Any],
    reconciliation: dict[str, Any],
    health: dict[str, Any],
    gate: dict[str, Any],
    artifacts: Path,
    daily_review: str,
    incident: str,
) -> str:
    lines: list[str] = []
    lines.append(f"# qlrk demo report — {ticker}")
    lines.append("")
    lines.append(
        "> **TOY / DEMO / EDUCATIONAL ONLY.** The SMA-crossover strategy below "
        "is illustrative, not a validated trading strategy. Price data is real "
        "public AAPL daily bars; all broker-fill divergences are synthetic."
    )
    lines.append("")
    lines.append("## Inputs")
    lines.append("")
    lines.append(f"- ticker: `{ticker}`")
    lines.append(f"- data source: **{source}** ({len(bars)} bars, {bars[0].date} → {bars[-1].date})")
    lines.append(f"- toy strategy: SMA({DEMO_FAST}) × SMA({DEMO_SLOW}) crossover")
    lines.append("")
    lines.append("## Toy strategy output")
    lines.append("")
    lines.append(f"- signals generated: {len(signals)}")
    lines.append(f"- round-trip trades: {len(trades)}")
    lines.append(f"- total toy P&L: `${metrics['demo_total_pnl']}`")
    lines.append(f"- toy win rate: {metrics['demo_win_rate']}")
    lines.append(f"- toy max drawdown (pct of peak equity): {metrics['max_drawdown_pct']}")
    lines.append("")
    if trades:
        lines.append("### First few trades")
        lines.append("")
        lines.append("| entry | exit | entry px | exit px | qty | pnl |")
        lines.append("|---|---|---|---|---|---|")
        for t in trades[:8]:
            lines.append(
                f"| {t.entry_date} | {t.exit_date} | {t.entry_price} | {t.exit_price} | {t.qty} | {t.pnl} |"
            )
        lines.append("")
    lines.append("## Toolkit pipeline")
    lines.append("")
    lines.append(
        "The toy signals above were passed through the toolkit. Here is what "
        "each stage produced — each step is a real artifact on disk."
    )
    lines.append("")
    lines.append(f"- **freeze**: `{manifest.config_hash[:12]}…` → [manifest.json]({artifacts / 'manifest.json'})")
    lines.append(
        f"- **contamination**: admissible = `{contamination.get('admissible')}` "
        f"→ [contamination.json]({artifacts / 'contamination.json'})"
    )
    lines.append(
        f"- **reconcile**: matched = `{reconciliation.get('matched')}`, "
        f"divergences = `{len(reconciliation.get('divergences') or [])}` "
        f"→ [reconciliation.json]({artifacts / 'reconciliation.json'})"
    )
    lines.append(
        f"- **monitor**: state = `{health.get('state')}` "
        f"→ [health.json]({artifacts / 'health.json'})"
    )
    lines.append(
        f"- **gate**: passed = `{gate.get('passed')}` (stage=`{gate.get('stage')}`) "
        f"→ [gate.json]({artifacts / 'gate.json'})"
    )
    lines.append("")
    if reconciliation.get("divergences"):
        lines.append("### Reconciliation divergences classified")
        lines.append("")
        for d in reconciliation["divergences"]:
            lines.append(f"- `{d.get('kind')}` {d.get('symbol')} — {d.get('detail')}")
        lines.append("")
        lines.append(
            f"_These divergences are synthetic — the demo deliberately drops "
            f"the last broker fill and applies a ${DEMO_SLIPPAGE:.2f}/share "
            f"slippage so the reconciliation engine has something to report._"
        )
        lines.append("")
    if health.get("triggered"):
        lines.append("### Monitoring alerts")
        lines.append("")
        for t in health["triggered"]:
            lines.append(f"- **{t.get('severity')}** `{t.get('name')}` — {t.get('message')}")
        lines.append("")
    lines.append("## Gate breakdown")
    lines.append("")
    for c in gate.get("checks", []):
        mark = "PASS" if c.get("passed") else "FAIL"
        lines.append(f"- `{mark}` {c.get('name')} — {c.get('detail')}")
    lines.append("")
    lines.append("## Daily review (auto-rendered)")
    lines.append("")
    lines.append(daily_review.strip())
    lines.append("")
    if incident:
        lines.append("## Incident post-mortem (auto-rendered)")
        lines.append("")
        lines.append(incident.strip())
        lines.append("")
    lines.append("## Where to go next")
    lines.append("")
    lines.append("- Replace the toy SMA signals with your own model fills.")
    lines.append("- Commit a real clean-baseline manifest and diff every session.")
    lines.append("- Tune `templates/monitoring_thresholds.yaml` for your strategy.")
    lines.append("- See `docs/adapting_to_your_strategy.md` for a step-by-step guide.")
    lines.append("")
    return "\n".join(lines)


# --- CLI glue ---------------------------------------------------------------


def add_cli_parser(subparsers) -> None:  # type: ignore[no-untyped-def]
    p = subparsers.add_parser(
        "demo",
        help="run the end-to-end public demo (yfinance AAPL + SMA-crossover toy)",
        description=(
            "End-to-end public demo. Fetches AAPL daily bars (yfinance, "
            "falls back to a bundled cached CSV), runs a toy SMA-crossover, "
            "and pipes the result through freeze / reconcile / monitor / "
            "gate / daily-review. The strategy is TOY / DEMO / EDUCATIONAL "
            "ONLY — not alpha, not production."
        ),
    )
    p.add_argument("--ticker", default=DEMO_TICKER)
    p.add_argument("--state-dir", default=".qlrk_state/demo")
    p.add_argument(
        "--offline",
        action="store_true",
        help="skip yfinance and use the bundled cached public-market CSV",
    )
    p.add_argument("--repo-root", default=".", help="git root (for manifest)")
    p.set_defaults(func=_cmd_demo)


def _cmd_demo(args) -> int:  # type: ignore[no-untyped-def]
    try:
        result = run_demo(
            state_dir=args.state_dir,
            ticker=args.ticker,
            offline=args.offline,
            repo_root=args.repo_root,
        )
    except FileNotFoundError as exc:
        print(f"[demo] {exc}")
        print("[demo] (Re)run from the repo root, or ensure examples/sample_aapl_daily.csv exists.")
        return 2

    def _rel(p: Path) -> str:
        try:
            return str(p.relative_to(Path.cwd()))
        except ValueError:
            return str(p)

    print("== qlrk demo ==")
    print(f"  data source     : {result.source}")
    print(f"  bars            : {result.bars_count}")
    print(f"  toy signals     : {result.signals_count}")
    print(f"  toy trades      : {result.trades_count}")
    print(f"  manifest        : {_rel(result.manifest_path)}")
    print(f"  reconciliation  : {_rel(result.reconciliation_path)}")
    print(f"  health          : {_rel(result.health_path)}")
    print(f"  gate            : {_rel(result.gate_path)}")
    print(f"  REPORT          : {_rel(result.report_path)}")
    print()
    print("Open the REPORT file above to see what the toolkit produced.")
    print("All strategy content is TOY / DEMO / EDUCATIONAL ONLY.")
    return 0
