from qlrk.freeze import build_manifest, read_manifest, write_manifest


def test_build_manifest_produces_hash_and_timestamp():
    m = build_manifest(
        config={"universe": ["A", "B"], "risk_pct": 0.01},
        feature_flags={"flag_x": True},
    )
    assert m.generated_at
    assert m.config_hash
    assert m.feature_flags == {"flag_x": True}


def test_manifest_hash_is_stable_under_key_order():
    a = build_manifest(config={"x": 1, "y": 2}, feature_flags={"f": True})
    b = build_manifest(config={"y": 2, "x": 1}, feature_flags={"f": True})
    assert a.config_hash == b.config_hash


def test_manifest_hash_changes_on_value_change():
    a = build_manifest(config={"x": 1}, feature_flags={})
    b = build_manifest(config={"x": 2}, feature_flags={})
    assert a.config_hash != b.config_hash


def test_manifest_roundtrip(tmp_state):
    m = build_manifest(config={"k": "v"}, feature_flags={})
    path = tmp_state / "m.json"
    write_manifest(m, path)
    back = read_manifest(path)
    assert back is not None
    assert back.config == {"k": "v"}
    assert back.config_hash == m.config_hash


def test_read_missing_manifest_returns_none(tmp_state):
    assert read_manifest(tmp_state / "does_not_exist.json") is None
