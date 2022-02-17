import os
from io import open

from .plugin.interface import VersionSourceInterface


class CodeSource(VersionSourceInterface):
    PLUGIN_NAME = 'code'

    def get_version_data(self):
        relative_path = self.config.get('path')
        if not relative_path:
            raise ValueError('option `path` must be specified')
        elif not isinstance(relative_path, str):
            raise TypeError('option `path` must be a string')

        path = os.path.normpath(os.path.join(self.root, relative_path))
        if not os.path.isfile(path):
            raise OSError('file does not exist: {}'.format(relative_path))

        expression = self.config.get('expression') or '__version__'
        if not isinstance(expression, str):
            raise TypeError('option `expression` must be a string')

        with open(path, 'r', encoding='utf-8') as f:
            contents = f.read()

        global_variables = {}

        # Load the file
        exec(contents, global_variables)

        # Execute the expression to determine the version
        version = eval(expression, global_variables)

        return {'version': version}

    def set_version(self, version, version_data):
        raise NotImplementedError('Cannot rewrite loaded code')
