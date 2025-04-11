from __future__ import annotations

import re
from collections import defaultdict
from contextlib import contextmanager
from functools import cached_property
from typing import TYPE_CHECKING, Any, Generator, cast

from hatch.project.env import EnvironmentMetadata
from hatch.utils.fs import Path
from hatch.utils.runner import ExecutionContext

if TYPE_CHECKING:
    from hatch.cli.application import Application
    from hatch.config.model import RootConfig
    from hatch.env.plugin.interface import EnvironmentInterface
    from hatch.project.frontend.core import BuildFrontend


class Project:
    def __init__(self, path: Path, *, name: str | None = None, config=None):
        self._path = path

        # From app config
        self.chosen_name = name

        # Lazily attach the current app
        self.__app: Application | None = None

        # Location of pyproject.toml
        self._project_file_path: Path | None = None

        self._root_searched = False
        self._root: Path | None = None
        self._raw_config = config
        self._plugin_manager = None
        self._metadata = None
        self._config = None

        self._explicit_path: Path | None = None

    @property
    def plugin_manager(self):
        if self._plugin_manager is None:
            from hatch.plugin.manager import PluginManager

            self._plugin_manager = PluginManager()

        return self._plugin_manager

    @property
    def config(self):
        if self._config is None:
            from hatch.project.config import ProjectConfig

            self._config = ProjectConfig(self.location, self.metadata.hatch.config, self.plugin_manager)

        return self._config

    @property
    def root(self) -> Path | None:
        if not self._root_searched:
            self._root = self.find_project_root()
            self._root_searched = True

        return self._root

    @property
    def location(self) -> Path:
        return self._explicit_path or self.root or self._path

    def set_path(self, path: Path) -> None:
        self._explicit_path = path

    def set_app(self, app: Application) -> None:
        self.__app = app

    @cached_property
    def app(self) -> Application:
        if self.__app is None:  # no cov
            message = 'The application has not been set'
            raise RuntimeError(message)

        from hatch.cli.application import Application

        return cast(Application, self.__app)

    @cached_property
    def build_env(self) -> EnvironmentInterface:
        # Prevent the default environment from being used as a builder environment
        environment = self.get_environment('hatch-build' if self.app.env == 'default' else self.app.env)
        if not environment.builder:
            self.app.abort(f'Environment `{environment.name}` is not a builder environment')

        return environment

    @cached_property
    def build_frontend(self) -> BuildFrontend:
        from hatch.project.frontend.core import BuildFrontend

        return BuildFrontend(self, self.build_env)

    @cached_property
    def env_metadata(self) -> EnvironmentMetadata:
        return EnvironmentMetadata(self.app.data_dir / 'env' / '.metadata', self.location)

    @cached_property
    def dependency_groups(self) -> dict[str, Any]:
        """
        https://peps.python.org/pep-0735/
        """
        from hatchling.metadata.utils import normalize_project_name

        dependency_groups = self.raw_config.get('dependency-groups', {})

        if not isinstance(dependency_groups, dict):
            message = 'Field `dependency-groups` must be a table'
            raise TypeError(message)

        original_names = defaultdict(list)
        normalized_groups = {}

        for group_name, value in dependency_groups.items():
            normed_group_name = normalize_project_name(group_name)
            original_names[normed_group_name].append(group_name)
            normalized_groups[normed_group_name] = value

        errors = []
        for normed_name, names in original_names.items():
            if len(names) > 1:
                errors.append(f"{normed_name} ({', '.join(names)})")
        if errors:
            msg = f"Field `dependency-groups` contains duplicate names: {', '.join(errors)}"
            raise ValueError(msg)

        return normalized_groups

    def get_environment(self, env_name: str | None = None) -> EnvironmentInterface:
        if env_name is None:
            env_name = self.app.env

        if env_name in self.config.internal_envs:
            config = self.config.internal_envs[env_name]
        elif env_name in self.config.envs:
            config = self.config.envs[env_name]
        else:
            self.app.abort(f'Unknown environment: {env_name}')

        environment_type = config['type']
        environment_class = self.plugin_manager.environment.get(environment_type)
        if environment_class is None:
            self.app.abort(f'Environment `{env_name}` has unknown type: {environment_type}')

        from hatch.env.internal import is_isolated_environment

        if self.location.is_file():
            data_directory = isolated_data_directory = self.app.data_dir / 'env' / environment_type / '.scripts'
        elif is_isolated_environment(env_name, config):
            data_directory = isolated_data_directory = self.app.data_dir / 'env' / '.internal' / env_name
        else:
            data_directory = self.app.get_env_directory(environment_type)
            isolated_data_directory = self.app.data_dir / 'env' / environment_type

        self.config.finalize_env_overrides(environment_class.get_option_types())

        return environment_class(
            self.location,
            self.metadata,
            env_name,
            config,
            self.config.matrix_variables.get(env_name, {}),
            data_directory,
            isolated_data_directory,
            self.app.platform,
            self.app.verbosity,
            self.app,
        )

    # Ensure that this method is clearly written since it is
    # used for documenting the life cycle of environments.
    def prepare_environment(self, environment: EnvironmentInterface):
        if not environment.exists():
            self.env_metadata.reset(environment)

            with environment.app_status_creation():
                environment.create()

            if not environment.skip_install:
                if environment.pre_install_commands:
                    with environment.app_status_pre_installation():
                        self.app.run_shell_commands(
                            ExecutionContext(
                                environment,
                                shell_commands=environment.pre_install_commands,
                                source='pre-install',
                                show_code_on_error=True,
                            )
                        )

                with environment.app_status_project_installation():
                    if environment.dev_mode:
                        environment.install_project_dev_mode()
                    else:
                        environment.install_project()

                if environment.post_install_commands:
                    with environment.app_status_post_installation():
                        self.app.run_shell_commands(
                            ExecutionContext(
                                environment,
                                shell_commands=environment.post_install_commands,
                                source='post-install',
                                show_code_on_error=True,
                            )
                        )

        with environment.app_status_dependency_state_check():
            new_dep_hash = environment.dependency_hash()

        current_dep_hash = self.env_metadata.dependency_hash(environment)
        if new_dep_hash != current_dep_hash:
            with environment.app_status_dependency_installation_check():
                dependencies_in_sync = environment.dependencies_in_sync()

            if not dependencies_in_sync:
                with environment.app_status_dependency_synchronization():
                    environment.sync_dependencies()
                    new_dep_hash = environment.dependency_hash()

            self.env_metadata.update_dependency_hash(environment, new_dep_hash)

    def prepare_build_environment(self, *, targets: list[str] | None = None) -> None:
        from hatch.project.constants import BUILD_BACKEND

        if targets is None:
            targets = ['wheel']

        build_backend = self.metadata.build.build_backend
        with self.location.as_cwd(), self.build_env.get_env_vars():
            if not self.build_env.exists():
                try:
                    self.build_env.check_compatibility()
                except Exception as e:  # noqa: BLE001
                    self.app.abort(f'Environment `{self.build_env.name}` is incompatible: {e}')

            self.prepare_environment(self.build_env)

            extra_dependencies: list[str] = []
            with self.app.status('Inspecting build dependencies'):
                if build_backend != BUILD_BACKEND:
                    for target in targets:
                        if target == 'sdist':
                            extra_dependencies.extend(self.build_frontend.get_requires('sdist'))
                        elif target == 'wheel':
                            extra_dependencies.extend(self.build_frontend.get_requires('wheel'))
                        else:
                            self.app.abort(f'Target `{target}` is not supported by `{build_backend}`')
                else:
                    required_build_deps = self.build_frontend.hatch.get_required_build_deps(targets)
                    if required_build_deps:
                        with self.metadata.context.apply_context(self.build_env.context):
                            extra_dependencies.extend(self.metadata.context.format(dep) for dep in required_build_deps)

            if extra_dependencies:
                self.build_env.dependencies.extend(extra_dependencies)
                with self.build_env.app_status_dependency_synchronization():
                    self.build_env.sync_dependencies()

    def get_dependencies(self) -> tuple[list[str], dict[str, list[str]]]:
        dynamic_fields = {'dependencies', 'optional-dependencies'}
        if not dynamic_fields.intersection(self.metadata.dynamic):
            dependencies: list[str] = self.metadata.core_raw_metadata.get('dependencies', [])
            features: dict[str, list[str]] = self.metadata.core_raw_metadata.get('optional-dependencies', {})
            return dependencies, features

        from hatch.project.constants import BUILD_BACKEND

        self.prepare_build_environment()
        build_backend = self.metadata.build.build_backend
        with self.location.as_cwd(), self.build_env.get_env_vars():
            if build_backend != BUILD_BACKEND:
                project_metadata = self.build_frontend.get_core_metadata()
            else:
                project_metadata = self.build_frontend.hatch.get_core_metadata()

        dynamic_dependencies: list[str] = project_metadata.get('dependencies', [])
        dynamic_features: dict[str, list[str]] = project_metadata.get('optional-dependencies', {})

        return dynamic_dependencies, dynamic_features

    def expand_environments(self, env_name: str) -> list[str]:
        if env_name in self.config.internal_matrices:
            return list(self.config.internal_matrices[env_name]['envs'])

        if env_name in self.config.matrices:
            return list(self.config.matrices[env_name]['envs'])

        if env_name in self.config.internal_envs:
            return [env_name]

        if env_name in self.config.envs:
            return [env_name]

        return []

    @classmethod
    def from_config(cls, config: RootConfig, project: str) -> Project | None:
        # Disallow empty strings
        if not project:
            return None

        if project in config.projects:
            location = config.projects[project].location
            if location:
                return cls(Path(location).resolve(), name=project)
        else:
            for project_dir in config.dirs.project:
                if not project_dir:
                    continue

                location = Path(project_dir, project)
                if location.is_dir():
                    return cls(Path(location).resolve(), name=project)

        return None

    def find_project_root(self) -> Path | None:
        path = self._path

        while True:
            possible_file = path.joinpath('pyproject.toml')
            if possible_file.is_file():
                self._project_file_path = possible_file
                return path

            if path.joinpath('setup.py').is_file():
                return path

            new_path = path.parent
            if new_path == path:
                return None

            path = new_path

    @contextmanager
    def ensure_cwd(self) -> Generator[Path, None, None]:
        cwd = Path.cwd()
        location = self.location
        if location.is_file() or cwd == location or location in cwd.parents:
            yield cwd
        else:
            with location.as_cwd():
                yield location

    @staticmethod
    def canonicalize_name(name: str, *, strict=True) -> str:
        if strict:
            return re.sub(r'[-_.]+', '-', name).lower()

        # Used for creating new projects
        return re.sub(r'[-_. ]+', '-', name).lower()

    @property
    def metadata(self):
        if self._metadata is None:
            from hatchling.metadata.core import ProjectMetadata

            self._metadata = ProjectMetadata(self.location, self.plugin_manager, self.raw_config)

        return self._metadata

    @property
    def raw_config(self):
        if self._raw_config is None:
            if self.root is None or self._project_file_path is None:
                # Assume no pyproject.toml e.g. environment management only
                self._raw_config = {'project': {'name': self.location.name}}
            else:
                from hatch.utils.toml import load_toml_file

                raw_config = load_toml_file(str(self._project_file_path))
                # Assume environment management only
                if 'project' not in raw_config:
                    raw_config['project'] = {'name': self.location.name}

                self._raw_config = raw_config

        return self._raw_config

    def save_config(self, config):
        import tomlkit

        with open(str(self._project_file_path), 'w', encoding='utf-8') as f:
            f.write(tomlkit.dumps(config))

    @staticmethod
    def initialize(project_file_path, template_config):
        import tomlkit

        with open(str(project_file_path), encoding='utf-8') as f:
            raw_config = tomlkit.parse(f.read())

        build_system_config = raw_config.setdefault('build-system', {})

        build_system_config.clear()
        build_system_config['requires'] = ['hatchling']
        build_system_config['build-backend'] = 'hatchling.build'

        project_config = raw_config.get('project')
        if project_config is None:
            raw_config['project'] = project_config = {}

        project_name = project_config.get('name')
        if not project_name:
            project_config['name'] = template_config['project_name_normalized']

        project_description = project_config.get('description')
        if not project_description:
            project_config['description'] = template_config['description']

        project_config['dynamic'] = ['version']

        tool_config = raw_config.get('tool')
        if tool_config is None:
            raw_config['tool'] = tool_config = {}

        hatch_config = tool_config.get('hatch')
        if hatch_config is None:
            tool_config['hatch'] = hatch_config = {}

        version_config = hatch_config.get('version')
        if version_config is None:
            hatch_config['version'] = version_config = {}

        version_config.clear()
        version_config['path'] = f'{template_config["package_name"]}/__init__.py'

        with open(str(project_file_path), 'w', encoding='utf-8') as f:
            f.write(tomlkit.dumps(raw_config))
