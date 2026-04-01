from __future__ import annotations

import tempfile
from typing import TYPE_CHECKING

from hatch.env.lockers.interface import LockerInterface
from hatch.env.utils import add_verbosity_flag
from hatch.utils.fs import Path

if TYPE_CHECKING:
    from hatch.env.plugin.interface import EnvironmentInterface
    from hatch.env.virtual import VirtualEnvironment


class UvLocker(LockerInterface):
    PLUGIN_NAME = "uv"

    @classmethod
    def supports(cls, environment: EnvironmentInterface) -> bool:
        from hatch.env.virtual import VirtualEnvironment

        return isinstance(environment, VirtualEnvironment) and environment.use_uv

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
        from hatch.env.virtual import VirtualEnvironment

        if not isinstance(environment, VirtualEnvironment):
            message = "UvLocker requires a virtual environment with UV"
            raise TypeError(message)

        env = environment
        deps_file: Path | None = None
        if dependencies:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
                f.write("\n".join(dependencies))
                f.write("\n")
                deps_file = Path(f.name)

        try:
            cls._compile(
                env,
                output_path,
                upgrade=upgrade,
                upgrade_packages=upgrade_packages,
                layered=layered,
                lock_extras=lock_extras,
                lock_groups=lock_groups,
                requirements_file=deps_file,
            )
        finally:
            if deps_file is not None:
                deps_file.unlink(missing_ok=True)

    @classmethod
    def _compile(
        cls,
        environment: VirtualEnvironment,
        output_path: Path,
        *,
        upgrade: bool,
        upgrade_packages: tuple[str, ...],
        layered: bool,
        lock_extras: tuple[str, ...],
        lock_groups: tuple[str, ...],
        requirements_file: Path | None,
    ) -> None:
        pyproject = environment.root / "pyproject.toml"
        command = [environment.uv_path, "pip", "compile"]

        if requirements_file is not None:
            command.append(str(requirements_file))
        if layered:
            command.append(str(pyproject))

        command.extend([
            "--generate-hashes",
            "--output-file",
            str(output_path),
        ])

        for extra in lock_extras:
            command.extend(["--extra", extra])
        for group in lock_groups:
            command.extend(["--group", group])

        add_verbosity_flag(command, environment.verbosity, adjustment=-1)

        if upgrade:
            command.append("--upgrade")
        for pkg in upgrade_packages:
            command.extend(["--upgrade-package", pkg])

        python_version = environment.config.get("python", "")
        if python_version:
            command.extend(["--python-version", python_version])

        with environment.command_context():
            environment.platform.check_command(command)

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

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False, encoding="utf-8") as f:
            temp_path = Path(f.name)

        try:
            cls.generate(
                environment,
                dependencies,
                temp_path,
                upgrade=upgrade,
                upgrade_packages=upgrade_packages,
                layered=layered,
                lock_extras=lock_extras,
                lock_groups=lock_groups,
            )
            existing = output_path.read_text(encoding="utf-8")
            fresh = temp_path.read_text(encoding="utf-8")
        finally:
            temp_path.unlink(missing_ok=True)

        return existing == fresh

    @classmethod
    def apply_lock(cls, environment: EnvironmentInterface, lock_path: Path) -> None:
        from hatch.env.virtual import VirtualEnvironment

        if not isinstance(environment, VirtualEnvironment):
            message = "UvLocker.apply_lock requires a virtual environment"
            raise TypeError(message)

        with environment.command_context():
            environment.platform.check_command(environment.uv_pip_sync_command(lock_path))

    @classmethod
    def install_matches_lock(cls, environment: EnvironmentInterface, lock_path: Path) -> bool:
        from hatch.env.virtual import VirtualEnvironment

        if not isinstance(environment, VirtualEnvironment):
            return True

        completed = environment.platform.run_command(
            environment.uv_pip_sync_command(lock_path, dry_run=True),
            capture_output=True,
        )
        return completed.returncode == 0
