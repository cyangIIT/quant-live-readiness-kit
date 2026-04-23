"""Freeze manifests.

A *freeze manifest* is the single source of truth for "what was running
when": it snapshots the strategy config, feature flags, universe, risk
caps, monitoring thresholds, git commit, dirty-tree state, and a hash of
all of the above. You emit one at the start of every paper/live session
and keep a pointer to the latest-admitted-clean manifest so that a
divergence on any subsequent tick is detectable.

This module is intentionally strategy-agnostic. The manifest carries a
free-form ``config`` dict; the toolkit makes no assumption about what
lives inside it.

Typical usage:

    from qlrk.freeze import build_manifest, write_manifest

    manifest = build_manifest(
        config={"universe": ["A", "B"], "risk_pct": 0.01},
        feature_flags={"auto_confirm_entries": True},
        repo_root=".",
    )
    write_manifest(manifest, "logs/freeze_manifest_latest.json")
"""
from __future__ import annotations

import logging
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .io_utils import atomic_write_json, load_json, sha256_of_mapping

log = logging.getLogger(__name__)


@dataclass
class Manifest:
    """A frozen snapshot of everything that could affect live behavior."""

    generated_at: str
    config: dict[str, Any]
    feature_flags: dict[str, Any]
    git_sha: str | None
    git_dirty: bool
    dirty_files: list[str] = field(default_factory=list)
    python_version: str = ""
    config_hash: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _git(cmd: list[str], cwd: str | Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", *cmd], cwd=str(cwd), stderr=subprocess.DEVNULL
        )
        return out.decode("utf-8").strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def _git_sha(cwd: str | Path) -> str | None:
    sha = _git(["rev-parse", "HEAD"], cwd)
    return sha or None


def _dirty_files(cwd: str | Path) -> list[str]:
    status = _git(["status", "--porcelain"], cwd)
    if not status:
        return []
    files = []
    for line in status.splitlines():
        line = line.rstrip()
        if len(line) >= 3:
            files.append(line[3:])
    return files


def build_manifest(
    *,
    config: dict[str, Any],
    feature_flags: dict[str, Any] | None = None,
    repo_root: str | Path = ".",
    notes: str = "",
) -> Manifest:
    """Construct a manifest from the current process state.

    Parameters
    ----------
    config : dict
        Arbitrary strategy/session configuration. Hashed into the manifest
        for drift detection. Keep it flat and JSON-serialisable.
    feature_flags : dict, optional
        Named booleans / enums that guard behavior changes.
    repo_root : str or Path
        Where to look for the git repo. Defaults to cwd.
    notes : str
        Free-form operator note.
    """
    import sys

    feature_flags = feature_flags or {}
    combined = {"config": config, "feature_flags": feature_flags}
    dirty_files = _dirty_files(repo_root)

    return Manifest(
        generated_at=datetime.now(timezone.utc).isoformat(),
        config=config,
        feature_flags=feature_flags,
        git_sha=_git_sha(repo_root),
        git_dirty=bool(dirty_files),
        dirty_files=dirty_files,
        python_version=sys.version.split()[0],
        config_hash=sha256_of_mapping(combined),
        notes=notes,
    )


def write_manifest(manifest: Manifest, path: str | Path) -> Path:
    """Write manifest atomically. Returns the resolved path."""
    target = Path(path)
    atomic_write_json(target, manifest.to_dict())
    return target


def read_manifest(path: str | Path) -> Manifest | None:
    """Load a manifest from disk. Returns None if missing."""
    data = load_json(path)
    if not data:
        return None
    return Manifest(
        generated_at=data.get("generated_at", ""),
        config=data.get("config", {}),
        feature_flags=data.get("feature_flags", {}),
        git_sha=data.get("git_sha"),
        git_dirty=bool(data.get("git_dirty", False)),
        dirty_files=list(data.get("dirty_files", [])),
        python_version=data.get("python_version", ""),
        config_hash=data.get("config_hash", ""),
        notes=data.get("notes", ""),
    )
