from __future__ import annotations

import tempfile
from typing import TYPE_CHECKING

from hatch.env.utils import add_verbosity_flag
from hatch.utils.fs import Path

if TYPE_CHECKING:
    from hatch.env.plugin.interface import EnvironmentInterface
    from hatch.env.virtual import VirtualEnvironment


def environment_has_lock_inputs(environment: EnvironmentInterface) -> bool:
    """Whether the environment has anything to pass to the lock resolver."""
    if environment.environment_dependencies or environment.additional_dependencies:
        return True
    if environment.features or environment.dependency_groups:
        return (environment.root / "pyproject.toml").is_file()
    if not environment.skip_install and (environment.root / "pyproject.toml").is_file():
        return True
    return bool(environment.dependencies)


def _lock_environment_only_strings(environment: EnvironmentInterface) -> list[str]:
    lines = list(environment.environment_dependencies)
    for dep in environment.additional_dependencies:
        lines.append(str(dep))
    return lines


def _uv_should_use_layered_lock(
    environment: EnvironmentInterface,
    lock_extras: tuple[str, ...],
    lock_groups: tuple[str, ...],
) -> bool:
    if not (environment.root / "pyproject.toml").is_file():
        return False
    if lock_extras or lock_groups:
        return True
    return not environment.skip_install


def generate_lockfile(
    environment: EnvironmentInterface,
    output_path: Path,
    *,
    upgrade: bool = False,
    upgrade_packages: tuple[str, ...] = (),
    deps_override: list[str] | None = None,
    lock_extras: tuple[str, ...] | None = None,
    lock_groups: tuple[str, ...] | None = None,
) -> None:
    from hatch.env.virtual import VirtualEnvironment

    extras = lock_extras if lock_extras is not None else tuple(environment.features)
    groups = lock_groups if lock_groups is not None else tuple(environment.dependency_groups)

    uv = isinstance(environment, VirtualEnvironment) and environment.use_uv
    layered = uv and _uv_should_use_layered_lock(environment, extras, groups)

    if layered:
        direct_deps = deps_override if deps_override is not None else _lock_environment_only_strings(environment)
    else:
        direct_deps = deps_override if deps_override is not None else environment.dependencies
        extras = ()
        groups = ()

    pyproject = environment.root / "pyproject.toml"
    if layered and not direct_deps and not pyproject.is_file():
        return

    if not direct_deps and not (layered and pyproject.is_file()):
        return

    deps_file: Path | None = None
    if direct_deps:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("\n".join(direct_deps))
            f.write("\n")
            deps_file = Path(f.name)

    try:
        if isinstance(environment, VirtualEnvironment) and environment.use_uv:
            _lock_with_uv(
                environment,
                output_path,
                upgrade=upgrade,
                upgrade_packages=upgrade_packages,
                layered=layered,
                lock_extras=extras,
                lock_groups=groups,
                requirements_file=deps_file,
            )
        else:
            if deps_file is None:
                return
            _lock_with_pip(environment, deps_file, output_path, upgrade=upgrade, upgrade_packages=upgrade_packages)
    finally:
        if deps_file is not None:
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
    output_path: Path,
    *,
    upgrade: bool = False,
    upgrade_packages: tuple[str, ...] = (),
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

    command.extend(
        [
            "--generate-hashes",
            "--output-file",
            str(output_path),
        ]
    )

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


def resolve_lockfile_path(environment: EnvironmentInterface) -> Path:
    lock_filename = environment.config.get("lock-filename")
    if lock_filename:
        return environment.root / lock_filename

    if environment.name == "default":
        return environment.root / "pylock.toml"

    # PEP 751 only allows one dot in the filename: pylock.<name>.toml
    safe_name = environment.name.replace(".", "-")
    return environment.root / f"pylock.{safe_name}.toml"
