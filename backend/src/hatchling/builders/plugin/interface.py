from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Callable, Generator

from ..config import BuilderConfig, env_var_enabled
from ..constants import BuildEnvVars
from ..utils import safe_walk


class IncludedFile:
    __slots__ = ('path', 'relative_path', 'distribution_path')

    def __init__(self, path, relative_path, distribution_path):
        self.path = path
        self.relative_path = relative_path
        self.distribution_path = distribution_path


class BuilderInterface(ABC):
    """
    Example usage:

    === ":octicons-file-code-16: plugin.py"

        ```python
        from hatchling.builders.plugin.interface import BuilderInterface


        class SpecialBuilder(BuilderInterface):
            PLUGIN_NAME = 'special'
            ...
        ```

    === ":octicons-file-code-16: hooks.py"

        ```python
        from hatchling.plugin import hookimpl

        from .plugin import SpecialBuilder


        @hookimpl
        def hatch_register_builder():
            return SpecialBuilder
        ```
    """

    PLUGIN_NAME = ''
    """The name used for selection."""

    def __init__(self, root, plugin_manager=None, config=None, metadata=None, app=None):
        self.__root = root
        self.__plugin_manager = plugin_manager
        self.__raw_config = config
        self.__metadata = metadata
        self.__app = app
        self.__config = None
        self.__project_config = None
        self.__hatch_config = None
        self.__build_config = None
        self.__build_targets = None
        self.__target_config = None

        # Metadata
        self.__project_id = None

    def build(
        self,
        directory=None,
        versions=None,
        hooks_only=None,
        clean=None,
        clean_hooks_after=None,
        clean_only=False,
    ) -> Generator[str, None, None]:
        # Fail early for invalid project metadata
        self.metadata.validate_fields()

        if directory is None:
            if BuildEnvVars.LOCATION in os.environ:
                directory = self.config.normalize_build_directory(os.environ[BuildEnvVars.LOCATION])
            else:
                directory = self.config.directory

        if not os.path.isdir(directory):
            os.makedirs(directory)

        version_api = self.get_version_api()

        if not versions:
            versions = self.config.versions
        else:
            unknown_versions = set(versions) - set(version_api)
            if unknown_versions:
                raise ValueError(
                    f'Unknown versions for target `{self.PLUGIN_NAME}`: {", ".join(map(str, sorted(unknown_versions)))}'
                )

        if hooks_only is None:
            hooks_only = env_var_enabled(BuildEnvVars.HOOKS_ONLY)

        configured_build_hooks = self.get_build_hooks(directory)
        build_hooks = list(configured_build_hooks.values())

        if clean_only:
            clean = True
        elif clean is None:
            clean = env_var_enabled(BuildEnvVars.CLEAN)
        if clean:
            if not hooks_only:
                self.clean(directory, versions)

            for build_hook in build_hooks:
                build_hook.clean(versions)

            if clean_only:
                return

        if clean_hooks_after is None:
            clean_hooks_after = env_var_enabled(BuildEnvVars.CLEAN_HOOKS_AFTER)

        for version in versions:
            self.app.display_debug(f'Building `{self.PLUGIN_NAME}` version `{version}`')

            build_data = self.get_default_build_data()

            # Make sure reserved fields are set
            build_data.setdefault('artifacts', [])
            build_data.setdefault('force_include', {})

            # Allow inspection of configured build hooks and the order in which they run
            build_data['build_hooks'] = tuple(configured_build_hooks)

            # Execute all `initialize` build hooks
            for build_hook in build_hooks:
                build_hook.initialize(version, build_data)

            if hooks_only:
                self.app.display_debug(f'Only ran build hooks for `{self.PLUGIN_NAME}` version `{version}`')
                continue

            # Build the artifact
            with self.config.set_build_data(build_data):
                artifact = version_api[version](directory, **build_data)

            # Execute all `finalize` build hooks
            for build_hook in build_hooks:
                build_hook.finalize(version, build_data, artifact)

            if clean_hooks_after:
                for build_hook in build_hooks:
                    build_hook.clean([version])

            yield artifact

    def recurse_included_files(self) -> Generator[IncludedFile, None, None]:
        """
        Returns a consistently generated series of file objects for every file that should be distributed. Each file
        object has three `str` attributes:

        - `path` - the absolute path
        - `relative_path` - the path relative to the project root; will be an empty string for external files
        - `distribution_path` - the path to be distributed as
        """
        for project_file in self.recurse_project_files():
            yield project_file

        for explicit_file in self.recurse_explicit_files():
            yield explicit_file

    def recurse_project_files(self) -> Generator[IncludedFile, None, None]:
        for root, dirs, files in safe_walk(self.root):
            relative_path = os.path.relpath(root, self.root)

            # First iteration
            if relative_path == '.':
                relative_path = ''

            if self.config.skip_excluded_dirs:
                dirs[:] = sorted(
                    d
                    for d in dirs
                    # The trailing slash is necessary so e.g. `bar/` matches `foo/bar`
                    if not self.config.path_is_excluded(f'{os.path.join(relative_path, d)}/')
                )
            else:
                dirs.sort()

            files.sort()
            is_package = '__init__.py' in files
            for f in files:
                relative_file_path = os.path.join(relative_path, f)
                if self.config.include_path(relative_file_path, is_package=is_package):
                    yield IncludedFile(
                        os.path.join(root, f), relative_file_path, self.config.get_distribution_path(relative_file_path)
                    )

    def recurse_explicit_files(self, inclusion_map=None) -> Generator[IncludedFile, None, None]:
        if inclusion_map is None:
            inclusion_map = self.config.get_force_include()

        for source, target_path in inclusion_map.items():
            external = not source.startswith(self.root)
            if os.path.isfile(source):
                yield IncludedFile(source, '' if external else os.path.relpath(source, self.root), target_path)
            elif os.path.isdir(source):
                for root, dirs, files in safe_walk(source):
                    relative_path = os.path.relpath(root, source)

                    # First iteration
                    if relative_path == '.':
                        relative_path = ''

                    dirs.sort()
                    files.sort()

                    for f in files:
                        relative_file_path = os.path.join(relative_path, f)
                        yield IncludedFile(
                            os.path.join(root, f),
                            '' if external else os.path.relpath(relative_file_path, self.root),
                            os.path.join(target_path, relative_file_path),
                        )

    @property
    def root(self):
        """
        The root of the project tree.
        """
        return self.__root

    @property
    def plugin_manager(self):
        if self.__plugin_manager is None:
            from ...plugin.manager import PluginManager

            self.__plugin_manager = PluginManager()

        return self.__plugin_manager

    @property
    def metadata(self):
        if self.__metadata is None:
            from ...metadata.core import ProjectMetadata

            self.__metadata = ProjectMetadata(self.root, self.plugin_manager, self.__raw_config)

        return self.__metadata

    @property
    def app(self):
        """
        An instance of [Application](utilities.md#hatchling.bridge.app.Application).
        """
        if self.__app is None:
            from ...bridge.app import Application

            self.__app = Application().get_safe_application()

        return self.__app

    @property
    def raw_config(self):
        if self.__raw_config is None:
            self.__raw_config = self.metadata.config

        return self.__raw_config

    @property
    def project_config(self):
        if self.__project_config is None:
            self.__project_config = self.metadata.core.config

        return self.__project_config

    @property
    def hatch_config(self):
        if self.__hatch_config is None:
            self.__hatch_config = self.metadata.hatch.config

        return self.__hatch_config

    @property
    def config(self):
        """
        An instance of [BuilderConfig](utilities.md#hatchling.builders.config.BuilderConfig).
        """
        if self.__config is None:
            self.__config = self.get_config_class()(
                self, self.root, self.PLUGIN_NAME, self.build_config, self.target_config
            )

        return self.__config

    @property
    def build_config(self):
        """
        === ":octicons-file-code-16: pyproject.toml"

            ```toml
            [tool.hatch.build]
            ```

        === ":octicons-file-code-16: hatch.toml"

            ```toml
            [build]
            ```
        """
        if self.__build_config is None:
            self.__build_config = self.metadata.hatch.build_config

        return self.__build_config

    @property
    def target_config(self):
        """
        === ":octicons-file-code-16: pyproject.toml"

            ```toml
            [tool.hatch.build.targets.<PLUGIN_NAME>]
            ```

        === ":octicons-file-code-16: hatch.toml"

            ```toml
            [build.targets.<PLUGIN_NAME>]
            ```
        """
        if self.__target_config is None:
            target_config = self.metadata.hatch.build_targets.get(self.PLUGIN_NAME, {})
            if not isinstance(target_config, dict):
                raise TypeError(f'Field `tool.hatch.build.targets.{self.PLUGIN_NAME}` must be a table')

            self.__target_config = target_config

        return self.__target_config

    @property
    def project_id(self):
        if self.__project_id is None:
            # https://discuss.python.org/t/clarify-naming-of-dist-info-directories/5565
            self.__project_id = f'{self.normalize_file_name_component(self.metadata.core.name)}-{self.metadata.version}'

        return self.__project_id

    def get_build_hooks(self, directory):
        configured_build_hooks = OrderedDict()
        for hook_name, config in self.config.hook_config.items():
            build_hook = self.plugin_manager.build_hook.get(hook_name)
            if build_hook is None:
                from ...plugin.exceptions import UnknownPluginError

                raise UnknownPluginError(f'Unknown build hook: {hook_name}')

            configured_build_hooks[hook_name] = build_hook(
                self.root, config, self.config, self.metadata, directory, self.PLUGIN_NAME, self.app
            )

        return configured_build_hooks

    @abstractmethod
    def get_version_api(self) -> dict[str, Callable]:
        """
        A mapping of `str` versions to a callable that is used for building.
        Each callable must have the following signature:

        ```python
        def ...(build_dir: str, build_data: dict) -> str:
        ```

        The return value must be the absolute path to the built artifact.
        """

    def get_default_versions(self):
        """
        A list of versions to build when users do not specify any, defaulting to all versions.
        """
        return list(self.get_version_api())

    def get_default_build_data(self):
        """
        A mapping that can be modified by [build hooks](build-hook.md) to influence the behavior of builds.
        """
        return {}

    def clean(self, directory, versions):
        """
        Called before builds if the `-c`/`--clean` flag was passed to the
        [`build`](../cli/reference.md#hatch-build) command.
        """

    @classmethod
    def get_config_class(cls):
        """
        Must return a subclass of [BuilderConfig](utilities.md#hatchling.builders.config.BuilderConfig).
        """
        return BuilderConfig

    @staticmethod
    def normalize_file_name_component(file_name):
        """
        https://peps.python.org/pep-0427/#escaping-and-unicode
        """
        return re.sub(r'[^\w\d.]+', '_', file_name, re.UNICODE)
