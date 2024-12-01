from __future__ import annotations

import os
from contextlib import contextmanager
from functools import cached_property
from typing import TYPE_CHECKING, Any, Generator, TypeVar

import pathspec

from hatchling.builders.constants import DEFAULT_BUILD_DIRECTORY, EXCLUDED_DIRECTORIES, BuildEnvVars
from hatchling.builders.utils import normalize_inclusion_map, normalize_relative_directory, normalize_relative_path
from hatchling.metadata.utils import normalize_project_name
from hatchling.utils.fs import locate_file

if TYPE_CHECKING:
    from hatchling.builders.plugin.interface import BuilderInterface


class BuilderConfig:
    def __init__(
        self,
        builder: BuilderInterface,
        root: str,
        plugin_name: str,
        build_config: dict[str, Any],
        target_config: dict[str, Any],
    ) -> None:
        self.__builder = builder
        self.__root = root
        self.__plugin_name = plugin_name
        self.__build_config = build_config
        self.__target_config = target_config

        # This is used when the only file selection is based on forced inclusion or build-time artifacts. This
        # instructs to `exclude` every encountered path without doing pattern matching that matches everything.
        self.__exclude_all: bool = False

        # Modified at build time
        self.build_artifact_spec: pathspec.GitIgnoreSpec | None = None
        self.build_force_include: dict[str, str] = {}
        self.build_reserved_paths: set[str] = set()

    @property
    def builder(self) -> BuilderInterface:
        return self.__builder

    @property
    def root(self) -> str:
        return self.__root

    @property
    def plugin_name(self) -> str:
        return self.__plugin_name

    @property
    def build_config(self) -> dict[str, Any]:
        return self.__build_config

    @property
    def target_config(self) -> dict[str, Any]:
        return self.__target_config

    def include_path(self, relative_path: str, *, explicit: bool = False, is_package: bool = True) -> bool:
        return (
            self.path_is_build_artifact(relative_path)
            or self.path_is_artifact(relative_path)
            or (
                not (self.only_packages and not is_package)
                and not self.path_is_excluded(relative_path)
                and (explicit or self.path_is_included(relative_path))
            )
        )

    def path_is_included(self, relative_path: str) -> bool:
        if self.include_spec is None:
            return True

        return self.include_spec.match_file(relative_path)

    def path_is_excluded(self, relative_path: str) -> bool:
        if self.__exclude_all:
            return True

        if self.exclude_spec is None:
            return False

        return self.exclude_spec.match_file(relative_path)

    def path_is_artifact(self, relative_path: str) -> bool:
        if self.artifact_spec is None:
            return False

        return self.artifact_spec.match_file(relative_path)

    def path_is_build_artifact(self, relative_path: str) -> bool:
        if self.build_artifact_spec is None:
            return False

        return self.build_artifact_spec.match_file(relative_path)

    def path_is_reserved(self, relative_path: str) -> bool:
        return relative_path in self.build_reserved_paths

    def directory_is_excluded(self, name: str, relative_path: str) -> bool:
        if name in EXCLUDED_DIRECTORIES:
            return True

        relative_directory = os.path.join(relative_path, name)
        return (
            self.path_is_reserved(relative_directory)
            # The trailing slash is necessary so e.g. `bar/` matches `foo/bar`
            or (self.skip_excluded_dirs and self.path_is_excluded(f'{relative_directory}/'))
        )

    @cached_property
    def include_spec(self) -> pathspec.GitIgnoreSpec | None:
        if 'include' in self.target_config:
            include_config = self.target_config
            include_location = f'tool.hatch.build.targets.{self.plugin_name}.include'
        else:
            include_config = self.build_config
            include_location = 'tool.hatch.build.include'

        all_include_patterns = []

        include_patterns = include_config.get('include', self.default_include())
        if not isinstance(include_patterns, list):
            message = f'Field `{include_location}` must be an array of strings'
            raise TypeError(message)

        for i, include_pattern in enumerate(include_patterns, 1):
            if not isinstance(include_pattern, str):
                message = f'Pattern #{i} in field `{include_location}` must be a string'
                raise TypeError(message)

            if not include_pattern:
                message = f'Pattern #{i} in field `{include_location}` cannot be an empty string'
                raise ValueError(message)

            all_include_patterns.append(include_pattern)

        # Matching only at the root requires a forward slash, back slashes do not work. As such,
        # normalize to forward slashes for consistency.
        all_include_patterns.extend(f"/{relative_path.replace(os.sep, '/')}/" for relative_path in self.packages)

        if all_include_patterns:
            return pathspec.GitIgnoreSpec.from_lines(all_include_patterns)
        return None

    @cached_property
    def exclude_spec(self) -> pathspec.GitIgnoreSpec | None:
        if 'exclude' in self.target_config:
            exclude_config = self.target_config
            exclude_location = f'tool.hatch.build.targets.{self.plugin_name}.exclude'
        else:
            exclude_config = self.build_config
            exclude_location = 'tool.hatch.build.exclude'

        all_exclude_patterns = self.default_global_exclude()

        if not self.ignore_vcs:
            all_exclude_patterns.extend(self.load_vcs_exclusion_patterns())

        exclude_patterns = exclude_config.get('exclude', self.default_exclude())
        if not isinstance(exclude_patterns, list):
            message = f'Field `{exclude_location}` must be an array of strings'
            raise TypeError(message)

        for i, exclude_pattern in enumerate(exclude_patterns, 1):
            if not isinstance(exclude_pattern, str):
                message = f'Pattern #{i} in field `{exclude_location}` must be a string'
                raise TypeError(message)

            if not exclude_pattern:
                message = f'Pattern #{i} in field `{exclude_location}` cannot be an empty string'
                raise ValueError(message)

            all_exclude_patterns.append(exclude_pattern)

        if all_exclude_patterns:
            return pathspec.GitIgnoreSpec.from_lines(all_exclude_patterns)
        return None

    @property
    def artifact_spec(self) -> pathspec.GitIgnoreSpec | None:
        if 'artifacts' in self.target_config:
            artifact_config = self.target_config
            artifact_location = f'tool.hatch.build.targets.{self.plugin_name}.artifacts'
        else:
            artifact_config = self.build_config
            artifact_location = 'tool.hatch.build.artifacts'

        all_artifact_patterns = []

        artifact_patterns = artifact_config.get('artifacts', [])
        if not isinstance(artifact_patterns, list):
            message = f'Field `{artifact_location}` must be an array of strings'
            raise TypeError(message)

        for i, artifact_pattern in enumerate(artifact_patterns, 1):
            if not isinstance(artifact_pattern, str):
                message = f'Pattern #{i} in field `{artifact_location}` must be a string'
                raise TypeError(message)

            if not artifact_pattern:
                message = f'Pattern #{i} in field `{artifact_location}` cannot be an empty string'
                raise ValueError(message)

            all_artifact_patterns.append(artifact_pattern)

        if all_artifact_patterns:
            return pathspec.GitIgnoreSpec.from_lines(all_artifact_patterns)
        return None

    @cached_property
    def hook_config(self) -> dict[str, Any]:
        hook_config: dict[str, dict[str, Any]] = {}

        global_hook_config = self.build_config.get('hooks', {})
        if not isinstance(global_hook_config, dict):
            message = 'Field `tool.hatch.build.hooks` must be a table'
            raise TypeError(message)

        for hook_name, config in global_hook_config.items():
            if not isinstance(config, dict):
                message = f'Field `tool.hatch.build.hooks.{hook_name}` must be a table'
                raise TypeError(message)

            hook_config.setdefault(hook_name, config)

        target_hook_config = self.target_config.get('hooks', {})
        if not isinstance(target_hook_config, dict):
            message = f'Field `tool.hatch.build.targets.{self.plugin_name}.hooks` must be a table'
            raise TypeError(message)

        for hook_name, config in target_hook_config.items():
            if not isinstance(config, dict):
                message = f'Field `tool.hatch.build.targets.{self.plugin_name}.hooks.{hook_name}` must be a table'
                raise TypeError(message)

            hook_config[hook_name] = config

        if not env_var_enabled(BuildEnvVars.NO_HOOKS):
            all_hooks_enabled = env_var_enabled(BuildEnvVars.HOOKS_ENABLE)
            final_hook_config = {
                hook_name: config
                for hook_name, config in hook_config.items()
                if (
                    all_hooks_enabled
                    or config.get('enable-by-default', True)
                    or env_var_enabled(f'{BuildEnvVars.HOOK_ENABLE_PREFIX}{hook_name.upper()}')
                )
            }
        else:
            final_hook_config = {}

        return final_hook_config

    @cached_property
    def directory(self) -> str:
        if 'directory' in self.target_config:
            directory = self.target_config['directory']
            if not isinstance(directory, str):
                message = f'Field `tool.hatch.build.targets.{self.plugin_name}.directory` must be a string'
                raise TypeError(message)
        else:
            directory = self.build_config.get('directory', DEFAULT_BUILD_DIRECTORY)
            if not isinstance(directory, str):
                message = 'Field `tool.hatch.build.directory` must be a string'
                raise TypeError(message)

        return self.normalize_build_directory(directory)

    @cached_property
    def skip_excluded_dirs(self) -> bool:
        if 'skip-excluded-dirs' in self.target_config:
            skip_excluded_dirs = self.target_config['skip-excluded-dirs']
            if not isinstance(skip_excluded_dirs, bool):
                message = f'Field `tool.hatch.build.targets.{self.plugin_name}.skip-excluded-dirs` must be a boolean'
                raise TypeError(message)
        else:
            skip_excluded_dirs = self.build_config.get('skip-excluded-dirs', False)
            if not isinstance(skip_excluded_dirs, bool):
                message = 'Field `tool.hatch.build.skip-excluded-dirs` must be a boolean'
                raise TypeError(message)

        return skip_excluded_dirs

    @cached_property
    def ignore_vcs(self) -> bool:
        if 'ignore-vcs' in self.target_config:
            ignore_vcs = self.target_config['ignore-vcs']
            if not isinstance(ignore_vcs, bool):
                message = f'Field `tool.hatch.build.targets.{self.plugin_name}.ignore-vcs` must be a boolean'
                raise TypeError(message)
        else:
            ignore_vcs = self.build_config.get('ignore-vcs', False)
            if not isinstance(ignore_vcs, bool):
                message = 'Field `tool.hatch.build.ignore-vcs` must be a boolean'
                raise TypeError(message)

        return ignore_vcs

    @cached_property
    def require_runtime_dependencies(self) -> bool:
        if 'require-runtime-dependencies' in self.target_config:
            require_runtime_dependencies = self.target_config['require-runtime-dependencies']
            if not isinstance(require_runtime_dependencies, bool):
                message = (
                    f'Field `tool.hatch.build.targets.{self.plugin_name}.require-runtime-dependencies` '
                    f'must be a boolean'
                )
                raise TypeError(message)
        else:
            require_runtime_dependencies = self.build_config.get('require-runtime-dependencies', False)
            if not isinstance(require_runtime_dependencies, bool):
                message = 'Field `tool.hatch.build.require-runtime-dependencies` must be a boolean'
                raise TypeError(message)

        return require_runtime_dependencies

    @cached_property
    def require_runtime_features(self) -> list[str]:
        if 'require-runtime-features' in self.target_config:
            features_config = self.target_config
            features_location = f'tool.hatch.build.targets.{self.plugin_name}.require-runtime-features'
        else:
            features_config = self.build_config
            features_location = 'tool.hatch.build.require-runtime-features'

        require_runtime_features = features_config.get('require-runtime-features', [])
        if not isinstance(require_runtime_features, list):
            message = f'Field `{features_location}` must be an array'
            raise TypeError(message)

        all_features: dict[str, None] = {}
        for i, raw_feature in enumerate(require_runtime_features, 1):
            if not isinstance(raw_feature, str):
                message = f'Feature #{i} of field `{features_location}` must be a string'
                raise TypeError(message)

            if not raw_feature:
                message = f'Feature #{i} of field `{features_location}` cannot be an empty string'
                raise ValueError(message)

            feature = normalize_project_name(raw_feature)
            if feature not in self.builder.metadata.core.optional_dependencies:
                message = (
                    f'Feature `{feature}` of field `{features_location}` is not defined in '
                    f'field `project.optional-dependencies`'
                )
                raise ValueError(message)

            all_features[feature] = None

        return list(all_features)

    @cached_property
    def only_packages(self) -> bool:
        """
        Whether or not the target should ignore non-artifact files that do not reside within a Python package.
        """
        if 'only-packages' in self.target_config:
            only_packages = self.target_config['only-packages']
            if not isinstance(only_packages, bool):
                message = f'Field `tool.hatch.build.targets.{self.plugin_name}.only-packages` must be a boolean'
                raise TypeError(message)
        else:
            only_packages = self.build_config.get('only-packages', False)
            if not isinstance(only_packages, bool):
                message = 'Field `tool.hatch.build.only-packages` must be a boolean'
                raise TypeError(message)

        return only_packages

    @cached_property
    def reproducible(self) -> bool:
        """
        Whether or not the target should be built in a reproducible manner, defaulting to true.
        """
        if 'reproducible' in self.target_config:
            reproducible = self.target_config['reproducible']
            if not isinstance(reproducible, bool):
                message = f'Field `tool.hatch.build.targets.{self.plugin_name}.reproducible` must be a boolean'
                raise TypeError(message)
        else:
            reproducible = self.build_config.get('reproducible', True)
            if not isinstance(reproducible, bool):
                message = 'Field `tool.hatch.build.reproducible` must be a boolean'
                raise TypeError(message)

        return reproducible

    @cached_property
    def dev_mode_dirs(self) -> list[str]:
        """
        Directories which must be added to Python's search path in
        [dev mode](../config/environment/overview.md#dev-mode).
        """
        if 'dev-mode-dirs' in self.target_config:
            dev_mode_dirs_config = self.target_config
            dev_mode_dirs_location = f'tool.hatch.build.targets.{self.plugin_name}.dev-mode-dirs'
        else:
            dev_mode_dirs_config = self.build_config
            dev_mode_dirs_location = 'tool.hatch.build.dev-mode-dirs'

        all_dev_mode_dirs = []

        dev_mode_dirs = dev_mode_dirs_config.get('dev-mode-dirs', [])
        if not isinstance(dev_mode_dirs, list):
            message = f'Field `{dev_mode_dirs_location}` must be an array of strings'
            raise TypeError(message)

        for i, dev_mode_dir in enumerate(dev_mode_dirs, 1):
            if not isinstance(dev_mode_dir, str):
                message = f'Directory #{i} in field `{dev_mode_dirs_location}` must be a string'
                raise TypeError(message)

            if not dev_mode_dir:
                message = f'Directory #{i} in field `{dev_mode_dirs_location}` cannot be an empty string'
                raise ValueError(message)

            all_dev_mode_dirs.append(dev_mode_dir)

        return all_dev_mode_dirs

    @cached_property
    def dev_mode_exact(self) -> bool:
        if 'dev-mode-exact' in self.target_config:
            dev_mode_exact = self.target_config['dev-mode-exact']
            if not isinstance(dev_mode_exact, bool):
                message = f'Field `tool.hatch.build.targets.{self.plugin_name}.dev-mode-exact` must be a boolean'
                raise TypeError(message)
        else:
            dev_mode_exact = self.build_config.get('dev-mode-exact', False)
            if not isinstance(dev_mode_exact, bool):
                message = 'Field `tool.hatch.build.dev-mode-exact` must be a boolean'
                raise TypeError(message)

        return dev_mode_exact

    @cached_property
    def versions(self) -> list[str]:
        # Used as an ordered set
        all_versions: dict[str, None] = {}

        versions = self.target_config.get('versions', [])
        if not isinstance(versions, list):
            message = f'Field `tool.hatch.build.targets.{self.plugin_name}.versions` must be an array of strings'
            raise TypeError(message)

        for i, version in enumerate(versions, 1):
            if not isinstance(version, str):
                message = (
                    f'Version #{i} in field `tool.hatch.build.targets.{self.plugin_name}.versions` must be a string'
                )
                raise TypeError(message)

            if not version:
                message = (
                    f'Version #{i} in field `tool.hatch.build.targets.{self.plugin_name}.versions` '
                    f'cannot be an empty string'
                )
                raise ValueError(message)

            all_versions[version] = None

        if not all_versions:
            default_versions = self.__builder.get_default_versions()
            for version in default_versions:
                all_versions[version] = None
        else:
            unknown_versions = set(all_versions) - set(self.__builder.get_version_api())
            if unknown_versions:
                message = (
                    f'Unknown versions in field `tool.hatch.build.targets.{self.plugin_name}.versions`: '
                    f'{", ".join(map(str, sorted(unknown_versions)))}'
                )
                raise ValueError(message)

        return list(all_versions)

    @cached_property
    def dependencies(self) -> list[str]:
        # Used as an ordered set
        dependencies: dict[str, None] = {}

        target_dependencies = self.target_config.get('dependencies', [])
        if not isinstance(target_dependencies, list):
            message = f'Field `tool.hatch.build.targets.{self.plugin_name}.dependencies` must be an array'
            raise TypeError(message)

        for i, dependency in enumerate(target_dependencies, 1):
            if not isinstance(dependency, str):
                message = (
                    f'Dependency #{i} of field `tool.hatch.build.targets.{self.plugin_name}.dependencies` '
                    f'must be a string'
                )
                raise TypeError(message)

            dependencies[dependency] = None

        global_dependencies = self.build_config.get('dependencies', [])
        if not isinstance(global_dependencies, list):
            message = 'Field `tool.hatch.build.dependencies` must be an array'
            raise TypeError(message)

        for i, dependency in enumerate(global_dependencies, 1):
            if not isinstance(dependency, str):
                message = f'Dependency #{i} of field `tool.hatch.build.dependencies` must be a string'
                raise TypeError(message)

            dependencies[dependency] = None

        require_runtime_dependencies = self.require_runtime_dependencies
        require_runtime_features = dict.fromkeys(self.require_runtime_features)
        for hook_name, config in self.hook_config.items():
            hook_require_runtime_dependencies = config.get('require-runtime-dependencies', False)
            if not isinstance(hook_require_runtime_dependencies, bool):
                message = f'Option `require-runtime-dependencies` of build hook `{hook_name}` must be a boolean'
                raise TypeError(message)

            if hook_require_runtime_dependencies:
                require_runtime_dependencies = True

            hook_require_runtime_features = config.get('require-runtime-features', [])
            if not isinstance(hook_require_runtime_features, list):
                message = f'Option `require-runtime-features` of build hook `{hook_name}` must be an array'
                raise TypeError(message)

            for i, raw_feature in enumerate(hook_require_runtime_features, 1):
                if not isinstance(raw_feature, str):
                    message = (
                        f'Feature #{i} of option `require-runtime-features` of build hook `{hook_name}` '
                        f'must be a string'
                    )
                    raise TypeError(message)

                if not raw_feature:
                    message = (
                        f'Feature #{i} of option `require-runtime-features` of build hook `{hook_name}` '
                        f'cannot be an empty string'
                    )
                    raise ValueError(message)

                feature = normalize_project_name(raw_feature)
                if feature not in self.builder.metadata.core.optional_dependencies:
                    message = (
                        f'Feature `{feature}` of option `require-runtime-features` of build hook `{hook_name}` '
                        f'is not defined in field `project.optional-dependencies`'
                    )
                    raise ValueError(message)

                require_runtime_features[feature] = None

            hook_dependencies = config.get('dependencies', [])
            if not isinstance(hook_dependencies, list):
                message = f'Option `dependencies` of build hook `{hook_name}` must be an array'
                raise TypeError(message)

            for i, dependency in enumerate(hook_dependencies, 1):
                if not isinstance(dependency, str):
                    message = f'Dependency #{i} of option `dependencies` of build hook `{hook_name}` must be a string'
                    raise TypeError(message)

                dependencies[dependency] = None

        if require_runtime_dependencies:
            for dependency in self.builder.metadata.core.dependencies:
                dependencies[dependency] = None

        if require_runtime_features:
            for feature in require_runtime_features:
                for dependency in self.builder.metadata.core.optional_dependencies[feature]:
                    dependencies[dependency] = None

        for dependency in self.dynamic_dependencies:
            dependencies[dependency] = None

        return list(dependencies)

    @cached_property
    def dynamic_dependencies(self) -> list[str]:
        dependencies = []
        for hook_name, config in self.hook_config.items():
            build_hook_cls = self.builder.plugin_manager.build_hook.get(hook_name)
            if build_hook_cls is None:
                continue

            # Hook exists but dynamic dependencies are not imported lazily.
            # This happens for example when using the `custom` build hook.
            try:
                build_hook = build_hook_cls(
                    self.root, config, self, self.builder.metadata, '', self.builder.PLUGIN_NAME, self.builder.app
                )
            except ImportError:
                continue

            dependencies.extend(build_hook.dependencies())

        return dependencies

    @cached_property
    def sources(self) -> dict[str, str]:
        if 'sources' in self.target_config:
            sources_config = self.target_config
            sources_location = f'tool.hatch.build.targets.{self.plugin_name}.sources'
        else:
            sources_config = self.build_config
            sources_location = 'tool.hatch.build.sources'

        sources = {}

        raw_sources = sources_config.get('sources', [])
        if isinstance(raw_sources, list):
            for i, source in enumerate(raw_sources, 1):
                if not isinstance(source, str):
                    message = f'Source #{i} in field `{sources_location}` must be a string'
                    raise TypeError(message)

                if not source:
                    message = f'Source #{i} in field `{sources_location}` cannot be an empty string'
                    raise ValueError(message)

                sources[normalize_relative_directory(source)] = ''
        elif isinstance(raw_sources, dict):
            for source, path in raw_sources.items():
                if not isinstance(path, str):
                    message = f'Path for source `{source}` in field `{sources_location}` must be a string'
                    raise TypeError(message)

                normalized_path = normalize_relative_path(path)
                if normalized_path == '.':
                    normalized_path = ''
                else:
                    normalized_path += os.sep

                sources[normalize_relative_directory(source) if source else source] = normalized_path
        else:
            message = f'Field `{sources_location}` must be a mapping or array of strings'
            raise TypeError(message)

        for relative_path in self.packages:
            source, _package = os.path.split(relative_path)
            if source and normalize_relative_directory(relative_path) not in sources:
                sources[normalize_relative_directory(source)] = ''

        return dict(sorted(sources.items()))

    @cached_property
    def packages(self) -> list[str]:
        if 'packages' in self.target_config:
            package_config = self.target_config
            package_location = f'tool.hatch.build.targets.{self.plugin_name}.packages'
        else:
            package_config = self.build_config
            package_location = 'tool.hatch.build.packages'

        packages = package_config.get('packages', self.default_packages())
        if not isinstance(packages, list):
            message = f'Field `{package_location}` must be an array of strings'
            raise TypeError(message)

        for i, package in enumerate(packages, 1):
            if not isinstance(package, str):
                message = f'Package #{i} in field `{package_location}` must be a string'
                raise TypeError(message)

            if not package:
                message = f'Package #{i} in field `{package_location}` cannot be an empty string'
                raise ValueError(message)

        return sorted(normalize_relative_path(package) for package in packages)

    @cached_property
    def force_include(self) -> dict[str, str]:
        if 'force-include' in self.target_config:
            force_include_config = self.target_config
            force_include_location = f'tool.hatch.build.targets.{self.plugin_name}.force-include'
        else:
            force_include_config = self.build_config
            force_include_location = 'tool.hatch.build.force-include'

        force_include = force_include_config.get('force-include', {})
        if not isinstance(force_include, dict):
            message = f'Field `{force_include_location}` must be a mapping'
            raise TypeError(message)

        for i, (source, relative_path) in enumerate(force_include.items(), 1):
            if not source:
                message = f'Source #{i} in field `{force_include_location}` cannot be an empty string'
                raise ValueError(message)

            if not isinstance(relative_path, str):
                message = f'Path for source `{source}` in field `{force_include_location}` must be a string'
                raise TypeError(message)

            if not relative_path:
                message = f'Path for source `{source}` in field `{force_include_location}` cannot be an empty string'
                raise ValueError(message)

        return normalize_inclusion_map(force_include, self.root)

    @cached_property
    def only_include(self) -> dict[str, str]:
        if 'only-include' in self.target_config:
            only_include_config = self.target_config
            only_include_location = f'tool.hatch.build.targets.{self.plugin_name}.only-include'
        else:
            only_include_config = self.build_config
            only_include_location = 'tool.hatch.build.only-include'

        only_include = only_include_config.get('only-include', self.default_only_include()) or self.packages
        if not isinstance(only_include, list):
            message = f'Field `{only_include_location}` must be an array'
            raise TypeError(message)

        inclusion_map = {}

        for i, relative_path in enumerate(only_include, 1):
            if not isinstance(relative_path, str):
                message = f'Path #{i} in field `{only_include_location}` must be a string'
                raise TypeError(message)

            normalized_path = normalize_relative_path(relative_path)
            if not normalized_path or normalized_path.startswith(('~', '..')):
                message = f'Path #{i} in field `{only_include_location}` must be relative: {relative_path}'
                raise ValueError(message)

            if normalized_path in inclusion_map:
                message = f'Duplicate path in field `{only_include_location}`: {normalized_path}'
                raise ValueError(message)

            inclusion_map[normalized_path] = normalized_path

        return normalize_inclusion_map(inclusion_map, self.root)

    def get_distribution_path(self, relative_path: str) -> str:
        # src/foo/bar.py -> foo/bar.py
        for source, replacement in self.sources.items():
            if not source:
                return replacement + relative_path

            if relative_path.startswith(source):
                return relative_path.replace(source, replacement, 1)

        return relative_path

    @cached_property
    def vcs_exclusion_files(self) -> dict[str, list[str]]:
        exclusion_files: dict[str, list[str]] = {'git': [], 'hg': []}

        local_gitignore = locate_file(self.root, '.gitignore', boundary='.git')
        if local_gitignore is not None:
            exclusion_files['git'].append(local_gitignore)

        local_hgignore = locate_file(self.root, '.hgignore', boundary='.hg')
        if local_hgignore is not None:
            exclusion_files['hg'].append(local_hgignore)

        return exclusion_files

    def load_vcs_exclusion_patterns(self) -> list[str]:
        patterns = []

        # https://git-scm.com/docs/gitignore#_pattern_format
        for exclusion_file in self.vcs_exclusion_files['git']:
            with open(exclusion_file, encoding='utf-8') as f:
                patterns.extend(f.readlines())

        # https://linux.die.net/man/5/hgignore
        for exclusion_file in self.vcs_exclusion_files['hg']:
            with open(exclusion_file, encoding='utf-8') as f:
                glob_mode = False
                for line in f:
                    exact_line = line.strip()
                    if exact_line == 'syntax: glob':
                        glob_mode = True
                        continue

                    if exact_line.startswith('syntax: '):
                        glob_mode = False
                        continue

                    if glob_mode:
                        patterns.append(line)

        # validate project root is not excluded by vcs
        exclude_spec = pathspec.GitIgnoreSpec.from_lines(patterns)
        if exclude_spec.match_file(self.root):
            return []

        return patterns

    def normalize_build_directory(self, build_directory: str) -> str:
        if not os.path.isabs(build_directory):
            build_directory = os.path.join(self.root, build_directory)

        return os.path.normpath(build_directory)

    def default_include(self) -> list:  # noqa: PLR6301
        return []

    def default_exclude(self) -> list:  # noqa: PLR6301
        return []

    def default_packages(self) -> list:  # noqa: PLR6301
        return []

    def default_only_include(self) -> list:  # noqa: PLR6301
        return []

    def default_global_exclude(self) -> list[str]:  # noqa: PLR6301
        patterns = ['*.py[cdo]', f'/{DEFAULT_BUILD_DIRECTORY}']
        patterns.sort()
        return patterns

    def set_exclude_all(self) -> None:
        self.__exclude_all = True

    def get_force_include(self) -> dict[str, str]:
        force_include = self.force_include.copy()
        force_include.update(self.build_force_include)
        return force_include

    @contextmanager
    def set_build_data(self, build_data: dict[str, Any]) -> Generator:
        try:
            # Include anything the hooks indicate
            build_artifacts = build_data['artifacts']
            if build_artifacts:
                self.build_artifact_spec = pathspec.GitIgnoreSpec.from_lines(build_artifacts)

            self.build_force_include.update(normalize_inclusion_map(build_data['force_include'], self.root))

            for inclusion_map in (self.force_include, self.build_force_include):
                for source, target in inclusion_map.items():
                    # Ignore source
                    # old/ -> new/
                    # old.ext -> new.ext
                    if source.startswith(f'{self.root}{os.sep}'):
                        self.build_reserved_paths.add(self.get_distribution_path(os.path.relpath(source, self.root)))
                    # Ignore target files only
                    # ../out.ext -> ../in.ext
                    elif os.path.isfile(source):
                        self.build_reserved_paths.add(self.get_distribution_path(target))

            yield
        finally:
            self.build_artifact_spec = None
            self.build_force_include.clear()
            self.build_reserved_paths.clear()


def env_var_enabled(env_var: str, *, default: bool = False) -> bool:
    if env_var in os.environ:
        return os.environ[env_var] in {'1', 'true'}

    return default


BuilderConfigBound = TypeVar('BuilderConfigBound', bound=BuilderConfig)
