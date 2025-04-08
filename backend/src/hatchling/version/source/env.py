from __future__ import annotations

import os

from hatchling.version.source.plugin.interface import VersionSourceInterface


class EnvSource(VersionSourceInterface):
    PLUGIN_NAME = 'env'

    def get_version_data(self) -> dict:
        variable = self.config.get('variable', '')
        default_value = self.config.get('default-value', '')

        if not variable:
            message = 'option `variable` must be specified'
            raise ValueError(message)

        if not isinstance(variable, str):
            message = 'option `variable` must be a string'
            raise TypeError(message)

        if default_value and not isinstance(default_value, str):
            message = 'option `default-value` must be a string'
            raise TypeError(message)

        if variable not in os.environ and not default_value:
            message = f'environment variable `{variable}` is not set'
            raise RuntimeError(message)

        return {'version': os.getenv(variable, default_value)}

    def set_version(self, version: str, version_data: dict) -> None:  # noqa: ARG002, PLR6301
        message = 'Cannot set environment variables'
        raise NotImplementedError(message)
