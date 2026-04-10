from __future__ import annotations

import tempfile
from typing import TYPE_CHECKING

from hatch.env.lockers.interface import LockerInterface
from hatch.env.utils import add_verbosity_flag
from hatch.utils.fs import Path

if TYPE_CHECKING:
    from hatch.env.plugin.interface import EnvironmentInterface


class PipLocker(LockerInterface):
    PLUGIN_NAME = "pip"

    @classmethod
    def supports(cls, _environment: EnvironmentInterface) -> bool:
        return True

    @classmethod
    def generate(
        cls,
        environment: EnvironmentInterface,
        dependencies: list[str],
        output_path: Path,
        *,
        upgrade: bool = False,
        upgrade_packages: tuple[str, ...] = (),
        layered: bool = False,
        lock_extras: tuple[str, ...] = (),
        lock_groups: tuple[str, ...] = (),
    ) -> None:
        if layered or lock_extras or lock_groups:
            message = "The pip locker does not support layered locks with extras or dependency-groups; use installer uv"
            raise ValueError(message)

        if not dependencies:
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("\n".join(dependencies))
            f.write("\n")
            deps_file = Path(f.name)

        try:
            command = ["python", "-u", "-m", "pip", "lock", "-r", str(deps_file), "-o", str(output_path)]

            add_verbosity_flag(command, environment.verbosity, adjustment=-1)

            if upgrade:
                command.append("--upgrade")
            for pkg in upgrade_packages:
                command.extend(["--upgrade-package", pkg])

            with environment.command_context():
                environment.platform.check_command(command)
        finally:
            deps_file.unlink(missing_ok=True)

    @classmethod
    def in_sync(
        cls,
        environment: EnvironmentInterface,
        dependencies: list[str],
        output_path: Path,
        *,
        upgrade: bool = False,
        upgrade_packages: tuple[str, ...] = (),
        layered: bool = False,
        lock_extras: tuple[str, ...] = (),
        lock_groups: tuple[str, ...] = (),
    ) -> bool:
        if not output_path.is_file():
            return False

        if layered or lock_extras or lock_groups:
            return False

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False, encoding="utf-8") as f:
            temp_path = Path(f.name)

        try:
            cls.generate(
                environment,
                dependencies,
                temp_path,
                upgrade=upgrade,
                upgrade_packages=upgrade_packages,
                layered=False,
                lock_extras=(),
                lock_groups=(),
            )
            existing = output_path.read_text(encoding="utf-8")
            fresh = temp_path.read_text(encoding="utf-8")
        finally:
            temp_path.unlink(missing_ok=True)

        return existing == fresh

    @classmethod
    def apply_lock(cls, _environment: EnvironmentInterface, _lock_path: Path) -> None:
        from hatch.env.lock import LockerUnsupportedError

        message = (
            "Applying lockfiles with the pip locker is not yet supported. "
            'Use `installer = "uv"` (or `locker = "uv"`) for locked sync.'
        )
        raise LockerUnsupportedError(cls.PLUGIN_NAME, detail=message)

    @classmethod
    def install_matches_lock(cls, _environment: EnvironmentInterface, _lock_path: Path) -> bool:
        # We cannot verify lock conformance for pip because apply_lock is unsupported.
        return False
