"""Crash-safe kill switch.

A kill switch is a single persistent flag that says "do not send new
orders". It must survive process restart, and setting it must be
idempotent so that a HALT alert firing twice does not cause an error.

Contract:

* State is a JSON file on disk (one per operating envelope).
* ``engage`` writes the flag with a reason and timestamp. Safe to call
  repeatedly.
* ``clear`` removes the flag. Requires an explicit ``operator`` string
  so accidental automated clears are less likely.
* ``is_engaged`` is a fast read used by order-submission code paths.

The engine that owns the strategy is expected to check ``is_engaged``
before every entry and refuse to place new orders when True. Existing
positions are still managed by the engine's exit logic; the kill switch
does not close positions on its own.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .io_utils import atomic_write_json, load_json


@dataclass
class KillSwitchState:
    engaged: bool
    reason: str
    engaged_at: str | None
    operator: str | None
    metadata: dict[str, Any]


def _read(path: str | Path) -> dict[str, Any]:
    return load_json(path)


def is_engaged(path: str | Path) -> bool:
    return bool(_read(path).get("engaged", False))


def read_state(path: str | Path) -> KillSwitchState:
    data = _read(path)
    return KillSwitchState(
        engaged=bool(data.get("engaged", False)),
        reason=str(data.get("reason", "")),
        engaged_at=data.get("engaged_at"),
        operator=data.get("operator"),
        metadata=dict(data.get("metadata", {})),
    )


def engage(
    path: str | Path,
    *,
    reason: str,
    operator: str = "system",
    metadata: dict[str, Any] | None = None,
) -> KillSwitchState:
    """Engage the kill switch. Idempotent.

    If already engaged, the existing ``engaged_at`` is preserved (we do
    not want a repeated HALT to look like a new incident) and the
    ``reason`` is updated only if currently empty.
    """
    current = read_state(path)
    if current.engaged:
        new_reason = current.reason or reason
        data = {
            "engaged": True,
            "reason": new_reason,
            "engaged_at": current.engaged_at,
            "operator": current.operator,
            "metadata": current.metadata,
        }
    else:
        data = {
            "engaged": True,
            "reason": reason,
            "engaged_at": datetime.now(timezone.utc).isoformat(),
            "operator": operator,
            "metadata": dict(metadata or {}),
        }
    atomic_write_json(path, data)
    return read_state(path)


def clear(path: str | Path, *, operator: str) -> KillSwitchState:
    """Clear the kill switch. Requires an explicit operator label."""
    if not operator:
        raise ValueError("clear() requires an explicit operator string")
    data = {
        "engaged": False,
        "reason": "",
        "engaged_at": None,
        "operator": operator,
        "metadata": {"cleared_at": datetime.now(timezone.utc).isoformat()},
    }
    atomic_write_json(path, data)
    return read_state(path)
