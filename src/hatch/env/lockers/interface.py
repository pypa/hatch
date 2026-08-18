from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hatch.env.plugin.interface import EnvironmentInterface
    from hatch.utils.fs import Path


class LockerInterface(ABC):
    """
    Pluggable dependency locker.

    Implementations are registered via the ``hatch_register_locker`` hook.
    """

    PLUGIN_NAME: str = ""

    @classmethod
    @abstractmethod
    def supports(cls, environment: EnvironmentInterface) -> bool:
        """Whether this locker can operate in the given environment."""

    @classmethod
    @abstractmethod
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
        """
        Resolve and write a lockfile from PEP 508 ``dependencies`` and optional layered inputs.

        ``dependencies`` is the list of requirement lines (merged env / project inputs) that the
        orchestrator computed for this lock operation.
        """

    @classmethod
    @abstractmethod
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
        """
        Return whether ``output_path`` matches what :meth:`generate` would write now.
        """

    @classmethod
    @abstractmethod
    def apply_lock(cls, environment: EnvironmentInterface, lock_path: Path) -> None:
        """Install packages so the environment matches the lockfile at ``lock_path``."""

    @classmethod
    def install_matches_lock(cls, _environment: EnvironmentInterface, _lock_path: Path) -> bool:
        """
        Whether the environment already matches what :meth:`apply_lock` would install.

        Used for ``locked`` environments in :meth:`~hatch.env.virtual.VirtualEnvironment.dependencies_in_sync`.
        """
        return True
