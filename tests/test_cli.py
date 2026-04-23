"""Smoke-test the CLI end-to-end against the synthetic sample data."""
from __future__ import annotations

import json

from qlrk.cli import main


def test_cli_version(capsys):
    try:
        main(["--version"])
    except SystemExit as e:
        assert e.code == 0


def test_cli_reconcile_against_samples(examples_dir, tmp_state):
    out = tmp_state / "recon.json"
    rc = main([
        "reconcile",
        "--model", str(examples_dir / "sample_model_fills.csv"),
        "--broker", str(examples_dir / "sample_broker_fills.csv"),
        "--out", str(out),
    ])
    assert rc == 1  # sample data has intentional divergences
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["clean"] is False
    assert data["matched"] >= 0
    kinds = {d["kind"] for d in data["divergences"]}
    assert "qty_mismatch" in kinds
    assert "price_mismatch" in kinds


def test_cli_freeze_against_samples(examples_dir, tmp_state):
    manifest = tmp_state / "m.json"
    rc = main([
        "freeze",
        "--config", str(examples_dir / "config.example.yaml"),
        "--out", str(manifest),
        "--repo-root", str(tmp_state),  # ensures no git metadata leaks
    ])
    assert rc == 0
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert "config_hash" in data
    assert data["feature_flags"]["auto_confirm_entries"] is True


def test_cli_monitor_halts_when_rule_fires(tmp_state, examples_dir):
    bad_metrics = tmp_state / "metrics.json"
    bad_metrics.write_text(json.dumps({"max_drawdown_pct": 0.99, "fill_rate": 0.9, "order_reject_rate": 0, "reconciliation_divergences": 0}))
    out = tmp_state / "h.json"
    rc = main([
        "monitor",
        "--rules", str(examples_dir / "monitoring_rules.example.yaml"),
        "--metrics", str(bad_metrics),
        "--out", str(out),
    ])
    assert rc == 2  # HALT
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["state"] == "HALT"


def test_cli_gate_with_samples(examples_dir, tmp_state):
    out = tmp_state / "gate.json"
    rc = main([
        "gate",
        "--checklist", str(examples_dir / "promotion_gate.example.yaml"),
        "--metrics", str(examples_dir / "sample_metrics.json"),
        "--manual", str(examples_dir / "manual_overrides.example.yaml"),
        "--out", str(out),
    ])
    # With the sample metrics, reconciliation_divergences=4 > 2 → gate fails
    assert rc == 1
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["stage"] == "limited_live"


def test_cli_incident_renders(examples_dir, tmp_state):
    out = tmp_state / "i.md"
    rc = main([
        "incident",
        "--inputs", str(examples_dir / "incident_inputs.example.json"),
        "--out", str(out),
    ])
    assert rc == 0
    md = out.read_text(encoding="utf-8")
    assert md.startswith("# Incident")
    assert "Actions taken" in md


def test_cli_daily_renders(examples_dir, tmp_state):
    out = tmp_state / "d.md"
    rc = main([
        "daily",
        "--date", "2026-01-02",
        "--out", str(out),
    ])
    assert rc == 0
    assert out.read_text(encoding="utf-8").startswith("# Daily review — 2026-01-02")
