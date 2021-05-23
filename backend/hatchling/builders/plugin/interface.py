import os
import re
from collections import OrderedDict
from contextlib import contextmanager
from io import open

import pathspec

from ...utils.fs import locate_file
from ..constants import DEFAULT_BUILD_DIRECTORY, BuildEnvVars


class IncludedFile(object):
    __slots__ = ('path', 'relative_path', 'distribution_path')

    def __init__(self, path, relative_path, distribution_path):
        self.path = path
        self.relative_path = relative_path
        self.distribution_path = distribution_path


class BuilderInterface(object):
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
        self.__config = config
        self.__metadata = metadata
        self.__app = app
        self.__project_config = None
        self.__hatch_config = None
        self.__build_config = None
        self.__build_targets = None
        self.__target_config = None
        self.__hook_config = None
        self.__packages = None
        self.__versions = None
        self.__dependencies = None

        # Possible pathspec.PathSpec
        self.__include_spec = None
        self.__exclude_spec = None
        self.__artifact_spec = None
        self.build_artifact_spec = None

        # These are used to create the pathspecs and will never be `None` after the first match attempt
        self.__include_patterns = None
        self.__exclude_patterns = None
        self.__artifact_patterns = None

        # Common options
        self.__directory = None
        self.__ignore_vcs = None
        self.__reproducible = None
        self.__dev_mode_dirs = None

        # Metadata
        self.__project_id = None

    def build(self, directory=None, versions=None, clean=None, hooks_only=None, no_hooks=None, clean_only=False):
        if directory is None:
            if BuildEnvVars.LOCATION in os.environ:
                directory = self._normalize_build_directory(os.environ[BuildEnvVars.LOCATION])
            else:
                directory = self.directory

        if not os.path.isdir(directory):
            os.makedirs(directory)

        version_api = self.get_version_api()

        if not versions:
            versions = self.versions
        else:
            unknown_versions = set(versions) - set(version_api)
            if unknown_versions:
                raise ValueError(
                    'Unknown versions for target `{}`: {}'.format(
                        self.PLUGIN_NAME, ', '.join(map(str, sorted(unknown_versions)))
                    )
                )

        if hooks_only is None:
            hooks_only = _env_var_enabled(BuildEnvVars.HOOKS_ONLY)

        if no_hooks is None:
            no_hooks = _env_var_enabled(BuildEnvVars.NO_HOOKS)
        if no_hooks:
            configured_build_hooks = OrderedDict()
        else:
            configured_build_hooks = self.get_build_hooks(directory)

        build_hooks = list(configured_build_hooks.values())

        if clean_only:
            clean = True
        elif clean is None:
            clean = _env_var_enabled(BuildEnvVars.CLEAN)
        if clean:
            if not hooks_only:
                self.clean(directory, versions)
            if not no_hooks:
                for build_hook in build_hooks:
                    build_hook.clean(versions)

            if clean_only:
                return

        for version in versions:
            self.app.display_debug('Building `{}` version `{}`'.format(self.PLUGIN_NAME, version))

            build_data = self.get_default_build_data()

            # Make sure reserved fields are set
            build_data.setdefault('artifacts', [])

            # Pass all the configured build hooks for future unforeseen scenarios needing ultimate control
            build_data['configured_build_hooks'] = configured_build_hooks

            # Execute all `initialize` build hooks
            for build_hook in build_hooks:
                build_hook.initialize(version, build_data)

            if hooks_only:
                self.app.display_debug('Only ran build hooks for `{}` version `{}`'.format(self.PLUGIN_NAME, version))
                continue

            # Build the artifact
            with self.configure_with_build_data(build_data):
                artifact = version_api[version](directory, **build_data)

            # Execute all `finalize` build hooks
            for build_hook in build_hooks:
                build_hook.finalize(version, build_data, artifact)

            yield artifact

    def recurse_project_files(self):
        """
        Returns a consistently generated series of file objects for every file that should be distributed. Each file
        object has three `str` attributes:

        - `path` - the absolute path
        - `relative_path` - the path relative to the project root
        - `distribution_path` - the path to be distributed as
        """
        for root, dirs, files in os.walk(self.root):
            relative_path = os.path.relpath(root, self.root)

            # First iteration
            if relative_path == '.':
                relative_path = ''

            dirs[:] = sorted(
                d
                for d in dirs
                if not (
                    self.ignore_directory(d)
                    # The trailing slash is necessary so e.g. `bar/` matches `foo/bar`
                    or self.path_is_excluded('{}/'.format(os.path.join(relative_path, d)))
                )
            )

            if self.ignore_files(files):
                continue

            for f in sorted(files):
                relative_file_path = os.path.join(relative_path, f)
                if self.include_path(relative_file_path):
                    yield IncludedFile(
                        os.path.join(root, f), relative_file_path, self.get_distribution_path(relative_file_path)
                    )

    def include_path(self, relative_path):
        return (
            self.path_is_build_artifact(relative_path)
            or self.path_is_artifact(relative_path)
            or (self.path_is_included(relative_path) and not self.path_is_excluded(relative_path))
        )

    def path_is_included(self, relative_path):
        if self.include_spec is None:
            return True

        return self.include_spec.match_file(relative_path)

    def path_is_excluded(self, relative_path):
        if self.exclude_spec is None:
            return False

        return self.exclude_spec.match_file(relative_path)

    def path_is_artifact(self, relative_path):
        if self.artifact_spec is None:
            return False

        return self.artifact_spec.match_file(relative_path)

    def path_is_build_artifact(self, relative_path):
        if self.build_artifact_spec is None:
            return False

        return self.build_artifact_spec.match_file(relative_path)

    @property
    def include_spec(self):
        if self.__include_patterns is None:
            if 'include' in self.target_config:
                include_config = self.target_config
                include_location = 'tool.hatch.build.targets.{}.include'.format(self.PLUGIN_NAME)
            else:
                include_config = self.build_config
                include_location = 'tool.hatch.build.include'

            all_include_patterns = []

            include_patterns = include_config.get('include', self.default_include_patterns())
            if isinstance(include_patterns, str):
                for include_pattern in include_patterns.split(','):
                    if include_pattern:
                        all_include_patterns.append(include_pattern)
            elif isinstance(include_patterns, list):
                for i, include_pattern in enumerate(include_patterns, 1):
                    if not isinstance(include_pattern, str):
                        raise TypeError('Pattern #{} in field `{}` must be a string'.format(i, include_location))

                    if include_pattern:
                        all_include_patterns.append(include_pattern)
            else:
                raise TypeError(
                    'Field `{}` must be a comma-separated string or an array of strings'.format(include_location)
                )

            for relative_path, _ in self.packages:
                # Matching only at the root requires a forward slash, back slashes do not work. As such,
                # normalize to forward slashes for consistency.
                all_include_patterns.append('/{}'.format(relative_path.replace(os.path.sep, '/')))

            if all_include_patterns:
                self.__include_spec = pathspec.PathSpec.from_lines(
                    pathspec.patterns.GitWildMatchPattern, all_include_patterns
                )

            self.__include_patterns = all_include_patterns

        return self.__include_spec

    @property
    def exclude_spec(self):
        if self.__exclude_patterns is None:
            if 'exclude' in self.target_config:
                exclude_config = self.target_config
                exclude_location = 'tool.hatch.build.targets.{}.exclude'.format(self.PLUGIN_NAME)
            else:
                exclude_config = self.build_config
                exclude_location = 'tool.hatch.build.exclude'

            all_exclude_patterns = self.default_global_exclude_patterns()

            exclude_patterns = exclude_config.get('exclude', self.default_exclude_patterns())
            if isinstance(exclude_patterns, str):
                for exclude_pattern in exclude_patterns.split(','):
                    if exclude_pattern:
                        all_exclude_patterns.append(exclude_pattern)
            elif isinstance(exclude_patterns, list):
                for i, exclude_pattern in enumerate(exclude_patterns, 1):
                    if not isinstance(exclude_pattern, str):
                        raise TypeError('Pattern #{} in field `{}` must be a string'.format(i, exclude_location))

                    if exclude_pattern:
                        all_exclude_patterns.append(exclude_pattern)
            else:
                raise TypeError(
                    'Field `{}` must be a comma-separated string or an array of strings'.format(exclude_location)
                )

            if not self.ignore_vcs:
                all_exclude_patterns.extend(self.load_vcs_ignore_patterns())

            if all_exclude_patterns:
                self.__exclude_spec = pathspec.PathSpec.from_lines(
                    pathspec.patterns.GitWildMatchPattern, all_exclude_patterns
                )

            self.__exclude_patterns = all_exclude_patterns

        return self.__exclude_spec

    @property
    def artifact_spec(self):
        if self.__artifact_patterns is None:
            if 'artifacts' in self.target_config:
                artifact_config = self.target_config
                artifact_location = 'tool.hatch.build.targets.{}.artifacts'.format(self.PLUGIN_NAME)
            else:
                artifact_config = self.build_config
                artifact_location = 'tool.hatch.build.artifacts'

            all_artifact_patterns = []

            artifact_patterns = artifact_config.get('artifacts', [])
            if isinstance(artifact_patterns, str):
                for artifact_pattern in artifact_patterns.split(','):
                    if artifact_pattern:
                        all_artifact_patterns.append(artifact_pattern)
            elif isinstance(artifact_patterns, list):
                for i, artifact_pattern in enumerate(artifact_patterns, 1):
                    if not isinstance(artifact_pattern, str):
                        raise TypeError('Pattern #{} in field `{}` must be a string'.format(i, artifact_location))

                    if artifact_pattern:
                        all_artifact_patterns.append(artifact_pattern)
            else:
                raise TypeError(
                    'Field `{}` must be a comma-separated string or an array of strings'.format(artifact_location)
                )

            if all_artifact_patterns:
                self.__artifact_spec = pathspec.PathSpec.from_lines(
                    pathspec.patterns.GitWildMatchPattern, all_artifact_patterns
                )

            self.__artifact_patterns = all_artifact_patterns

        return self.__artifact_spec

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

            self.__metadata = ProjectMetadata(self.root, self.plugin_manager, self.__config)

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
    def config(self):
        if self.__config is None:
            self.__config = self.metadata.config

        return self.__config

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
                raise TypeError('Field `tool.hatch.build.targets.{}` must be a table'.format(self.PLUGIN_NAME))

            self.__target_config = target_config

        return self.__target_config

    @property
    def hook_config(self):
        if self.__hook_config is None:
            hook_config = OrderedDict()

            target_hook_config = self.target_config.get('hooks', {})
            if not isinstance(target_hook_config, dict):
                raise TypeError('Field `tool.hatch.build.targets.{}.hooks` must be a table'.format(self.PLUGIN_NAME))

            for hook_name, config in target_hook_config.items():
                if not isinstance(config, dict):
                    raise TypeError(
                        'Field `tool.hatch.build.targets.{}.hooks.{}` must be a table'.format(
                            self.PLUGIN_NAME, hook_name
                        )
                    )

                hook_config[hook_name] = config

            global_hook_config = self.build_config.get('hooks', {})
            if not isinstance(global_hook_config, dict):
                raise TypeError('Field `tool.hatch.build.hooks` must be a table')

            for hook_name, config in global_hook_config.items():
                if not isinstance(config, dict):
                    raise TypeError('Field `tool.hatch.build.hooks.{}` must be a table'.format(hook_name))

                hook_config.setdefault(hook_name, config)

            self.__hook_config = hook_config

        return self.__hook_config

    @property
    def directory(self):
        if self.__directory is None:
            if 'directory' in self.target_config:
                directory = self.target_config['directory']
                if not isinstance(directory, str):
                    raise TypeError(
                        'Field `tool.hatch.build.targets.{}.directory` must be a string'.format(self.PLUGIN_NAME)
                    )
            else:
                directory = self.build_config.get('directory', DEFAULT_BUILD_DIRECTORY)
                if not isinstance(directory, str):
                    raise TypeError('Field `tool.hatch.build.directory` must be a string')

            self.__directory = self._normalize_build_directory(directory)

        return self.__directory

    @property
    def ignore_vcs(self):
        if self.__ignore_vcs is None:
            if 'ignore-vcs' in self.target_config:
                ignore_vcs = self.target_config['ignore-vcs']
                if not isinstance(ignore_vcs, bool):
                    raise TypeError(
                        'Field `tool.hatch.build.targets.{}.ignore-vcs` must be a boolean'.format(self.PLUGIN_NAME)
                    )
            else:
                ignore_vcs = self.build_config.get('ignore-vcs', False)
                if not isinstance(ignore_vcs, bool):
                    raise TypeError('Field `tool.hatch.build.ignore-vcs` must be a boolean')

            self.__ignore_vcs = ignore_vcs

        return self.__ignore_vcs

    @property
    def reproducible(self):
        """
        Whether or not the target should be built in a reproducible manner, defaulting to true.
        """
        if self.__reproducible is None:
            if 'reproducible' in self.target_config:
                reproducible = self.target_config['reproducible']
                if not isinstance(reproducible, bool):
                    raise TypeError(
                        'Field `tool.hatch.build.targets.{}.reproducible` must be a boolean'.format(self.PLUGIN_NAME)
                    )
            else:
                reproducible = self.build_config.get('reproducible', True)
                if not isinstance(reproducible, bool):
                    raise TypeError('Field `tool.hatch.build.reproducible` must be a boolean')

            self.__reproducible = reproducible

        return self.__reproducible

    @property
    def dev_mode_dirs(self):
        """
        Directories which must be added to Python's search path in [dev mode](../config/environment.md#dev-mode).
        """
        if self.__dev_mode_dirs is None:
            if 'dev-mode-dirs' in self.target_config:
                dev_mode_dirs_config = self.target_config
                dev_mode_dirs_location = 'tool.hatch.build.targets.{}.dev-mode-dirs'.format(self.PLUGIN_NAME)
            else:
                dev_mode_dirs_config = self.build_config
                dev_mode_dirs_location = 'tool.hatch.build.dev-mode-dirs'

            all_dev_mode_dirs = []

            dev_mode_dirs = dev_mode_dirs_config.get('dev-mode-dirs', [])
            if isinstance(dev_mode_dirs, str):
                for dev_mode_dir in dev_mode_dirs.split(','):
                    if dev_mode_dir:
                        all_dev_mode_dirs.append(dev_mode_dir)
            elif isinstance(dev_mode_dirs, list):
                for i, dev_mode_dir in enumerate(dev_mode_dirs, 1):
                    if not isinstance(dev_mode_dir, str):
                        raise TypeError(
                            'Directory #{} in field `{}` must be a string'.format(i, dev_mode_dirs_location)
                        )

                    if dev_mode_dir:
                        all_dev_mode_dirs.append(dev_mode_dir)
            else:
                raise TypeError(
                    'Field `{}` must be a comma-separated string or an array of strings'.format(dev_mode_dirs_location)
                )

            self.__dev_mode_dirs = all_dev_mode_dirs

        return self.__dev_mode_dirs

    @property
    def packages(self):
        if self.__packages is None:
            if 'packages' in self.target_config:
                package_config = self.target_config
                package_location = 'tool.hatch.build.targets.{}.packages'.format(self.PLUGIN_NAME)
            else:
                package_config = self.build_config
                package_location = 'tool.hatch.build.packages'

            all_packages = set()

            packages = package_config.get('packages', [])
            if isinstance(packages, str):
                for package in packages.split(','):
                    if package:
                        all_packages.add(os.path.normpath(package).lstrip(os.path.sep))
            elif isinstance(packages, list):
                for i, package in enumerate(packages, 1):
                    if not isinstance(package, str):
                        raise TypeError('Package #{} in field `{}` must be a string'.format(i, package_location))

                    if package:
                        all_packages.add(os.path.normpath(package).lstrip(os.path.sep))
            else:
                raise TypeError(
                    'Field `{}` must be a comma-separated string or an array of strings'.format(package_location)
                )

            unique_packages = {}
            package_data = []

            for relative_path in sorted(all_packages):
                source, package = os.path.split(relative_path)
                if package in unique_packages:
                    raise ValueError(
                        'Package `{}` of field `{}` is already defined by path `{}`'.format(
                            package, package_location, unique_packages[package]
                        )
                    )

                unique_packages[package] = relative_path

                if source:
                    package_data.append((relative_path + os.path.sep, lambda path: path[len(source) + 1 :]))
                else:
                    package_data.append((relative_path + os.path.sep, lambda path: path))

            self.__packages = package_data

        return self.__packages

    @property
    def versions(self):
        if self.__versions is None:
            # Used as an ordered set
            all_versions = OrderedDict()

            versions = self.target_config.get('versions', [])
            if isinstance(versions, str):
                for version in versions.split(','):
                    if version:
                        all_versions[version] = None
            elif isinstance(versions, list):
                for i, version in enumerate(versions, 1):
                    if not isinstance(version, str):
                        raise TypeError(
                            'Version #{} in field `tool.hatch.build.targets.{}.versions` must be a string'.format(
                                i, self.PLUGIN_NAME
                            )
                        )

                    if version:
                        all_versions[version] = None
            else:
                raise TypeError(
                    'Field `tool.hatch.build.targets.{}.versions` must be a comma-separated '
                    'string or an array of strings'.format(self.PLUGIN_NAME)
                )

            if not all_versions:
                default_versions = self.get_default_versions()
                for version in default_versions:
                    all_versions[version] = None
            else:
                unknown_versions = set(all_versions) - set(self.get_version_api())
                if unknown_versions:
                    raise ValueError(
                        'Unknown versions in field `tool.hatch.build.targets.{}.versions`: {}'.format(
                            self.PLUGIN_NAME, ', '.join(map(str, sorted(unknown_versions)))
                        )
                    )

            self.__versions = list(all_versions)

        return self.__versions

    @property
    def dependencies(self):
        if self.__dependencies is None:
            # Used as an ordered set
            dependencies = OrderedDict()

            target_dependencies = self.target_config.get('dependencies', [])
            if not isinstance(target_dependencies, list):
                raise TypeError(
                    'Field `tool.hatch.build.targets.{}.dependencies` must be an array'.format(self.PLUGIN_NAME)
                )

            for i, dependency in enumerate(target_dependencies, 1):
                if not isinstance(dependency, str):
                    raise TypeError(
                        'Dependency #{} of field `tool.hatch.build.targets.{}.dependencies` must be a string'.format(
                            i, self.PLUGIN_NAME
                        )
                    )

                dependencies[dependency] = None

            global_dependencies = self.build_config.get('dependencies', [])
            if not isinstance(global_dependencies, list):
                raise TypeError('Field `tool.hatch.build.dependencies` must be an array')

            for i, dependency in enumerate(global_dependencies, 1):
                if not isinstance(dependency, str):
                    raise TypeError(
                        'Dependency #{} of field `tool.hatch.build.dependencies` must be a string'.format(i)
                    )

                dependencies[dependency] = None

            for hook_name, config in self.hook_config.items():
                hook_dependencies = config.get('dependencies', [])
                if not isinstance(hook_dependencies, list):
                    raise TypeError('Option `dependencies` of build hook `{}` must be an array'.format(hook_name))

                for i, dependency in enumerate(hook_dependencies, 1):
                    if not isinstance(dependency, str):
                        raise TypeError(
                            'Dependency #{} of option `dependencies` of build hook `{}` must be a string'.format(
                                i, hook_name
                            )
                        )

                    dependencies[dependency] = None

            self.__dependencies = list(dependencies)

        return self.__dependencies

    @property
    def project_id(self):
        if self.__project_id is None:
            self.__project_id = '{}-{}'.format(
                # https://discuss.python.org/t/clarify-naming-of-dist-info-directories/5565
                self.normalize_file_name_component(self.metadata.core.name),
                self.metadata.version,
            )

        return self.__project_id

    def get_build_hooks(self, directory):
        hook_config = self.hook_config

        configured_build_hooks = OrderedDict()
        for hook_name, config in hook_config.items():
            build_hook = self.plugin_manager.build_hook.get(hook_name)
            if build_hook is None:
                raise ValueError('Unknown build hook: {}'.format(hook_name))

            configured_build_hooks[hook_name] = build_hook(self.root, config, directory, self.PLUGIN_NAME, self.app)

        return configured_build_hooks

    def get_distribution_path(self, relative_path):
        # src/foo/bar.py -> foo/bar.py
        for package_relative_path, formatter in self.packages:
            if relative_path.startswith(package_relative_path):
                return formatter(relative_path)

        return relative_path

    def load_vcs_ignore_patterns(self):
        # https://git-scm.com/docs/gitignore#_pattern_format
        default_exclusion_file = locate_file(self.root, '.gitignore')
        if default_exclusion_file is None:
            return []

        with open(default_exclusion_file, 'r', encoding='utf-8') as f:
            return f.readlines()

    def default_include_patterns(self):
        return []

    def default_exclude_patterns(self):
        return []

    def default_global_exclude_patterns(self):
        return ['.git']

    def ignore_directory(self, directory):
        # A hack used by WheelBuilder to ignore any test directories when no inclusion patterns are provided.
        return False

    def ignore_files(self, files):
        # A hack used by WheelBuilder to ignore any non-package directory when no inclusion patterns are provided.
        return False

    def get_version_api(self):
        """
        :material-align-horizontal-left: **REQUIRED** :material-align-horizontal-right:

        A mapping of `str` versions to a callable that is used for building.
        Each callable must have the following signature:

        ```python
        def ...(build_dir: str, build_data: dict) -> str:
        ```

        The return value must be the absolute path to the built artifact.
        """
        raise NotImplementedError

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

    @contextmanager
    def configure_with_build_data(self, build_data):
        try:
            # Include anything the hooks indicate
            build_artifacts = build_data['artifacts']
            if build_artifacts:
                self.build_artifact_spec = pathspec.PathSpec.from_lines(
                    pathspec.patterns.GitWildMatchPattern, build_artifacts
                )

            yield
        finally:
            self.build_artifact_spec = None

    def _normalize_build_directory(self, build_directory):
        if not os.path.isabs(build_directory):
            build_directory = os.path.join(self.root, build_directory)

        return os.path.normpath(build_directory)

    @staticmethod
    def normalize_file_name_component(file_name):
        """
        https://www.python.org/dev/peps/pep-0427/#escaping-and-unicode
        """
        return re.sub(r'[^\w\d.]+', '_', file_name, re.UNICODE)


def _env_var_enabled(env_var, default=False):
    if env_var in os.environ:
        return os.environ[env_var] in ('1', 'true')
    else:
        return default
