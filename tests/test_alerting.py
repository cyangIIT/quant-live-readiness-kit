import json

from qlrk.alerting import Alert, AlertRouter, ConsoleAdapter, FileAdapter


class _CapturingAdapter:
    def __init__(self):
        self.received = []

    def emit(self, alert):
        self.received.append(alert)


def test_router_fires_on_transition(tmp_state):
    adapter = _CapturingAdapter()
    router = AlertRouter(adapters=[adapter], state_path=tmp_state / "s.json")
    assert router.emit(Alert(severity="WARN", title="t", message="m"))
    # Same severity is suppressed by default
    assert not router.emit(Alert(severity="WARN", title="t", message="m"))
    # Different severity fires again
    assert router.emit(Alert(severity="HALT", title="t", message="m"))
    assert len(adapter.received) == 2


def test_router_ignores_transition_guard_when_disabled(tmp_state):
    adapter = _CapturingAdapter()
    router = AlertRouter(adapters=[adapter], state_path=tmp_state / "s.json")
    router.emit(Alert(severity="WARN", title="t", message="m"))
    router.emit(Alert(severity="WARN", title="t", message="m"), only_on_transition=False)
    assert len(adapter.received) == 2


def test_file_adapter_writes_json_line(tmp_state):
    path = tmp_state / "alerts.jsonl"
    adapter = FileAdapter(path)
    adapter.emit(Alert(severity="HALT", title="x", message="y"))
    line = path.read_text(encoding="utf-8").strip()
    data = json.loads(line)
    assert data["severity"] == "HALT"


def test_console_adapter_does_not_raise(capsys):
    ConsoleAdapter().emit(Alert(severity="INFO", title="x", message="y"))
    out = capsys.readouterr()
    assert "INFO" in out.err
