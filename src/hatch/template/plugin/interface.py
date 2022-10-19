from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from hatch.utils.fs import Path


class TemplateInterface:
    PLUGIN_NAME = ''
    PRIORITY = 100

    def __init__(self, plugin_config: dict, cache_dir: 'Path', creation_time: 'datetime') -> None:
        self.plugin_config = plugin_config
        self.cache_dir = cache_dir
        self.creation_time = creation_time

    def initialize_config(self, config) -> None:
        """
        Allow modification of the configuration passed to every file for new projects
        before the list of files are determined.
        """

    def get_files(self, config):
        """Add to the list of files for new projects that are written to the file system."""
        return []

    def finalize_files(self, config, files) -> None:
        """Allow modification of files for new projects before they are written to the file system."""
        pass
