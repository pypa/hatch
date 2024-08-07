from __future__ import annotations

import os

from hatchling.version.source.plugin.interface import VersionSourceInterface


class CodeSource(VersionSourceInterface):
    PLUGIN_NAME = 'code'

    def get_version_data(self) -> dict:
        import sys
        from importlib.util import module_from_spec, spec_from_file_location

        relative_path = self.config.get('path')
        if not relative_path:
            message = 'option `path` must be specified'
            raise ValueError(message)

        if not isinstance(relative_path, str):
            message = 'option `path` must be a string'
            raise TypeError(message)

        path = os.path.normpath(os.path.join(self.root, relative_path))
        if not os.path.isfile(path):
            message = f'file does not exist: {relative_path}'
            raise OSError(message)

        expression = self.config.get('expression') or '__version__'
        if not isinstance(expression, str):
            message = 'option `expression` must be a string'
            raise TypeError(message)

        search_paths = self.config.get('search-paths', [])
        if not isinstance(search_paths, list):
            message = 'option `search-paths` must be an array'
            raise TypeError(message)

        absolute_search_paths = []
        for i, search_path in enumerate(search_paths, 1):
            if not isinstance(search_path, str):
                message = f'entry #{i} of option `search-paths` must be a string'
                raise TypeError(message)

            absolute_search_paths.append(os.path.normpath(os.path.join(self.root, search_path)))

        spec = spec_from_file_location(os.path.splitext(path)[0], path)
        module = module_from_spec(spec)  # type: ignore[arg-type]

        old_search_paths = list(sys.path)
        try:
            sys.path[:] = [*absolute_search_paths, *old_search_paths]
            spec.loader.exec_module(module)  # type: ignore[union-attr]
        finally:
            sys.path[:] = old_search_paths

        # Execute the expression to determine the version
        version = eval(expression, vars(module))  # noqa: S307

        return {'version': version}

    def set_version(self, version: str, version_data: dict) -> None:  # noqa: ARG002, PLR6301
        message = 'Cannot rewrite loaded code'
        raise NotImplementedError(message)
