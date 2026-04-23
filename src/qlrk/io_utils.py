"""Safe file I/O helpers used across the toolkit.

- ``atomic_write_json`` writes to a temp file then renames, so a crash mid-
  write cannot leave a half-written artifact.
- ``load_yaml`` / ``load_json`` enforce UTF-8 and return ``{}`` for missing
  files rather than raising (callers should decide what missing means).
- ``sha256_of_mapping`` produces a canonical hash of a nested dict, useful
  for detecting config drift.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import yaml


def atomic_write_json(path: str | os.PathLike[str], data: Any, *, indent: int = 2) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=target.name + ".", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=indent, sort_keys=True, default=str)
            fh.write("\n")
        os.replace(tmp, target)
    except Exception:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def load_json(path: str | os.PathLike[str]) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_yaml(path: str | os.PathLike[str]) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def sha256_of_mapping(mapping: dict[str, Any]) -> str:
    canonical = json.dumps(mapping, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
