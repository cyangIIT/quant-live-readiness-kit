"""``qlrk`` CLI entry point.

Subcommands:

* ``demo``        — end-to-end public demo (yfinance AAPL + SMA-crossover toy).
* ``freeze``      — build a manifest from a config file and write it to disk.
* ``reconcile``   — diff model fills against broker fills (CSV in, JSON/MD out).
* ``monitor``     — evaluate metrics against a rules file and print health.
* ``gate``        — score a promotion-gate YAML against current metrics.
* ``incident``    — render a Markdown incident post-mortem from JSON inputs.
* ``daily``       — render a Markdown end-of-session review.

The CLI is thin — every subcommand is a pure function on the underlying
module; the CLI just handles argument parsing and I/O.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .alerting import Alert, AlertRouter, ConsoleAdapter, FileAdapter
from .contamination import detect as detect_contamination
from .demo import add_cli_parser as _add_demo_parser
from .freeze import build_manifest, read_manifest, write_manifest
from .io_utils import load_json, load_yaml
from .monitoring import Rule, evaluate
from .promotion import score as score_gate
from .reconciliation import Fill, reconcile
from .reporting import render_daily_review, render_incident


def _read_csv_fills(path: str | Path) -> list[Fill]:
    out: list[Fill] = []
    with Path(path).open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            out.append(Fill.from_dict(row))
    return out


def _dump_json(obj: Any, path: str | None) -> None:
    text = json.dumps(obj, indent=2, sort_keys=True, default=str)
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


# --- freeze ------------------------------------------------------------------


def _cmd_freeze(args: argparse.Namespace) -> int:
    config_path = args.config
    cfg = load_yaml(config_path) if config_path.endswith((".yml", ".yaml")) else load_json(config_path)
    feature_flags = cfg.pop("feature_flags", {}) if isinstance(cfg, dict) else {}
    manifest = build_manifest(
        config=cfg,
        feature_flags=feature_flags,
        repo_root=args.repo_root,
        notes=args.notes or "",
    )
    out = Path(args.out)
    write_manifest(manifest, out)
    print(f"wrote manifest to {out}")
    if args.contaminated_against:
        clean = read_manifest(args.contaminated_against)
        if clean is None:
            print(f"[warn] clean baseline not found: {args.contaminated_against}", file=sys.stderr)
            return 0
        report = detect_contamination(manifest, clean)
        _dump_json(report.to_dict(), args.contamination_out)
        if not report.admissible:
            return 2
    return 0


# --- reconcile ---------------------------------------------------------------


def _cmd_reconcile(args: argparse.Namespace) -> int:
    model = _read_csv_fills(args.model)
    broker = _read_csv_fills(args.broker)
    report = reconcile(
        model,
        broker,
        price_tolerance=args.price_tolerance,
        qty_tolerance=args.qty_tolerance,
    )
    _dump_json(report.to_dict(), args.out)
    return 0 if report.clean else 1


# --- monitor -----------------------------------------------------------------


def _cmd_monitor(args: argparse.Namespace) -> int:
    rules_raw = load_yaml(args.rules).get("rules", [])
    rules = [Rule.from_dict(r) for r in rules_raw]
    metrics = load_json(args.metrics)
    health = evaluate(metrics, rules)
    _dump_json(health.to_dict(), args.out)

    if args.alert_file:
        router = AlertRouter(
            adapters=[ConsoleAdapter(), FileAdapter(args.alert_file)],
            state_path=args.alert_state,
        )
        if health.state != "PASS":
            router.emit(
                Alert(
                    severity=health.state,
                    title="monitoring transition",
                    message="; ".join(t.describe() for t in health.triggered),
                )
            )
        else:
            router.emit(
                Alert(
                    severity="CLEAR",
                    title="monitoring clear",
                    message="all rules pass",
                )
            )

    if health.state == "HALT":
        return 2
    if health.state == "WARN":
        return 1
    return 0


# --- gate --------------------------------------------------------------------


def _cmd_gate(args: argparse.Namespace) -> int:
    metrics = load_json(args.metrics)
    manual_overrides = {}
    if args.manual:
        manual_overrides = load_yaml(args.manual).get("manual", {})
    result = score_gate(args.checklist, metrics, manual_overrides=manual_overrides)
    _dump_json(result.to_dict(), args.out)
    return 0 if result.passed else 1


# --- incident ----------------------------------------------------------------


def _cmd_incident(args: argparse.Namespace) -> int:
    inputs = load_json(args.inputs)
    md = render_incident(
        title=inputs.get("title", "Untitled incident"),
        detected_at=inputs.get("detected_at", ""),
        severity=inputs.get("severity", "WARN"),
        summary=inputs.get("summary", ""),
        health=inputs.get("health"),
        reconciliation=inputs.get("reconciliation"),
        contamination=inputs.get("contamination"),
        actions_taken=inputs.get("actions_taken"),
        followups=inputs.get("followups"),
        authored_by=inputs.get("authored_by", "unknown"),
    )
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(md, encoding="utf-8")
    else:
        print(md)
    return 0


# --- daily -------------------------------------------------------------------


def _cmd_daily(args: argparse.Namespace) -> int:
    manifest = load_json(args.manifest) if args.manifest else None
    contamination = load_json(args.contamination) if args.contamination else None
    reconciliation = load_json(args.reconciliation) if args.reconciliation else None
    health = load_json(args.health) if args.health else None
    md = render_daily_review(
        date=args.date,
        manifest=manifest,
        contamination=contamination,
        reconciliation=reconciliation,
        health=health,
        notes=args.notes or "",
    )
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(md, encoding="utf-8")
    else:
        print(md)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="qlrk",
        description="Operational toolkit for research-to-live readiness.",
    )
    p.add_argument("--version", action="version", version=f"qlrk {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("freeze", help="emit a freeze manifest")
    f.add_argument("--config", required=True, help="path to config YAML/JSON")
    f.add_argument("--out", required=True, help="manifest output path (.json)")
    f.add_argument("--repo-root", default=".", help="git repo root (default: cwd)")
    f.add_argument("--notes", default="", help="free-form notes")
    f.add_argument("--contaminated-against", default=None, help="clean baseline manifest to diff against")
    f.add_argument("--contamination-out", default=None, help="write contamination report here (default: stdout)")
    f.set_defaults(func=_cmd_freeze)

    r = sub.add_parser("reconcile", help="diff model vs broker fills")
    r.add_argument("--model", required=True, help="model fills CSV")
    r.add_argument("--broker", required=True, help="broker fills CSV")
    r.add_argument("--out", default=None, help="write report JSON here (default stdout)")
    r.add_argument("--price-tolerance", type=float, default=0.01)
    r.add_argument("--qty-tolerance", type=float, default=0.0)
    r.set_defaults(func=_cmd_reconcile)

    m = sub.add_parser("monitor", help="evaluate metrics against rules")
    m.add_argument("--rules", required=True, help="rules YAML")
    m.add_argument("--metrics", required=True, help="metrics JSON")
    m.add_argument("--out", default=None, help="health report JSON output")
    m.add_argument("--alert-file", default=None, help="also emit alerts to this JSONL file")
    m.add_argument("--alert-state", default=None, help="alert state file (for transition-only firing)")
    m.set_defaults(func=_cmd_monitor)

    g = sub.add_parser("gate", help="score a promotion-gate checklist")
    g.add_argument("--checklist", required=True, help="checklist YAML")
    g.add_argument("--metrics", required=True, help="metrics JSON")
    g.add_argument("--manual", default=None, help="manual overrides YAML")
    g.add_argument("--out", default=None, help="gate result JSON output")
    g.set_defaults(func=_cmd_gate)

    i = sub.add_parser("incident", help="render a Markdown incident post-mortem")
    i.add_argument("--inputs", required=True, help="incident inputs JSON")
    i.add_argument("--out", default=None, help="write .md here (default stdout)")
    i.set_defaults(func=_cmd_incident)

    _add_demo_parser(sub)

    d = sub.add_parser("daily", help="render a Markdown end-of-session review")
    d.add_argument("--date", required=True)
    d.add_argument("--manifest", default=None)
    d.add_argument("--contamination", default=None)
    d.add_argument("--reconciliation", default=None)
    d.add_argument("--health", default=None)
    d.add_argument("--notes", default="")
    d.add_argument("--out", default=None)
    d.set_defaults(func=_cmd_daily)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
