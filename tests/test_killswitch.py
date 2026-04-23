import pytest

from qlrk import killswitch


def test_engage_sets_flag(tmp_state):
    path = tmp_state / "ks.json"
    assert not killswitch.is_engaged(path)
    state = killswitch.engage(path, reason="test", operator="alice")
    assert state.engaged
    assert state.reason == "test"
    assert killswitch.is_engaged(path)


def test_engage_is_idempotent(tmp_state):
    path = tmp_state / "ks.json"
    first = killswitch.engage(path, reason="first", operator="alice")
    second = killswitch.engage(path, reason="second", operator="bob")
    # engaged_at must not change on re-engage
    assert first.engaged_at == second.engaged_at
    # original reason preserved
    assert second.reason == "first"


def test_clear_requires_operator(tmp_state):
    path = tmp_state / "ks.json"
    killswitch.engage(path, reason="x", operator="alice")
    with pytest.raises(ValueError):
        killswitch.clear(path, operator="")


def test_clear_resets_flag(tmp_state):
    path = tmp_state / "ks.json"
    killswitch.engage(path, reason="x", operator="alice")
    state = killswitch.clear(path, operator="alice")
    assert not state.engaged
    assert not killswitch.is_engaged(path)


def test_read_state_on_missing_file(tmp_state):
    path = tmp_state / "nope.json"
    state = killswitch.read_state(path)
    assert state.engaged is False
    assert state.reason == ""
