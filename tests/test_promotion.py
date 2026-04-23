from qlrk.promotion import score


def _checklist():
    return {
        "stage": "limited_live",
        "checks": [
            {"name": "freeze", "kind": "boolean", "value_key": "freeze_manifest_exists"},
            {"name": "dd", "kind": "threshold", "metric": "dd_pct", "op": "<", "threshold": 0.05},
            {"name": "operator", "kind": "manual", "default": False},
        ],
    }


def test_all_pass():
    metrics = {"freeze_manifest_exists": True, "dd_pct": 0.02}
    r = score(_checklist(), metrics, manual_overrides={"operator": True})
    assert r.passed
    assert all(c.passed for c in r.checks)


def test_boolean_fails_when_false():
    r = score(_checklist(), {"freeze_manifest_exists": False, "dd_pct": 0.02}, manual_overrides={"operator": True})
    assert not r.passed
    failed_names = {c.name for c in r.failed()}
    assert "freeze" in failed_names


def test_threshold_fails_when_above():
    r = score(_checklist(), {"freeze_manifest_exists": True, "dd_pct": 0.06}, manual_overrides={"operator": True})
    assert not r.passed
    assert "dd" in {c.name for c in r.failed()}


def test_manual_default_false():
    r = score(_checklist(), {"freeze_manifest_exists": True, "dd_pct": 0.02})
    assert not r.passed
    assert "operator" in {c.name for c in r.failed()}


def test_unknown_kind_is_recorded_as_failure():
    checklist = {"stage": "x", "checks": [{"name": "mystery", "kind": "quantum"}]}
    r = score(checklist, {})
    assert not r.passed
    assert r.checks[0].detail.startswith("unknown")


def test_missing_metric_treated_as_fail():
    checklist = {
        "stage": "x",
        "checks": [{"name": "dd", "kind": "threshold", "metric": "dd", "op": "<", "threshold": 0.05}],
    }
    r = score(checklist, {})
    assert not r.passed
