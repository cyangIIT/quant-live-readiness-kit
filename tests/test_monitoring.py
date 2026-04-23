import pytest

from qlrk.monitoring import Rule, evaluate, transition


def test_pass_when_no_rule_triggers():
    rules = [Rule(name="dd", metric="dd", op=">", threshold=0.1, severity="HALT")]
    r = evaluate({"dd": 0.02}, rules)
    assert r.state == "PASS"
    assert r.triggered == []


def test_warn_state():
    rules = [Rule(name="dd_w", metric="dd", op=">", threshold=0.01, severity="WARN")]
    r = evaluate({"dd": 0.05}, rules)
    assert r.state == "WARN"
    assert len(r.triggered) == 1


def test_halt_beats_warn():
    rules = [
        Rule(name="w", metric="x", op=">", threshold=0, severity="WARN"),
        Rule(name="h", metric="x", op=">", threshold=0, severity="HALT"),
    ]
    r = evaluate({"x": 1}, rules)
    assert r.state == "HALT"
    assert len(r.triggered) == 2


def test_missing_metric_does_not_trigger():
    rules = [Rule(name="x", metric="missing", op=">", threshold=0, severity="HALT")]
    r = evaluate({}, rules)
    assert r.state == "PASS"


def test_unknown_op_raises():
    r = Rule(name="x", metric="y", op="??", threshold=0, severity="WARN")
    with pytest.raises(ValueError):
        r.evaluate(5)


def test_transition_detection():
    assert transition("PASS", "WARN") == "PASS->WARN"
    assert transition("WARN", "WARN") is None
    assert transition(None, "HALT") == "INIT->HALT"


def test_rule_from_dict():
    r = Rule.from_dict({
        "name": "dd",
        "metric": "drawdown",
        "op": ">",
        "threshold": 0.05,
        "severity": "warn",
        "message": "too deep",
    })
    assert r.severity == "WARN"
    assert r.evaluate(0.1)
