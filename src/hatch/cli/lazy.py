from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from collections.abc import Sequence

class LazyGroup(click.Group):
    """A click Group that defers subcommand imports until invocation time.

    Commands are registered as dotted import paths (e.g. "hatch.cli.build:build")
    and only imported when actually invoked or when help listing forces enumeration.
    """

    def __init__(self, *args, lazy_subcommands: dict[str, str] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        # Map of command-name -> "module.path:attribute"
        self._lazy_subcommands: dict[str, str] = lazy_subcommands or {}

    def list_commands(self, ctx: click.Context) -> list[str]:
        # Merge eagerly-added commands with lazy ones, sorted
        eager = super().list_commands(ctx)
        return sorted(set(eager) | set(self._lazy_subcommands))

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.BaseCommand | None:
        # Check eagerly-registered commands first
        if cmd := super().get_command(ctx, cmd_name):
            return cmd

        if cmd_name not in self._lazy_subcommands:
            return None

        # Import on demand
        import_path = self._lazy_subcommands[cmd_name]
        module_path, attr_name = import_path.rsplit(":", 1)
        module = importlib.import_module(module_path)
        cmd = getattr(module, attr_name)

        # Cache it so subsequent calls don't re-import
        self.add_command(cmd, cmd_name)
        return cmd