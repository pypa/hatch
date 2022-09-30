import os

from hatchling.version.source.plugin.interface import VersionSourceInterface


class EnvSource(VersionSourceInterface):
    PLUGIN_NAME = 'env'

    def get_version_data(self):
        variable = self.config.get('variable', None)
        if not variable:
            raise ValueError('option `variable` must be specified')
        elif not isinstance(variable, str):
            raise TypeError('option `variable` must be a string')

        try:
            version = os.environ[variable]
        except KeyError:
            raise RuntimeError(f'variable `{variable}` is not set')

        return {'version': version}

    def set_version(self, version, version_data):
        raise NotImplementedError('Cannot set version environment variable with hatch.')
