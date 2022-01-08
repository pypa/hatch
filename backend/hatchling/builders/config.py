import os
from collections import OrderedDict
from contextlib import contextmanager
from io import open

import pathspec

from ..utils.fs import locate_file
from .constants import DEFAULT_BUILD_DIRECTORY, BuildEnvVars


class BuilderConfig(object):
    def __init__(self, builder, root, plugin_name, build_config, target_config):
        self.__builder = builder
        self.__root = root
        self.__plugin_name = plugin_name
        self.__build_config = build_config
        self.__target_config = target_config
        self.__hook_config = None
        self.__versions = None
        self.__dependencies = None
        self.__packages = None
        self.__package_sources = None

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

    @property
    def builder(self):
        return self.__builder

    @property
    def root(self):
        return self.__root

    @property
    def plugin_name(self):
        return self.__plugin_name

    @property
    def build_config(self):
        return self.__build_config

    @property
    def target_config(self):
        return self.__target_config

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
                include_location = 'tool.hatch.build.targets.{}.include'.format(self.plugin_name)
            else:
                include_config = self.build_config
                include_location = 'tool.hatch.build.include'

            all_include_patterns = []

            include_patterns = include_config.get('include', self.default_include())
            if not isinstance(include_patterns, list):
                raise TypeError('Field `{}` must be an array of strings'.format(include_location))

            for i, include_pattern in enumerate(include_patterns, 1):
                if not isinstance(include_pattern, str):
                    raise TypeError('Pattern #{} in field `{}` must be a string'.format(i, include_location))
                elif not include_pattern:
                    raise ValueError('Pattern #{} in field `{}` cannot be an empty string'.format(i, include_location))

                all_include_patterns.append(include_pattern)

            for relative_path in self.packages:
                # Matching only at the root requires a forward slash, back slashes do not work. As such,
                # normalize to forward slashes for consistency.
                all_include_patterns.append('/{}/'.format(relative_path.replace(os.path.sep, '/')))

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
                exclude_location = 'tool.hatch.build.targets.{}.exclude'.format(self.plugin_name)
            else:
                exclude_config = self.build_config
                exclude_location = 'tool.hatch.build.exclude'

            all_exclude_patterns = self.default_global_exclude()

            exclude_patterns = exclude_config.get('exclude', self.default_exclude())
            if not isinstance(exclude_patterns, list):
                raise TypeError('Field `{}` must be an array of strings'.format(exclude_location))

            for i, exclude_pattern in enumerate(exclude_patterns, 1):
                if not isinstance(exclude_pattern, str):
                    raise TypeError('Pattern #{} in field `{}` must be a string'.format(i, exclude_location))
                elif not exclude_pattern:
                    raise ValueError('Pattern #{} in field `{}` cannot be an empty string'.format(i, exclude_location))

                all_exclude_patterns.append(exclude_pattern)

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
                artifact_location = 'tool.hatch.build.targets.{}.artifacts'.format(self.plugin_name)
            else:
                artifact_config = self.build_config
                artifact_location = 'tool.hatch.build.artifacts'

            all_artifact_patterns = []

            artifact_patterns = artifact_config.get('artifacts', [])
            if not isinstance(artifact_patterns, list):
                raise TypeError('Field `{}` must be an array of strings'.format(artifact_location))

            for i, artifact_pattern in enumerate(artifact_patterns, 1):
                if not isinstance(artifact_pattern, str):
                    raise TypeError('Pattern #{} in field `{}` must be a string'.format(i, artifact_location))
                elif not artifact_pattern:
                    raise ValueError('Pattern #{} in field `{}` cannot be an empty string'.format(i, artifact_location))

                all_artifact_patterns.append(artifact_pattern)

            if all_artifact_patterns:
                self.__artifact_spec = pathspec.PathSpec.from_lines(
                    pathspec.patterns.GitWildMatchPattern, all_artifact_patterns
                )

            self.__artifact_patterns = all_artifact_patterns

        return self.__artifact_spec

    @property
    def hook_config(self):
        if self.__hook_config is None:
            hook_config = OrderedDict()

            target_hook_config = self.target_config.get('hooks', {})
            if not isinstance(target_hook_config, dict):
                raise TypeError('Field `tool.hatch.build.targets.{}.hooks` must be a table'.format(self.plugin_name))

            for hook_name, config in target_hook_config.items():
                if not isinstance(config, dict):
                    raise TypeError(
                        'Field `tool.hatch.build.targets.{}.hooks.{}` must be a table'.format(
                            self.plugin_name, hook_name
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

            final_hook_config = OrderedDict()
            if not env_var_enabled(BuildEnvVars.NO_HOOKS):
                all_hooks_enabled = env_var_enabled(BuildEnvVars.HOOKS_ENABLE)
                for hook_name, config in hook_config.items():
                    if (
                        all_hooks_enabled
                        or config.get('enable-by-default', True)
                        or env_var_enabled('{}{}'.format(BuildEnvVars.HOOK_ENABLE_PREFIX, hook_name.upper()))
                    ):
                        final_hook_config[hook_name] = config

            self.__hook_config = final_hook_config

        return self.__hook_config

    @property
    def directory(self):
        if self.__directory is None:
            if 'directory' in self.target_config:
                directory = self.target_config['directory']
                if not isinstance(directory, str):
                    raise TypeError(
                        'Field `tool.hatch.build.targets.{}.directory` must be a string'.format(self.plugin_name)
                    )
            else:
                directory = self.build_config.get('directory', DEFAULT_BUILD_DIRECTORY)
                if not isinstance(directory, str):
                    raise TypeError('Field `tool.hatch.build.directory` must be a string')

            self.__directory = self.normalize_build_directory(directory)

        return self.__directory

    @property
    def ignore_vcs(self):
        if self.__ignore_vcs is None:
            if 'ignore-vcs' in self.target_config:
                ignore_vcs = self.target_config['ignore-vcs']
                if not isinstance(ignore_vcs, bool):
                    raise TypeError(
                        'Field `tool.hatch.build.targets.{}.ignore-vcs` must be a boolean'.format(self.plugin_name)
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
                        'Field `tool.hatch.build.targets.{}.reproducible` must be a boolean'.format(self.plugin_name)
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
                dev_mode_dirs_location = 'tool.hatch.build.targets.{}.dev-mode-dirs'.format(self.plugin_name)
            else:
                dev_mode_dirs_config = self.build_config
                dev_mode_dirs_location = 'tool.hatch.build.dev-mode-dirs'

            all_dev_mode_dirs = []

            dev_mode_dirs = dev_mode_dirs_config.get('dev-mode-dirs', [])
            if not isinstance(dev_mode_dirs, list):
                raise TypeError('Field `{}` must be an array of strings'.format(dev_mode_dirs_location))

            for i, dev_mode_dir in enumerate(dev_mode_dirs, 1):
                if not isinstance(dev_mode_dir, str):
                    raise TypeError('Directory #{} in field `{}` must be a string'.format(i, dev_mode_dirs_location))
                elif not dev_mode_dir:
                    raise ValueError(
                        'Directory #{} in field `{}` cannot be an empty string'.format(i, dev_mode_dirs_location)
                    )

                all_dev_mode_dirs.append(dev_mode_dir)

            self.__dev_mode_dirs = all_dev_mode_dirs

        return self.__dev_mode_dirs

    @property
    def versions(self):
        if self.__versions is None:
            # Used as an ordered set
            all_versions = OrderedDict()

            versions = self.target_config.get('versions', [])
            if not isinstance(versions, list):
                raise TypeError(
                    'Field `tool.hatch.build.targets.{}.versions` must be an array of strings'.format(self.plugin_name)
                )

            for i, version in enumerate(versions, 1):
                if not isinstance(version, str):
                    raise TypeError(
                        'Version #{} in field `tool.hatch.build.targets.{}.versions` must be a string'.format(
                            i, self.plugin_name
                        )
                    )
                elif not version:
                    raise ValueError(
                        'Version #{} in field `tool.hatch.build.targets.{}.versions` cannot be an empty string'.format(
                            i, self.plugin_name
                        )
                    )

                all_versions[version] = None

            if not all_versions:
                default_versions = self.__builder.get_default_versions()
                for version in default_versions:
                    all_versions[version] = None
            else:
                unknown_versions = set(all_versions) - set(self.__builder.get_version_api())
                if unknown_versions:
                    raise ValueError(
                        'Unknown versions in field `tool.hatch.build.targets.{}.versions`: {}'.format(
                            self.plugin_name, ', '.join(map(str, sorted(unknown_versions)))
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
                    'Field `tool.hatch.build.targets.{}.dependencies` must be an array'.format(self.plugin_name)
                )

            for i, dependency in enumerate(target_dependencies, 1):
                if not isinstance(dependency, str):
                    raise TypeError(
                        'Dependency #{} of field `tool.hatch.build.targets.{}.dependencies` must be a string'.format(
                            i, self.plugin_name
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
    def packages(self):
        if self.__packages is None:
            if 'packages' in self.target_config:
                package_config = self.target_config
                package_location = 'tool.hatch.build.targets.{}.packages'.format(self.plugin_name)
            else:
                package_config = self.build_config
                package_location = 'tool.hatch.build.packages'

            all_packages = set()

            packages = package_config.get('packages', self.default_packages())
            if not isinstance(packages, list):
                raise TypeError('Field `{}` must be an array of strings'.format(package_location))

            for i, package in enumerate(packages, 1):
                if not isinstance(package, str):
                    raise TypeError('Package #{} in field `{}` must be a string'.format(i, package_location))
                elif not package:
                    raise ValueError('Package #{} in field `{}` cannot be an empty string'.format(i, package_location))

                all_packages.add(os.path.normpath(package).lstrip(os.path.sep))

            unique_packages = {}
            packages = []
            package_sources = []

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
                    package_sources.append(source + os.path.sep)

                packages.append(relative_path)

            self.__packages = packages
            self.__package_sources = package_sources

        return self.__packages

    @property
    def package_sources(self):
        if self.__package_sources is None:
            _ = self.packages

        return self.__package_sources

    def get_distribution_path(self, relative_path):
        # src/foo/bar.py -> foo/bar.py
        for package_source in self.package_sources:
            if relative_path.startswith(package_source):
                return relative_path[len(package_source) :]

        return relative_path

    def load_vcs_ignore_patterns(self):
        # https://git-scm.com/docs/gitignore#_pattern_format
        default_exclusion_file = locate_file(self.root, '.gitignore')
        if default_exclusion_file is None:
            return []

        with open(default_exclusion_file, 'r', encoding='utf-8') as f:
            return f.readlines()

    def normalize_build_directory(self, build_directory):
        if not os.path.isabs(build_directory):
            build_directory = os.path.join(self.root, build_directory)

        return os.path.normpath(build_directory)

    def default_include(self):
        return []

    def default_exclude(self):
        return []

    def default_packages(self):
        return []

    def default_global_exclude(self):
        return ['.git']

    @contextmanager
    def set_build_data(self, build_data):
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


def env_var_enabled(env_var, default=False):
    if env_var in os.environ:
        return os.environ[env_var] in ('1', 'true')
    else:
        return default
