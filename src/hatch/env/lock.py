from __future__ import annotations

import tempfile
from typing import TYPE_CHECKING

from hatch.env.utils import add_verbosity_flag
from hatch.utils.fs import Path

if TYPE_CHECKING:
    from hatch.env.plugin.interface import EnvironmentInterface
    from hatch.env.virtual import VirtualEnvironment


def generate_lockfile(
    environment: EnvironmentInterface,
    output_path: Path,
    *,
    upgrade: bool = False,
    upgrade_packages: tuple[str, ...] = (),
) -> None:
    deps = environment.dependencies
    if not deps:
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("\n".join(deps))
        f.write("\n")
        deps_file = Path(f.name)

    try:
        from hatch.env.virtual import VirtualEnvironment

        if isinstance(environment, VirtualEnvironment) and environment.use_uv:
            _lock_with_uv(environment, deps_file, output_path, upgrade=upgrade, upgrade_packages=upgrade_packages)
        else:
            _lock_with_pip(environment, deps_file, output_path, upgrade=upgrade, upgrade_packages=upgrade_packages)
    finally:
        deps_file.unlink()


def _lock_with_pip(
    environment: EnvironmentInterface,
    deps_file: Path,
    output_path: Path,
    *,
    upgrade: bool = False,
    upgrade_packages: tuple[str, ...] = (),
) -> None:
    command = ["python", "-u", "-m", "pip", "lock", "-r", str(deps_file), "-o", str(output_path)]

    add_verbosity_flag(command, environment.verbosity, adjustment=-1)

    if upgrade:
        command.append("--upgrade")
    for pkg in upgrade_packages:
        command.extend(["--upgrade-package", pkg])

    with environment.command_context():
        environment.platform.check_command(command)


def _lock_with_uv(
    environment: VirtualEnvironment,
    deps_file: Path,
    output_path: Path,
    *,
    upgrade: bool = False,
    upgrade_packages: tuple[str, ...] = (),
) -> None:
    command = [
        environment.uv_path,
        "pip",
        "compile",
        str(deps_file),
        "--generate-hashes",
        "--output-file",
        str(output_path),
    ]

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


def resolve_output_path(environment: EnvironmentInterface, custom_output: str | None = None) -> Path:
    if custom_output:
        return Path(custom_output)

    lock_filename = environment.config.get("lock-filename")
    if lock_filename:
        return environment.root / lock_filename

    if environment.name == "default":
        return environment.root / "pylock.toml"

    return environment.root / f"pylock.{environment.name}.toml"
