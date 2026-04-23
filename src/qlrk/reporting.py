"""Render Markdown incident and daily-review reports.

These renderers take structured dicts (the output of ``to_dict()`` on
the other module types, or free-form metadata) and produce Markdown a
human operator can read in five minutes. Markdown is preferred over
HTML because it commits cleanly in ``incidents/`` folders and reviews
well in pull requests.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def render_incident(
    *,
    title: str,
    detected_at: str,
    severity: str,
    summary: str,
    health: dict[str, Any] | None = None,
    reconciliation: dict[str, Any] | None = None,
    contamination: dict[str, Any] | None = None,
    actions_taken: list[str] | None = None,
    followups: list[str] | None = None,
    authored_by: str = "unknown",
) -> str:
    """Render a Markdown incident post-mortem."""
    parts: list[str] = []
    parts.append(f"# Incident — {title}")
    parts.append("")
    parts.append(f"- **Detected at**: {detected_at}")
    parts.append(f"- **Severity**: {severity}")
    parts.append(f"- **Authored by**: {authored_by}")
    parts.append(f"- **Report generated at**: {_ts()}")
    parts.append("")
    parts.append("## Summary")
    parts.append("")
    parts.append(summary.strip() or "_(fill in)_")
    parts.append("")

    if health:
        parts.append("## Health at detection")
        parts.append("")
        parts.append(f"- **state**: {health.get('state')}")
        triggered = health.get("triggered") or []
        if triggered:
            parts.append("- **triggered rules**:")
            for t in triggered:
                parts.append(f"  - `{t.get('name')}` — {t.get('message')}")
        else:
            parts.append("- no rules triggered")
        parts.append("")

    if contamination:
        parts.append("## Contamination findings")
        parts.append("")
        findings = contamination.get("findings") or []
        if not findings:
            parts.append("- none")
        for f in findings:
            parts.append(
                f"- **{f.get('severity', '').upper()}** `{f.get('kind')}.{f.get('key')}` — {f.get('message')}"
            )
        parts.append("")

    if reconciliation:
        parts.append("## Reconciliation")
        parts.append("")
        parts.append(f"- **matched**: {reconciliation.get('matched')}")
        divergences = reconciliation.get("divergences") or []
        parts.append(f"- **divergences**: {len(divergences)}")
        for d in divergences[:20]:
            parts.append(
                f"  - `{d.get('kind')}` {d.get('symbol')} — {d.get('detail')}"
            )
        if len(divergences) > 20:
            parts.append(f"  - _(+{len(divergences) - 20} more omitted)_")
        parts.append("")

    parts.append("## Actions taken")
    parts.append("")
    for a in actions_taken or []:
        parts.append(f"- {a}")
    if not actions_taken:
        parts.append("- _(fill in)_")
    parts.append("")

    parts.append("## Follow-ups")
    parts.append("")
    for f in followups or []:
        parts.append(f"- [ ] {f}")
    if not followups:
        parts.append("- [ ] _(fill in)_")
    parts.append("")

    return "\n".join(parts)


def render_daily_review(
    *,
    date: str,
    manifest: dict[str, Any] | None,
    contamination: dict[str, Any] | None,
    reconciliation: dict[str, Any] | None,
    health: dict[str, Any] | None,
    notes: str = "",
) -> str:
    """Render a Markdown end-of-session review."""
    parts: list[str] = []
    parts.append(f"# Daily review — {date}")
    parts.append("")
    parts.append(f"_Generated at {_ts()}_")
    parts.append("")

    parts.append("## Manifest")
    parts.append("")
    if manifest:
        parts.append(f"- **git_sha**: `{manifest.get('git_sha')}`")
        parts.append(f"- **git_dirty**: {manifest.get('git_dirty')}")
        parts.append(f"- **config_hash**: `{manifest.get('config_hash')}`")
        flags = manifest.get("feature_flags") or {}
        if flags:
            parts.append("- **feature_flags**:")
            for k, v in sorted(flags.items()):
                parts.append(f"  - `{k}` = `{v}`")
    else:
        parts.append("- _(no manifest loaded)_")
    parts.append("")

    parts.append("## Admissibility")
    parts.append("")
    if contamination:
        parts.append(f"- **admissible**: {contamination.get('admissible')}")
        for f in contamination.get("findings", [])[:10]:
            parts.append(
                f"  - `{f.get('severity','').upper()}` {f.get('kind')}.{f.get('key')}: {f.get('message')}"
            )
    else:
        parts.append("- _(no contamination report)_")
    parts.append("")

    parts.append("## Reconciliation")
    parts.append("")
    if reconciliation:
        parts.append(f"- **matched**: {reconciliation.get('matched')}")
        divergences = reconciliation.get("divergences") or []
        parts.append(f"- **divergences**: {len(divergences)}")
    else:
        parts.append("- _(no reconciliation report)_")
    parts.append("")

    parts.append("## Health")
    parts.append("")
    if health:
        parts.append(f"- **state**: {health.get('state')}")
        for t in health.get("triggered", [])[:10]:
            parts.append(f"  - {t.get('message')}")
    else:
        parts.append("- _(no health report)_")
    parts.append("")

    if notes.strip():
        parts.append("## Notes")
        parts.append("")
        parts.append(notes.strip())
        parts.append("")

    return "\n".join(parts)
