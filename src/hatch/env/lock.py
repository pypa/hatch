"""
Resolve and write environment lockfiles (PEP 751 ``pylock.toml``) via pluggable **lockers**.

Lockers are registered with ``hatch_register_locker``; built-ins ``uv`` and ``pip`` delegate to
``uv pip compile`` / ``pip lock``. See ``docs/how-to/environment/lockfiles.md``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from hatch.env.lockers.interface import LockerInterface
    from hatch.env.plugin.interface import EnvironmentInterface
    from hatch.project.core import Project
    from hatch.utils.fs import Path


class LockerNotFoundError(Exception):
    def __init__(self, name: str) -> None:
        super().__init__(f"Unknown locker plugin: {name}")
        self.name = name


class LockerUnsupportedError(Exception):
    def __init__(self, name: str, *, detail: str = "") -> None:
        msg = f"Locker `{name}` does not support this environment"
        if detail:
            msg = f"{msg}: {detail}"
        super().__init__(msg)
        self.name = name
        self.detail = detail


@dataclass
class LockGenerationState:
    """Inputs for :meth:`LockerInterface.generate` / :meth:`LockerInterface.in_sync`."""

    dependencies: list[str]
    layered: bool
    lock_extras: tuple[str, ...]
    lock_groups: tuple[str, ...]


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
    lines.extend(map(str, environment.additional_dependencies))
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


def prepare_lock_generation_state(
    environment: EnvironmentInterface,
    *,
    deps_override: list[str] | None = None,
    lock_extras: tuple[str, ...] | None = None,
    lock_groups: tuple[str, ...] | None = None,
) -> LockGenerationState | None:
    """
    Compute PEP 508 dependency lines and layered flags for the active locker.

    Returns ``None`` when there is nothing to lock (same conditions as skipping generation).
    """
    from hatch.env.virtual import VirtualEnvironment

    extras = lock_extras if lock_extras is not None else tuple(environment.features)
    groups = lock_groups if lock_groups is not None else tuple(environment.dependency_groups)

    uv = isinstance(environment, VirtualEnvironment) and environment.use_uv
    layered = uv and _uv_should_use_layered_lock(environment, extras, groups)

    if layered:
        direct_deps = deps_override if deps_override is not None else _lock_environment_only_strings(environment)
    else:
        direct_deps = deps_override if deps_override is not None else list(environment.dependencies)
        extras = ()
        groups = ()

    pyproject = environment.root / "pyproject.toml"
    if layered and not direct_deps and not pyproject.is_file():
        return None

    if not direct_deps and not (layered and pyproject.is_file()):
        return None

    return LockGenerationState(
        dependencies=list(direct_deps),
        layered=layered,
        lock_extras=extras,
        lock_groups=groups,
    )


def get_locker_plugin_class(project: Project, environment: EnvironmentInterface) -> type[LockerInterface]:
    name: str | None = environment.config.get("locker")
    if name is None:
        name = project.config.locker
    if name is None:
        from hatch.env.virtual import VirtualEnvironment

        name = "uv" if isinstance(environment, VirtualEnvironment) and environment.use_uv else "pip"

    cls = project.plugin_manager.locker.get(name)
    if cls is None:
        raise LockerNotFoundError(name)
    if not cls.supports(environment):
        raise LockerUnsupportedError(name)

    return cls


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
    state = prepare_lock_generation_state(
        environment,
        deps_override=deps_override,
        lock_extras=lock_extras,
        lock_groups=lock_groups,
    )
    if state is None:
        return

    locker_cls = get_locker_plugin_class(environment.app.project, environment)
    locker_cls.generate(
        environment,
        state.dependencies,
        output_path,
        upgrade=upgrade,
        upgrade_packages=upgrade_packages,
        layered=state.layered,
        lock_extras=state.lock_extras,
        lock_groups=state.lock_groups,
    )


def lockfile_in_sync(
    environment: EnvironmentInterface,
    output_path: Path,
    *,
    upgrade: bool = False,
    upgrade_packages: tuple[str, ...] = (),
    deps_override: list[str] | None = None,
    lock_extras: tuple[str, ...] | None = None,
    lock_groups: tuple[str, ...] | None = None,
) -> bool:
    """Whether ``output_path`` matches a fresh resolution (see :meth:`LockerInterface.in_sync`)."""
    state = prepare_lock_generation_state(
        environment,
        deps_override=deps_override,
        lock_extras=lock_extras,
        lock_groups=lock_groups,
    )
    if state is None:
        return output_path.is_file()

    locker_cls = get_locker_plugin_class(environment.app.project, environment)
    return locker_cls.in_sync(
        environment,
        state.dependencies,
        output_path,
        upgrade=upgrade,
        upgrade_packages=upgrade_packages,
        layered=state.layered,
        lock_extras=state.lock_extras,
        lock_groups=state.lock_groups,
    )


verify_lockfile = lockfile_in_sync


def apply_lock_with_locker(environment: EnvironmentInterface, lock_path: Path) -> None:
    """Apply the lockfile at ``lock_path`` using the configured locker."""
    locker_cls = get_locker_plugin_class(environment.app.project, environment)
    locker_cls.apply_lock(environment, lock_path)


def apply_lockfile_to_environment(environment: EnvironmentInterface, lock_path: Path | None = None) -> None:
    """Same as :func:`apply_lock_with_locker` using ``lock_path`` or :func:`resolve_lockfile_path`."""
    path = resolve_lockfile_path(environment) if lock_path is None else lock_path
    apply_lock_with_locker(environment, path)


def merge_environment_lock_inputs(
    project: Project,
    env_names: list[str],
    abort: Callable[[str], None],
) -> tuple[EnvironmentInterface, list[str] | None, tuple[str, ...] | None, tuple[str, ...] | None, str]:
    """
    Merge dependency lines for environments that share one lockfile (matrix / ``lock-filename``).

    Returns ``(representative_environment, deps_override, lock_extras, lock_groups, display_label)``.
    Overrides are ``None`` when only a single environment is involved (use the env's own config).
    """
    from hatch.env.virtual import VirtualEnvironment

    if len(env_names) == 1:
        environment = project.get_environment(env_names[0])
        return environment, None, None, None, env_names[0]

    seen_full: set[str] = set()
    merged_full: list[str] = []
    seen_env_only: set[str] = set()
    merged_env_only: list[str] = []
    python_versions: set[str] = set()
    extras_union: set[str] = set()
    groups_union: set[str] = set()
    for env in env_names:
        env_obj = project.get_environment(env)
        for dep in env_obj.dependencies:
            if dep not in seen_full:
                seen_full.add(dep)
                merged_full.append(dep)
        for dep in env_obj.environment_dependencies:
            if dep not in seen_env_only:
                seen_env_only.add(dep)
                merged_env_only.append(dep)
        for dep in env_obj.additional_dependencies:
            dep_s = str(dep)
            if dep_s not in seen_env_only:
                seen_env_only.add(dep_s)
                merged_env_only.append(dep_s)
        extras_union.update(env_obj.features)
        groups_union.update(env_obj.dependency_groups)
        python_version = env_obj.config.get("python", "")
        python_versions.add(python_version)

    if len(python_versions) > 1:
        versions_str = ", ".join(sorted(v for v in python_versions if v) or ["(default)"])
        abort(
            f"Environments sharing this lockfile target different Python versions ({versions_str}). "
            f"A single lockfile cannot be valid across different Python versions. "
            f"Use distinct `lock-filename` values for each Python version."
        )

    environment = project.get_environment(env_names[0])
    display_name = ", ".join(env_names)
    use_layered_merge = (
        isinstance(environment, VirtualEnvironment)
        and environment.use_uv
        and (environment.root / "pyproject.toml").is_file()
        and (extras_union or groups_union or any(not project.get_environment(e).skip_install for e in env_names))
    )
    if use_layered_merge:
        merged_deps = merged_env_only
        merged_extras = tuple(sorted(extras_union))
        merged_groups = tuple(sorted(groups_union))
    else:
        merged_deps = merged_full
        merged_extras = ()
        merged_groups = ()

    return environment, merged_deps, merged_extras, merged_groups, display_name


def resolve_lockfile_path(environment: EnvironmentInterface) -> Path:
    lock_filename = environment.config.get("lock-filename")
    if lock_filename:
        return environment.root / lock_filename

    if environment.name == "default":
        return environment.root / "pylock.toml"

    # PEP 751 only allows one dot in the filename: pylock.<name>.toml
    safe_name = environment.name.replace(".", "-")
    return environment.root / f"pylock.{safe_name}.toml"
