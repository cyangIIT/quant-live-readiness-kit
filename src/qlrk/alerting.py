"""Pluggable alerting adapters.

Built-in adapters:

* ``ConsoleAdapter`` — print to stderr. Always safe.
* ``FileAdapter`` — append JSON line to a rotated file.
* ``WebhookAdapter`` — POST a JSON payload. Network failure falls through
  to a logger warning; never raises.

Adapters are fed through ``AlertRouter``, which fires each alert only on
*state transitions* so a stuck HALT does not spam the channel every
tick.

Adapters are intentionally minimal — the goal is an obvious path for
adding your own (Slack, PagerDuty, SES, etc.) without touching the rest
of the toolkit.
"""
from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol
from urllib import error, request

from .io_utils import atomic_write_json, load_json

log = logging.getLogger(__name__)


@dataclass
class Alert:
    severity: str  # "INFO" | "WARN" | "HALT" | "CLEAR"
    title: str
    message: str
    ts: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.ts:
            self.ts = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "ts": self.ts,
            "metadata": self.metadata,
        }


class Adapter(Protocol):
    def emit(self, alert: Alert) -> None: ...


class ConsoleAdapter:
    def __init__(self, stream: Any | None = None) -> None:
        self._stream = stream or sys.stderr

    def emit(self, alert: Alert) -> None:
        tag = f"[{alert.severity}]"
        line = f"{alert.ts} {tag} {alert.title}: {alert.message}"
        print(line, file=self._stream, flush=True)


class FileAdapter:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, alert: Alert) -> None:
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(alert.to_dict(), sort_keys=True) + "\n")


class WebhookAdapter:
    """POST alert JSON to a URL. Failures are logged, never raised."""

    def __init__(self, url: str, *, timeout: float = 3.0) -> None:
        self.url = url
        self.timeout = timeout

    def emit(self, alert: Alert) -> None:
        data = json.dumps(alert.to_dict()).encode("utf-8")
        req = request.Request(
            self.url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310
                resp.read()
        except (error.URLError, error.HTTPError, OSError) as exc:
            log.warning("webhook emit failed: %s", exc)


@dataclass
class AlertRouter:
    """Forward alerts to all adapters, with transition-only firing."""

    adapters: list[Adapter]
    state_path: str | Path | None = None

    def _load_last(self) -> str | None:
        if not self.state_path:
            return None
        return load_json(self.state_path).get("last_severity")

    def _save_last(self, severity: str) -> None:
        if not self.state_path:
            return
        atomic_write_json(self.state_path, {"last_severity": severity})

    def emit(self, alert: Alert, *, only_on_transition: bool = True) -> bool:
        """Emit an alert. Returns True if it was dispatched.

        When ``only_on_transition`` is True (default), duplicate severities
        are suppressed. Pass False for alerts that should always fire
        regardless of prior state (e.g. manual test alerts).
        """
        last = self._load_last()
        if only_on_transition and last == alert.severity:
            return False
        for adapter in self.adapters:
            try:
                adapter.emit(alert)
            except Exception as exc:  # adapter bugs must not crash caller
                log.warning("adapter %s failed: %s", type(adapter).__name__, exc)
        self._save_last(alert.severity)
        return True
