from __future__ import annotations

from typing import Any

from hatchling.builders.binary import BinaryBuilder


class AppBuilder(BinaryBuilder):
    PLUGIN_NAME = 'app'

    def build_bootstrap(
        self,
        directory: str,
        **build_data: Any,
    ) -> str:
        self.app.display_warning(
            'The `app` build target is deprecated and will be removed in a future release. '
            'Use the `binary` build target instead.'
        )
        return super().build_bootstrap(directory, **build_data)
