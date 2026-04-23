"""End-to-end test for `qlrk demo` against the bundled cached CSV.

We always run in ``--offline`` mode in CI so tests never depend on the
network or yfinance availability.
"""
from __future__ import annotations

import json
from pathlib import Path

from qlrk.cli import main
from qlrk.demo import (
    _cached_csv_path,
    build_trades,
    compute_metrics,
    generate_signals,
    load_bars,
    run_demo,
)


def test_cached_csv_bundled_with_repo():
    path = _cached_csv_path()
    assert path.exists()
    # Sanity: at least a few rows of real market data.
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) > 50
    assert lines[0].lower().startswith("date,open,high,low,close,volume")


def test_offline_demo_via_run_demo(tmp_path: Path):
    out = tmp_path / "demo"
    result = run_demo(state_dir=out, offline=True, repo_root=str(tmp_path))

    assert result.source == "cached"
    assert result.bars_count > 50
    # The toy strategy must emit at least one round-trip on 400 bars of AAPL.
    assert result.trades_count >= 1

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["feature_flags"]["use_sma_crossover_demo"] is True
    assert manifest["config"]["strategy"]["kind"] == "sma_crossover_toy"

    recon = json.loads(result.reconciliation_path.read_text(encoding="utf-8"))
    # We intentionally drop one broker fill so reconcile must find >=1 divergence.
    assert len(recon["divergences"]) >= 1
    kinds = {d["kind"] for d in recon["divergences"]}
    assert "missing_at_broker" in kinds

    health = json.loads(result.health_path.read_text(encoding="utf-8"))
    assert health["state"] in {"PASS", "WARN", "HALT"}

    gate = json.loads(result.gate_path.read_text(encoding="utf-8"))
    assert gate["stage"] == "demo_promotion"

    report = result.report_path.read_text(encoding="utf-8")
    assert "TOY / DEMO / EDUCATIONAL ONLY" in report
    assert "SMA" in report


def test_offline_demo_via_cli(tmp_path: Path):
    out = tmp_path / "demo_cli"
    rc = main(["demo", "--state-dir", str(out), "--offline", "--repo-root", str(tmp_path)])
    assert rc == 0
    assert (out / "demo_report.md").exists()
    assert (out / "manifest.json").exists()
    assert (out / "reconciliation.json").exists()


def test_signal_and_trade_primitives():
    bars, _src = load_bars(offline=True)
    signals = generate_signals(bars)
    # Cached CSV covers ~18 months — crossover should fire several times.
    assert len(signals) > 2
    # After generate_signals, BUYs and SELLs alternate.
    for i in range(1, len(signals)):
        assert signals[i].action != signals[i - 1].action
    trades = build_trades(signals)
    metrics = compute_metrics(trades)
    assert metrics["demo_trade_count"] == len(trades)
    assert 0.0 <= metrics["max_drawdown_pct"] <= 1.0
