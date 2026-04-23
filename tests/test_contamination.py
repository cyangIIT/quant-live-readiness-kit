from qlrk.contamination import detect
from qlrk.freeze import build_manifest


def _m(config=None, flags=None, dirty=False):
    m = build_manifest(config=config or {}, feature_flags=flags or {})
    # Override volatile fields for deterministic tests
    m.git_sha = "abc123"
    m.git_dirty = dirty
    m.dirty_files = ["x.py"] if dirty else []
    return m


def test_identical_manifests_are_admissible():
    clean = _m(config={"risk_pct": 0.01})
    current = _m(config={"risk_pct": 0.01})
    # recompute hash so they match
    current.config_hash = clean.config_hash
    report = detect(current, clean)
    assert report.admissible
    assert report.findings == []


def test_config_change_blocks_admissibility():
    clean = _m(config={"risk_pct": 0.01})
    current = _m(config={"risk_pct": 0.02})
    report = detect(current, clean)
    assert not report.admissible
    assert any(f.kind == "config" and f.key == "risk_pct" for f in report.findings)


def test_feature_flag_change_blocks_by_default():
    clean = _m(flags={"new_entry": False})
    current = _m(flags={"new_entry": True})
    report = detect(current, clean)
    assert not report.admissible
    assert any(f.kind == "feature_flag" for f in report.findings)


def test_feature_flag_change_can_be_downgraded_to_warn():
    clean = _m(flags={"f": False})
    current = _m(flags={"f": True})
    report = detect(current, clean, block_on_flag_change=False)
    assert report.admissible  # only WARN findings
    assert any(f.severity == "warn" and f.kind == "feature_flag" for f in report.findings)


def test_dirty_tree_blocks_when_clean_baseline_was_clean():
    clean = _m(dirty=False)
    current = _m(dirty=True)
    report = detect(current, clean)
    assert not report.admissible
    assert any(f.kind == "dirty" for f in report.findings)


def test_git_sha_change_is_warn_by_default():
    clean = _m()
    current = _m()
    current.git_sha = "different"
    report = detect(current, clean)
    # default: warn only for git SHA
    assert report.admissible
    assert any(f.kind == "git_sha" and f.severity == "warn" for f in report.findings)


def test_report_round_trips_to_dict():
    clean = _m(config={"x": 1})
    current = _m(config={"x": 2})
    report = detect(current, clean)
    data = report.to_dict()
    assert "admissible" in data
    assert "findings" in data
    assert data["findings"][0]["kind"] == "config"
