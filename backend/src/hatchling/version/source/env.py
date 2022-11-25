from __future__ import annotations

import os

from hatchling.version.source.plugin.interface import VersionSourceInterface


class EnvSource(VersionSourceInterface):
    PLUGIN_NAME = 'env'

    def get_version_data(self) -> dict:
        variable = self.config.get('variable', '')
        if not variable:
            raise ValueError('option `variable` must be specified')
        elif not isinstance(variable, str):
            raise TypeError('option `variable` must be a string')

        if variable not in os.environ:
            raise RuntimeError(f'environment variable `{variable}` is not set')

        return {'version': os.environ[variable]}

    def set_version(self, version: str, version_data: dict) -> None:
        raise NotImplementedError('Cannot set environment variables')
