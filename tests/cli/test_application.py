import os
from contextlib import contextmanager
from subprocess import CompletedProcess
from unittest.mock import Mock

from hatch.cli.application import Application
from hatch.utils.runner import ExecutionContext


class FakeEnvironment:
    @contextmanager
    def command_context(self):
        yield

    def resolve_commands(self, commands):
        return commands

    def run_shell_command(self, command, **kwargs):
        self.command = command
        self.kwargs = kwargs
        return CompletedProcess(command, 0)


def test_run_shell_commands_restores_sigint_in_child(monkeypatch):
    environment = FakeEnvironment()
    context = ExecutionContext(environment, shell_commands=["echo hello"])
    application = Application(Mock(), verbosity=0, enable_color=False, interactive=False)
    signal_handler = Mock()
    monkeypatch.setattr("hatch.cli.application.signal.getsignal", signal_handler)
    monkeypatch.setattr("hatch.cli.application.signal.signal", signal_handler)

    application.run_shell_commands(context)

    assert environment.command == "echo hello"
    if os.name != "nt":
        assert "preexec_fn" in environment.kwargs
        environment.kwargs["preexec_fn"]()
        assert signal_handler.call_count == 4
    else:
        assert "preexec_fn" not in environment.kwargs
        assert signal_handler.call_count == 3
