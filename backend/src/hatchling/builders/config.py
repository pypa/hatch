import os
from contextlib import contextmanager

import pathspec

from hatchling.builders.constants import DEFAULT_BUILD_DIRECTORY, EXCLUDED_DIRECTORIES, BuildEnvVars
from hatchling.builders.utils import normalize_inclusion_map, normalize_relative_directory, normalize_relative_path
from hatchling.metadata.utils import normalize_project_name
from hatchling.utils.fs import locate_file


class BuilderConfig:
    def __init__(self, builder, root, plugin_name, build_config, target_config):
        self.__builder = builder
        self.__root = root
        self.__plugin_name = plugin_name
        self.__build_config = build_config
        self.__target_config = target_config
        self.__hook_config = None
        self.__versions = None
        self.__dependencies = None
        self.__sources = None
        self.__packages = None
        self.__only_include = None
        self.__force_include = None
        self.__vcs_exclusion_files = None

        # Possible pathspec.GitIgnoreSpec
        self.__include_spec = None
        self.__exclude_spec = None
        self.__artifact_spec = None

        # These are used to create the pathspecs and will never be `None` after the first match attempt
        self.__include_patterns = None
        self.__exclude_patterns = None
        self.__artifact_patterns = None

        # Modified at build time
        self.build_artifact_spec = None
        self.build_force_include = {}
        self.build_reserved_paths = set()

        # Common options
        self.__directory = None
        self.__skip_excluded_dirs = None
        self.__ignore_vcs = None
        self.__only_packages = None
        self.__reproducible = None
        self.__dev_mode_dirs = None
        self.__dev_mode_exact = None
        self.__require_runtime_dependencies = None
        self.__require_runtime_features = None

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

    def include_path(self, relative_path, *, explicit=False, is_package=True):
        return (
            self.path_is_build_artifact(relative_path)
            or self.path_is_artifact(relative_path)
            or (
                not (self.only_packages and not is_package)
                and not self.path_is_reserved(relative_path)
                and not self.path_is_excluded(relative_path)
                and (explicit or self.path_is_included(relative_path))
            )
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

    def path_is_reserved(self, relative_path):
        return relative_path in self.build_reserved_paths

    def directory_is_excluded(self, name, relative_path):
        if name in EXCLUDED_DIRECTORIES:
            return True

        relative_directory = os.path.join(relative_path, name)
        return (
            self.path_is_reserved(relative_directory)
            # The trailing slash is necessary so e.g. `bar/` matches `foo/bar`
            or (self.skip_excluded_dirs and self.path_is_excluded(f'{relative_directory}/'))
        )

    @property
    def include_spec(self):
        if self.__include_patterns is None:
            if 'include' in self.target_config:
                include_config = self.target_config
                include_location = f'tool.hatch.build.targets.{self.plugin_name}.include'
            else:
                include_config = self.build_config
                include_location = 'tool.hatch.build.include'

            all_include_patterns = []

            include_patterns = include_config.get('include', self.default_include())
            if not isinstance(include_patterns, list):
                raise TypeError(f'Field `{include_location}` must be an array of strings')

            for i, include_pattern in enumerate(include_patterns, 1):
                if not isinstance(include_pattern, str):
                    raise TypeError(f'Pattern #{i} in field `{include_location}` must be a string')
                elif not include_pattern:
                    raise ValueError(f'Pattern #{i} in field `{include_location}` cannot be an empty string')

                all_include_patterns.append(include_pattern)

            for relative_path in self.packages:
                # Matching only at the root requires a forward slash, back slashes do not work. As such,
                # normalize to forward slashes for consistency.
                all_include_patterns.append(f"/{relative_path.replace(os.sep, '/')}/")

            if all_include_patterns:
                self.__include_spec = pathspec.GitIgnoreSpec.from_lines(all_include_patterns)

            self.__include_patterns = all_include_patterns

        return self.__include_spec

    @property
    def exclude_spec(self):
        if self.__exclude_patterns is None:
            if 'exclude' in self.target_config:
                exclude_config = self.target_config
                exclude_location = f'tool.hatch.build.targets.{self.plugin_name}.exclude'
            else:
                exclude_config = self.build_config
                exclude_location = 'tool.hatch.build.exclude'

            all_exclude_patterns = self.default_global_exclude()

            exclude_patterns = exclude_config.get('exclude', self.default_exclude())
            if not isinstance(exclude_patterns, list):
                raise TypeError(f'Field `{exclude_location}` must be an array of strings')

            for i, exclude_pattern in enumerate(exclude_patterns, 1):
                if not isinstance(exclude_pattern, str):
                    raise TypeError(f'Pattern #{i} in field `{exclude_location}` must be a string')
                elif not exclude_pattern:
                    raise ValueError(f'Pattern #{i} in field `{exclude_location}` cannot be an empty string')

                all_exclude_patterns.append(exclude_pattern)

            if not self.ignore_vcs:
                all_exclude_patterns.extend(self.load_vcs_exclusion_patterns())

            if all_exclude_patterns:
                self.__exclude_spec = pathspec.GitIgnoreSpec.from_lines(all_exclude_patterns)

            self.__exclude_patterns = all_exclude_patterns

        return self.__exclude_spec

    @property
    def artifact_spec(self):
        if self.__artifact_patterns is None:
            if 'artifacts' in self.target_config:
                artifact_config = self.target_config
                artifact_location = f'tool.hatch.build.targets.{self.plugin_name}.artifacts'
            else:
                artifact_config = self.build_config
                artifact_location = 'tool.hatch.build.artifacts'

            all_artifact_patterns = []

            artifact_patterns = artifact_config.get('artifacts', [])
            if not isinstance(artifact_patterns, list):
                raise TypeError(f'Field `{artifact_location}` must be an array of strings')

            for i, artifact_pattern in enumerate(artifact_patterns, 1):
                if not isinstance(artifact_pattern, str):
                    raise TypeError(f'Pattern #{i} in field `{artifact_location}` must be a string')
                elif not artifact_pattern:
                    raise ValueError(f'Pattern #{i} in field `{artifact_location}` cannot be an empty string')

                all_artifact_patterns.append(artifact_pattern)

            if all_artifact_patterns:
                self.__artifact_spec = pathspec.GitIgnoreSpec.from_lines(all_artifact_patterns)

            self.__artifact_patterns = all_artifact_patterns

        return self.__artifact_spec

    @property
    def hook_config(self):
        if self.__hook_config is None:
            hook_config = {}

            global_hook_config = self.build_config.get('hooks', {})
            if not isinstance(global_hook_config, dict):
                raise TypeError('Field `tool.hatch.build.hooks` must be a table')

            for hook_name, config in global_hook_config.items():
                if not isinstance(config, dict):
                    raise TypeError(f'Field `tool.hatch.build.hooks.{hook_name}` must be a table')

                hook_config.setdefault(hook_name, config)

            target_hook_config = self.target_config.get('hooks', {})
            if not isinstance(target_hook_config, dict):
                raise TypeError(f'Field `tool.hatch.build.targets.{self.plugin_name}.hooks` must be a table')

            for hook_name, config in target_hook_config.items():
                if not isinstance(config, dict):
                    raise TypeError(
                        f'Field `tool.hatch.build.targets.{self.plugin_name}.hooks.{hook_name}` must be a table'
                    )

                hook_config[hook_name] = config

            final_hook_config = {}
            if not env_var_enabled(BuildEnvVars.NO_HOOKS):
                all_hooks_enabled = env_var_enabled(BuildEnvVars.HOOKS_ENABLE)
                for hook_name, config in hook_config.items():
                    if (
                        all_hooks_enabled
                        or config.get('enable-by-default', True)
                        or env_var_enabled(f'{BuildEnvVars.HOOK_ENABLE_PREFIX}{hook_name.upper()}')
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
                    raise TypeError(f'Field `tool.hatch.build.targets.{self.plugin_name}.directory` must be a string')
            else:
                directory = self.build_config.get('directory', DEFAULT_BUILD_DIRECTORY)
                if not isinstance(directory, str):
                    raise TypeError('Field `tool.hatch.build.directory` must be a string')

            self.__directory = self.normalize_build_directory(directory)

        return self.__directory

    @property
    def skip_excluded_dirs(self):
        if self.__skip_excluded_dirs is None:
            if 'skip-excluded-dirs' in self.target_config:
                skip_excluded_dirs = self.target_config['skip-excluded-dirs']
                if not isinstance(skip_excluded_dirs, bool):
                    raise TypeError(
                        f'Field `tool.hatch.build.targets.{self.plugin_name}.skip-excluded-dirs` must be a boolean'
                    )
            else:
                skip_excluded_dirs = self.build_config.get('skip-excluded-dirs', False)
                if not isinstance(skip_excluded_dirs, bool):
                    raise TypeError('Field `tool.hatch.build.skip-excluded-dirs` must be a boolean')

            self.__skip_excluded_dirs = skip_excluded_dirs

        return self.__skip_excluded_dirs

    @property
    def ignore_vcs(self):
        if self.__ignore_vcs is None:
            if 'ignore-vcs' in self.target_config:
                ignore_vcs = self.target_config['ignore-vcs']
                if not isinstance(ignore_vcs, bool):
                    raise TypeError(f'Field `tool.hatch.build.targets.{self.plugin_name}.ignore-vcs` must be a boolean')
            else:
                ignore_vcs = self.build_config.get('ignore-vcs', False)
                if not isinstance(ignore_vcs, bool):
                    raise TypeError('Field `tool.hatch.build.ignore-vcs` must be a boolean')

            self.__ignore_vcs = ignore_vcs

        return self.__ignore_vcs

    @property
    def require_runtime_dependencies(self):
        if self.__require_runtime_dependencies is None:
            if 'require-runtime-dependencies' in self.target_config:
                require_runtime_dependencies = self.target_config['require-runtime-dependencies']
                if not isinstance(require_runtime_dependencies, bool):
                    raise TypeError(
                        f'Field `tool.hatch.build.targets.{self.plugin_name}.require-runtime-dependencies` '
                        f'must be a boolean'
                    )
            else:
                require_runtime_dependencies = self.build_config.get('require-runtime-dependencies', False)
                if not isinstance(require_runtime_dependencies, bool):
                    raise TypeError('Field `tool.hatch.build.require-runtime-dependencies` must be a boolean')

            self.__require_runtime_dependencies = require_runtime_dependencies

        return self.__require_runtime_dependencies

    @property
    def require_runtime_features(self):
        if self.__require_runtime_features is None:
            if 'require-runtime-features' in self.target_config:
                features_config = self.target_config
                features_location = f'tool.hatch.build.targets.{self.plugin_name}.require-runtime-features'
            else:
                features_config = self.build_config
                features_location = 'tool.hatch.build.require-runtime-features'

            require_runtime_features = features_config.get('require-runtime-features', [])
            if not isinstance(require_runtime_features, list):
                raise TypeError(f'Field `{features_location}` must be an array')

            all_features = {}
            for i, feature in enumerate(require_runtime_features, 1):
                if not isinstance(feature, str):
                    raise TypeError(f'Feature #{i} of field `{features_location}` must be a string')
                elif not feature:
                    raise ValueError(f'Feature #{i} of field `{features_location}` cannot be an empty string')

                feature = normalize_project_name(feature)
                if feature not in self.builder.metadata.core.optional_dependencies:
                    raise ValueError(
                        f'Feature `{feature}` of field `{features_location}` is not defined in '
                        f'field `project.optional-dependencies`'
                    )

                all_features[feature] = None

            self.__require_runtime_features = list(all_features)

        return self.__require_runtime_features

    @property
    def only_packages(self):
        """
        Whether or not the target should ignore non-artifact files that do not reside within a Python package.
        """
        if self.__only_packages is None:
            if 'only-packages' in self.target_config:
                only_packages = self.target_config['only-packages']
                if not isinstance(only_packages, bool):
                    raise TypeError(
                        f'Field `tool.hatch.build.targets.{self.plugin_name}.only-packages` must be a boolean'
                    )
            else:
                only_packages = self.build_config.get('only-packages', False)
                if not isinstance(only_packages, bool):
                    raise TypeError('Field `tool.hatch.build.only-packages` must be a boolean')

            self.__only_packages = only_packages

        return self.__only_packages

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
                        f'Field `tool.hatch.build.targets.{self.plugin_name}.reproducible` must be a boolean'
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
        Directories which must be added to Python's search path in
        [dev mode](../config/environment/overview.md#dev-mode).
        """
        if self.__dev_mode_dirs is None:
            if 'dev-mode-dirs' in self.target_config:
                dev_mode_dirs_config = self.target_config
                dev_mode_dirs_location = f'tool.hatch.build.targets.{self.plugin_name}.dev-mode-dirs'
            else:
                dev_mode_dirs_config = self.build_config
                dev_mode_dirs_location = 'tool.hatch.build.dev-mode-dirs'

            all_dev_mode_dirs = []

            dev_mode_dirs = dev_mode_dirs_config.get('dev-mode-dirs', [])
            if not isinstance(dev_mode_dirs, list):
                raise TypeError(f'Field `{dev_mode_dirs_location}` must be an array of strings')

            for i, dev_mode_dir in enumerate(dev_mode_dirs, 1):
                if not isinstance(dev_mode_dir, str):
                    raise TypeError(f'Directory #{i} in field `{dev_mode_dirs_location}` must be a string')
                elif not dev_mode_dir:
                    raise ValueError(f'Directory #{i} in field `{dev_mode_dirs_location}` cannot be an empty string')

                all_dev_mode_dirs.append(dev_mode_dir)

            self.__dev_mode_dirs = all_dev_mode_dirs

        return self.__dev_mode_dirs

    @property
    def dev_mode_exact(self):
        if self.__dev_mode_exact is None:
            if 'dev-mode-exact' in self.target_config:
                dev_mode_exact = self.target_config['dev-mode-exact']
                if not isinstance(dev_mode_exact, bool):
                    raise TypeError(
                        f'Field `tool.hatch.build.targets.{self.plugin_name}.dev-mode-exact` must be a boolean'
                    )
            else:
                dev_mode_exact = self.build_config.get('dev-mode-exact', False)
                if not isinstance(dev_mode_exact, bool):
                    raise TypeError('Field `tool.hatch.build.dev-mode-exact` must be a boolean')

            self.__dev_mode_exact = dev_mode_exact

        return self.__dev_mode_exact

    @property
    def versions(self):
        if self.__versions is None:
            # Used as an ordered set
            all_versions = {}

            versions = self.target_config.get('versions', [])
            if not isinstance(versions, list):
                raise TypeError(
                    f'Field `tool.hatch.build.targets.{self.plugin_name}.versions` must be an array of strings'
                )

            for i, version in enumerate(versions, 1):
                if not isinstance(version, str):
                    raise TypeError(
                        f'Version #{i} in field `tool.hatch.build.targets.{self.plugin_name}.versions` must be a string'
                    )
                elif not version:
                    raise ValueError(
                        f'Version #{i} in field `tool.hatch.build.targets.{self.plugin_name}.versions` '
                        f'cannot be an empty string'
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
                        f'Unknown versions in field `tool.hatch.build.targets.{self.plugin_name}.versions`: '
                        f'{", ".join(map(str, sorted(unknown_versions)))}'
                    )

            self.__versions = list(all_versions)

        return self.__versions

    @property
    def dependencies(self):
        if self.__dependencies is None:
            # Used as an ordered set
            dependencies = {}

            target_dependencies = self.target_config.get('dependencies', [])
            if not isinstance(target_dependencies, list):
                raise TypeError(f'Field `tool.hatch.build.targets.{self.plugin_name}.dependencies` must be an array')

            for i, dependency in enumerate(target_dependencies, 1):
                if not isinstance(dependency, str):
                    raise TypeError(
                        f'Dependency #{i} of field `tool.hatch.build.targets.{self.plugin_name}.dependencies` '
                        f'must be a string'
                    )

                dependencies[dependency] = None

            global_dependencies = self.build_config.get('dependencies', [])
            if not isinstance(global_dependencies, list):
                raise TypeError('Field `tool.hatch.build.dependencies` must be an array')

            for i, dependency in enumerate(global_dependencies, 1):
                if not isinstance(dependency, str):
                    raise TypeError(f'Dependency #{i} of field `tool.hatch.build.dependencies` must be a string')

                dependencies[dependency] = None

            require_runtime_dependencies = self.require_runtime_dependencies
            require_runtime_features = {feature: None for feature in self.require_runtime_features}
            for hook_name, config in self.hook_config.items():
                hook_require_runtime_dependencies = config.get('require-runtime-dependencies', False)
                if not isinstance(hook_require_runtime_dependencies, bool):
                    raise TypeError(
                        f'Option `require-runtime-dependencies` of build hook `{hook_name}` must be a boolean'
                    )
                elif hook_require_runtime_dependencies:
                    require_runtime_dependencies = True

                hook_require_runtime_features = config.get('require-runtime-features', [])
                if not isinstance(hook_require_runtime_features, list):
                    raise TypeError(f'Option `require-runtime-features` of build hook `{hook_name}` must be an array')

                for i, feature in enumerate(hook_require_runtime_features, 1):
                    if not isinstance(feature, str):
                        raise TypeError(
                            f'Feature #{i} of option `require-runtime-features` of build hook `{hook_name}` '
                            f'must be a string'
                        )
                    elif not feature:
                        raise ValueError(
                            f'Feature #{i} of option `require-runtime-features` of build hook `{hook_name}` '
                            f'cannot be an empty string'
                        )

                    feature = normalize_project_name(feature)
                    if feature not in self.builder.metadata.core.optional_dependencies:
                        raise ValueError(
                            f'Feature `{feature}` of option `require-runtime-features` of build hook `{hook_name}` '
                            f'is not defined in field `project.optional-dependencies`'
                        )

                    require_runtime_features[feature] = None

                hook_dependencies = config.get('dependencies', [])
                if not isinstance(hook_dependencies, list):
                    raise TypeError(f'Option `dependencies` of build hook `{hook_name}` must be an array')

                for i, dependency in enumerate(hook_dependencies, 1):
                    if not isinstance(dependency, str):
                        raise TypeError(
                            f'Dependency #{i} of option `dependencies` of build hook `{hook_name}` must be a string'
                        )

                    dependencies[dependency] = None

            if require_runtime_dependencies:
                for dependency in self.builder.metadata.core.dependencies:
                    dependencies[dependency] = None

            if require_runtime_features:
                for feature in require_runtime_features:
                    for dependency in self.builder.metadata.core.optional_dependencies[feature]:
                        dependencies[dependency] = None

            self.__dependencies = list(dependencies)

        return self.__dependencies

    @property
    def sources(self):
        if self.__sources is None:
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
                        raise TypeError(f'Source #{i} in field `{sources_location}` must be a string')
                    elif not source:
                        raise ValueError(f'Source #{i} in field `{sources_location}` cannot be an empty string')

                    sources[normalize_relative_directory(source)] = ''
            elif isinstance(raw_sources, dict):
                for i, (source, path) in enumerate(raw_sources.items(), 1):
                    if not source:
                        raise ValueError(f'Source #{i} in field `{sources_location}` cannot be an empty string')
                    elif not isinstance(path, str):
                        raise TypeError(f'Path for source `{source}` in field `{sources_location}` must be a string')

                    normalized_path = normalize_relative_path(path)
                    if normalized_path == '.':
                        normalized_path = ''
                    else:
                        normalized_path += os.sep

                    sources[normalize_relative_directory(source)] = normalized_path
            else:
                raise TypeError(f'Field `{sources_location}` must be a mapping or array of strings')

            for relative_path in self.packages:
                source, package = os.path.split(relative_path)
                if source and normalize_relative_directory(relative_path) not in sources:
                    sources[normalize_relative_directory(source)] = ''

            self.__sources = dict(sorted(sources.items()))

        return self.__sources

    @property
    def packages(self):
        if self.__packages is None:
            if 'packages' in self.target_config:
                package_config = self.target_config
                package_location = f'tool.hatch.build.targets.{self.plugin_name}.packages'
            else:
                package_config = self.build_config
                package_location = 'tool.hatch.build.packages'

            packages = package_config.get('packages', self.default_packages())
            if not isinstance(packages, list):
                raise TypeError(f'Field `{package_location}` must be an array of strings')

            for i, package in enumerate(packages, 1):
                if not isinstance(package, str):
                    raise TypeError(f'Package #{i} in field `{package_location}` must be a string')
                elif not package:
                    raise ValueError(f'Package #{i} in field `{package_location}` cannot be an empty string')

            self.__packages = sorted(normalize_relative_path(package) for package in packages)

        return self.__packages

    @property
    def force_include(self):
        if self.__force_include is None:
            if 'force-include' in self.target_config:
                force_include_config = self.target_config
                force_include_location = f'tool.hatch.build.targets.{self.plugin_name}.force-include'
            else:
                force_include_config = self.build_config
                force_include_location = 'tool.hatch.build.force-include'

            force_include = force_include_config.get('force-include', {})
            if not isinstance(force_include, dict):
                raise TypeError(f'Field `{force_include_location}` must be a mapping')

            for i, (source, relative_path) in enumerate(force_include.items(), 1):
                if not source:
                    raise ValueError(f'Source #{i} in field `{force_include_location}` cannot be an empty string')
                elif not isinstance(relative_path, str):
                    raise TypeError(f'Path for source `{source}` in field `{force_include_location}` must be a string')
                elif not relative_path:
                    raise ValueError(
                        f'Path for source `{source}` in field `{force_include_location}` cannot be an empty string'
                    )

            self.__force_include = normalize_inclusion_map(force_include, self.root)

        return self.__force_include

    @property
    def only_include(self):
        if self.__only_include is None:
            if 'only-include' in self.target_config:
                only_include_config = self.target_config
                only_include_location = f'tool.hatch.build.targets.{self.plugin_name}.only-include'
            else:
                only_include_config = self.build_config
                only_include_location = 'tool.hatch.build.only-include'

            only_include = only_include_config.get('only-include', self.default_only_include()) or self.packages
            if not isinstance(only_include, list):
                raise TypeError(f'Field `{only_include_location}` must be an array')

            inclusion_map = {}

            for i, relative_path in enumerate(only_include, 1):
                if not isinstance(relative_path, str):
                    raise TypeError(f'Path #{i} in field `{only_include_location}` must be a string')

                normalized_path = normalize_relative_path(relative_path)
                if not normalized_path or normalized_path.startswith(('~', '..')):
                    raise ValueError(f'Path #{i} in field `{only_include_location}` must be relative: {relative_path}')
                elif normalized_path in inclusion_map:
                    raise ValueError(f'Duplicate path in field `{only_include_location}`: {normalized_path}')

                inclusion_map[normalized_path] = normalized_path

            self.__only_include = normalize_inclusion_map(inclusion_map, self.root)

        return self.__only_include

    def get_distribution_path(self, relative_path):
        # src/foo/bar.py -> foo/bar.py
        for source, replacement in self.sources.items():
            if relative_path.startswith(source):
                return relative_path.replace(source, replacement, 1)

        return relative_path

    @property
    def vcs_exclusion_files(self):
        if self.__vcs_exclusion_files is None:
            exclusion_files = {'git': [], 'hg': []}

            local_gitignore = locate_file(self.root, '.gitignore')
            if local_gitignore is not None:
                exclusion_files['git'].append(local_gitignore)

            local_hgignore = locate_file(self.root, '.hgignore')
            if local_hgignore is not None:
                exclusion_files['hg'].append(local_hgignore)

            self.__vcs_exclusion_files = exclusion_files

        return self.__vcs_exclusion_files

    def load_vcs_exclusion_patterns(self):
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
                    elif exact_line.startswith('syntax: '):
                        glob_mode = False
                        continue
                    elif glob_mode:
                        patterns.append(line)

        return patterns

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

    def default_only_include(self):
        return []

    def default_global_exclude(self):
        patterns = ['*.py[cdo]', f'/{DEFAULT_BUILD_DIRECTORY}']
        patterns.sort()
        return patterns

    def get_force_include(self):
        force_include = self.force_include.copy()
        force_include.update(self.build_force_include)
        return force_include

    @contextmanager
    def set_build_data(self, build_data):
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
                        self.build_reserved_paths.add(os.path.relpath(source, self.root))
                    # Ignore target files only
                    # ../out.ext -> ../in.ext
                    elif os.path.isfile(source):
                        self.build_reserved_paths.add(target)

            yield
        finally:
            self.build_artifact_spec = None
            self.build_force_include.clear()
            self.build_reserved_paths.clear()


def env_var_enabled(env_var, default=False):
    if env_var in os.environ:
        return os.environ[env_var] in ('1', 'true')
    else:
        return default
