"""Contamination detection.

Given two manifests — ``current`` (what is running now) and ``clean``
(the admitted-clean baseline) — return a structured list of reasons the
current state is *not* admissible as promotion evidence.

The checks are intentionally structural and strategy-agnostic:

* ``git_sha`` differs
* ``git_dirty`` is True when the clean baseline was clean
* any key in ``config`` was added, removed, or changed value
* any key in ``feature_flags`` was added, removed, or changed value
* ``config_hash`` does not match (belt-and-braces; redundant with the
  per-key diff but cheap to include)

The module makes no business judgement about *which* drifts are acceptable.
That is a policy decision for your team. This module reports; you decide.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .freeze import Manifest


@dataclass
class Finding:
    kind: str  # "git_sha" | "dirty" | "config" | "feature_flag" | "config_hash"
    key: str
    severity: str  # "warn" | "block"
    message: str
    current: Any = None
    clean: Any = None


@dataclass
class ContaminationReport:
    admissible: bool
    findings: list[Finding] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "admissible": self.admissible,
            "findings": [
                {
                    "kind": f.kind,
                    "key": f.key,
                    "severity": f.severity,
                    "message": f.message,
                    "current": f.current,
                    "clean": f.clean,
                }
                for f in self.findings
            ],
        }


def _diff_mapping(
    current: dict[str, Any],
    clean: dict[str, Any],
    *,
    kind: str,
    severity: str,
) -> list[Finding]:
    findings: list[Finding] = []
    for key in set(current) | set(clean):
        cur = current.get(key, "<absent>")
        cln = clean.get(key, "<absent>")
        if cur == cln:
            continue
        findings.append(
            Finding(
                kind=kind,
                key=key,
                severity=severity,
                message=f"{kind}.{key} changed: {cln!r} -> {cur!r}",
                current=cur,
                clean=cln,
            )
        )
    return findings


def detect(
    current: Manifest,
    clean: Manifest,
    *,
    block_on_dirty: bool = True,
    block_on_flag_change: bool = True,
    block_on_git_sha: bool = False,
) -> ContaminationReport:
    """Compare ``current`` against the admitted-clean baseline.

    Returns a ``ContaminationReport``. ``admissible`` is True iff there are
    no ``block`` severity findings.
    """
    findings: list[Finding] = []

    if current.git_sha != clean.git_sha:
        findings.append(
            Finding(
                kind="git_sha",
                key="git_sha",
                severity="block" if block_on_git_sha else "warn",
                message=f"git SHA changed: {clean.git_sha} -> {current.git_sha}",
                current=current.git_sha,
                clean=clean.git_sha,
            )
        )

    if current.git_dirty and not clean.git_dirty:
        findings.append(
            Finding(
                kind="dirty",
                key="git_dirty",
                severity="block" if block_on_dirty else "warn",
                message=(
                    "uncommitted changes in working tree; clean baseline was clean"
                ),
                current=current.dirty_files,
                clean=[],
            )
        )

    findings.extend(
        _diff_mapping(current.config, clean.config, kind="config", severity="block")
    )
    findings.extend(
        _diff_mapping(
            current.feature_flags,
            clean.feature_flags,
            kind="feature_flag",
            severity="block" if block_on_flag_change else "warn",
        )
    )

    if current.config_hash and clean.config_hash and current.config_hash != clean.config_hash:
        if not any(f.kind in ("config", "feature_flag") for f in findings):
            findings.append(
                Finding(
                    kind="config_hash",
                    key="config_hash",
                    severity="block",
                    message="config_hash differs but no per-key diff was detected; inputs may have non-deterministic ordering",
                    current=current.config_hash,
                    clean=clean.config_hash,
                )
            )

    admissible = not any(f.severity == "block" for f in findings)
    return ContaminationReport(admissible=admissible, findings=findings)
