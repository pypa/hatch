from __future__ import annotations

from typing import Optional

from ..config.user import ConfigFile, RootConfig
from ..project.core import Project
from ..utils.fs import Path
from ..utils.platform import Platform
from .terminal import Terminal


class Application(Terminal):
    def __init__(self, exit_func, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.platform = Platform(self.display_raw)
        self.__exit_func = exit_func

        self.config_file = ConfigFile()
        self.quiet = self.verbosity < 0
        self.verbose = self.verbosity > 0

        # Lazily set these as we acquire more knowledge about the environment
        self.data_dir: Optional[Path] = None
        self.cache_dir: Optional[Path] = None
        self.project: Optional[Project] = None
        self.env: Optional[str] = None
        self.env_active: Optional[str] = None

    @property
    def plugins(self):
        return self.project.plugin_manager

    @property
    def config(self) -> RootConfig:
        return self.config_file.model

    def get_environment(self, env_name=None):
        if env_name is None:
            env_name = self.env

        if env_name not in self.project.config.envs:
            self.abort(f'Unknown environment: {env_name}')

        config = self.project.config.envs[env_name]
        environment_type = config['type']
        environment_class = self.plugins.environment.get(environment_type)
        if environment_class is None:
            self.abort(f'Environment `{env_name}` has unknown type: {environment_type}')

        self.project.config.finalize_env_overrides(environment_class.get_option_types())

        data_dir = self.get_env_directory(environment_type)

        return environment_class(
            self.project.location,
            self.project.metadata,
            env_name,
            config,
            data_dir,
            self.platform,
            self.verbosity,
            self.get_safe_application(),
        )

    # Ensure that this method is clearly written since it is
    # used for documenting the life cycle of environments.
    def prepare_environment(self, environment):
        if not environment.exists():
            with self.status_waiting(f'Creating environment: {environment.name}'):
                environment.create()

            if not environment.skip_install:
                if environment.pre_install_commands:
                    with self.status_waiting('Running pre-installation commands'):
                        for process in environment.run_shell_commands(environment.pre_install_commands):
                            if process.returncode:
                                self.abort(f'Failed with exit code: {process.returncode}', code=process.returncode)

                if environment.dev_mode:
                    with self.status_waiting('Installing project in development mode'):
                        environment.install_project_dev_mode()
                else:
                    with self.status_waiting('Installing project'):
                        environment.install_project()

                if environment.post_install_commands:
                    with self.status_waiting('Running post-installation commands'):
                        for process in environment.run_shell_commands(environment.post_install_commands):
                            if process.returncode:
                                self.abort(f'Failed with exit code: {process.returncode}', code=process.returncode)

        if not environment.dependencies_in_sync():
            with self.status_waiting('Syncing dependencies'):
                environment.sync_dependencies()

    def get_env_directory(self, environment_type):
        directory = self.config.dirs.env

        if directory == 'isolated':
            return self.data_dir / 'env' / environment_type
        elif directory == 'local':
            return self.project.location / '.env' / environment_type
        else:
            return Path(directory).resolve() / 'env' / environment_type

    def abort(self, text='', code=1, **kwargs):
        if text:
            self.display_error(text, **kwargs)
        self.__exit_func(code)

    def get_safe_application(self) -> SafeApplication:
        return SafeApplication(self)


class SafeApplication:
    def __init__(self, app: Application):
        self.abort = app.abort
        self.display_info = app.display_info
        self.display_error = app.display_error
        self.display_success = app.display_success
        self.display_waiting = app.display_waiting
        self.display_warning = app.display_warning
        self.display_debug = app.display_debug
        self.display_mini_header = app.display_mini_header
        # Divergence from what the backend provides
        self.prompt = app.prompt
        self.status_waiting = app.status_waiting
