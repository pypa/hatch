from contextlib import nullcontext

from hatch.env.virtual import VirtualEnvironment


class _Platform:
    def __init__(self) -> None:
        self.commands: list[list[str]] = []

    def check_command(self, command: list[str]) -> None:
        self.commands.append(command)


class _LockedEnv(VirtualEnvironment):
    def __init__(self, root) -> None:
        self._root = root
        self._platform = _Platform()

    @property
    def root(self):
        return self._root

    @property
    def locked(self) -> bool:
        return True

    @property
    def skip_install(self) -> bool:
        return False

    @property
    def dev_mode(self) -> bool:
        return True

    @property
    def local_dependencies_complex(self):
        return []

    @property
    def platform(self):
        return self._platform

    def safe_activation(self):
        return nullcontext()

    def construct_pip_install_command(self, args: list[str]) -> list[str]:
        return ["install", *args]

    def apply_features(self, requirement: str) -> str:
        return requirement


def test_locked_sync_reinstalls_editable_project(tmp_path, monkeypatch):
    env = _LockedEnv(tmp_path)
    lockfile = tmp_path / "pylock.toml"
    lockfile.write_text("lock\n", encoding="utf-8")
    monkeypatch.setattr("hatch.env.lock.resolve_lockfile_path", lambda _env: lockfile)
    monkeypatch.setattr(
        "hatch.env.lock.apply_lock_with_locker",
        lambda *_args, **_kwargs: env.platform.commands.append(["sync"]),
    )

    env.sync_dependencies()

    assert env.platform.commands[0] == ["sync"]
    assert env.platform.commands[1] == ["install", "--editable", str(tmp_path)]
