from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING, Any, Callable

from hatchling.builders.config import BuilderConfig
from hatchling.builders.plugin.interface import BuilderInterface

if TYPE_CHECKING:
    from types import TracebackType


class BinaryBuilderConfig(BuilderConfig):
    SUPPORTED_VERSIONS = ('3.12', '3.11', '3.10', '3.9', '3.8', '3.7')

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.__scripts: list[str] | None = None
        self.__python_version: str | None = None
        self.__pyapp_version: str | None = None
        self.__env_vars: dict[str, str] | None = None
        self.__outputs: list[dict[str, Any]] | None = None

    @property
    def scripts(self) -> list[str]:
        if self.__scripts is None:
            known_scripts = self.builder.metadata.core.scripts
            scripts = self.target_config.get('scripts', [])

            if not isinstance(scripts, list):
                message = f'Field `tool.hatch.build.targets.{self.plugin_name}.scripts` must be an array'
                raise TypeError(message)

            for i, script in enumerate(scripts, 1):
                if not isinstance(script, str):
                    message = (
                        f'Script #{i} of field `tool.hatch.build.targets.{self.plugin_name}.scripts` must be a string'
                    )
                    raise TypeError(message)

                if script not in known_scripts:
                    message = f'Unknown script in field `tool.hatch.build.targets.{self.plugin_name}.scripts`: {script}'
                    raise ValueError(message)

            self.__scripts = sorted(set(scripts)) if scripts else list(known_scripts)

        return self.__scripts

    @property
    def python_version(self) -> str:
        if self.__python_version is None:
            python_version = self.target_config.get('python-version', '')

            if not isinstance(python_version, str):
                message = f'Field `tool.hatch.build.targets.{self.plugin_name}.python-version` must be a string'
                raise TypeError(message)

            if not python_version and 'PYAPP_DISTRIBUTION_SOURCE' not in os.environ:
                for supported_version in self.SUPPORTED_VERSIONS:
                    if self.builder.metadata.core.python_constraint.contains(supported_version):
                        python_version = supported_version
                        break
                else:
                    message = 'Field `project.requires-python` is incompatible with the known distributions'
                    raise ValueError(message)

            self.__python_version = python_version

        return self.__python_version

    @property
    def pyapp_version(self) -> str:
        if self.__pyapp_version is None:
            pyapp_version = self.target_config.get('pyapp-version', '')

            if not isinstance(pyapp_version, str):
                message = f'Field `tool.hatch.build.targets.{self.plugin_name}.pyapp-version` must be a string'
                raise TypeError(message)

            self.__pyapp_version = pyapp_version

        return self.__pyapp_version

    @property
    def env_vars(self) -> dict[str, str]:
        if self.__env_vars is None:
            env_vars = self.target_config.get('env-vars')

            if env_vars is None:
                self.__env_vars = {}
            elif isinstance(env_vars, dict):
                self.__env_vars = env_vars
            else:
                message = f'Field `tool.hatch.build.targets.{self.plugin_name}.env-vars` must be a table'
                raise TypeError(message)

        return self.__env_vars

    @property
    def outputs(self) -> list[dict[str, Any]]:
        """
        Allows specifying multiple build targets, each with its own options/environment variables.

        This extends the previously non-customizable script build targets by full control over what is built.
        """
        if self.__outputs is None:
            outputs = self.target_config.get('outputs')

            if not outputs:  # None or empty table
                # Fill in the default build targets.
                # First check the scripts section, if it is empty, fall-back to the default build target.
                if self.scripts:
                    self.__outputs = [
                        {
                            'exe_stem': f'{script}-{{version}}',  # version will be interpolated later
                            'env-vars': {'PYAPP_EXEC_SPEC': self.builder.metadata.core.scripts[script]},
                        }
                        for script in self.scripts
                    ]
                else:  # the default if nothing is defined - at least one empty table must be defined
                    self.__outputs = [{}]
            elif isinstance(outputs, list):
                self.__outputs = outputs
            else:
                message = f'Field `tool.hatch.build.targets.{self.plugin_name}.outputs` must be an array of tables'
                raise TypeError(message)

        return self.__outputs


class BinaryBuilder(BuilderInterface):
    """
    Build binaries
    """

    PLUGIN_NAME = 'binary'

    def get_version_api(self) -> dict[str, Callable]:
        return {'bootstrap': self.build_bootstrap}

    def get_default_versions(self) -> list[str]:  # noqa: PLR6301
        return ['bootstrap']

    def clean(
        self,
        directory: str,
        versions: list[str],  # noqa: ARG002
    ) -> None:
        import shutil

        app_dir = os.path.join(directory, self.PLUGIN_NAME)
        if os.path.isdir(app_dir):
            shutil.rmtree(app_dir)

    def build_bootstrap(
        self,
        directory: str,
        **build_data: Any,  # noqa: ARG002
    ) -> str:
        import shutil
        import tempfile

        app_dir = os.path.join(directory, self.PLUGIN_NAME)
        if not os.path.isdir(app_dir):
            os.makedirs(app_dir)

        for output_spec in self.config.outputs:
            env_vars = {  # merge options from the parent options table and the build target options table
                **self.config.env_vars,
                **output_spec.get('env-vars', {}),
            }

            with EnvVars(env_vars):
                cargo_path = os.environ.get('CARGO', '')
                if not cargo_path:
                    if not shutil.which('cargo'):
                        message = 'Executable `cargo` could not be found on PATH'
                        raise OSError(message)

                    cargo_path = 'cargo'

                on_windows = sys.platform == 'win32'
                base_env = dict(os.environ)
                base_env['PYAPP_PROJECT_NAME'] = self.metadata.name
                base_env['PYAPP_PROJECT_VERSION'] = self.metadata.version

                if self.config.python_version:
                    base_env['PYAPP_PYTHON_VERSION'] = self.config.python_version

                # https://doc.rust-lang.org/cargo/reference/config.html#buildtarget
                build_target = os.environ.get('CARGO_BUILD_TARGET', '')

                # This will determine whether we install from crates.io or build locally and is currently required for
                # cross compilation: https://github.com/cross-rs/cross/issues/1215
                repo_path = os.environ.get('PYAPP_REPO', '')

                with tempfile.TemporaryDirectory() as temp_dir:
                    exe_name = 'pyapp.exe' if on_windows else 'pyapp'
                    if repo_path:
                        context_dir = repo_path
                        target_dir = os.path.join(temp_dir, 'build')
                        if build_target:
                            temp_exe_path = os.path.join(target_dir, build_target, 'release', exe_name)
                        else:
                            temp_exe_path = os.path.join(target_dir, 'release', exe_name)
                        install_command = [cargo_path, 'build', '--release', '--target-dir', target_dir]
                    else:
                        context_dir = temp_dir
                        temp_exe_path = os.path.join(temp_dir, 'bin', exe_name)
                        install_command = [cargo_path, 'install', 'pyapp', '--force', '--root', temp_dir]
                        if self.config.pyapp_version:
                            install_command.extend(['--version', self.config.pyapp_version])

                    self.cargo_build(install_command, cwd=context_dir, env=base_env)

                    exe_stem_template = output_spec.get('exe-stem', '{name}-{version}')
                    exe_stem = exe_stem_template.format(name=self.metadata.name, version=self.metadata.version)
                    if build_target:
                        exe_stem = f'{exe_stem}-{build_target}'

                    exe_path = os.path.join(app_dir, f'{exe_stem}.exe' if on_windows else exe_stem)
                    shutil.move(temp_exe_path, exe_path)

        return app_dir

    def cargo_build(self, *args: Any, **kwargs: Any) -> None:
        import subprocess

        if self.app.verbosity < 0:
            kwargs['stdout'] = subprocess.PIPE
            kwargs['stderr'] = subprocess.STDOUT

        process = subprocess.run(*args, **kwargs)  # noqa: PLW1510
        if process.returncode:
            message = f'Compilation failed (code {process.returncode})'
            raise OSError(message)

    @classmethod
    def get_config_class(cls) -> type[BinaryBuilderConfig]:
        return BinaryBuilderConfig


class EnvVars(dict):
    """
    Context manager to temporarily set environment variables
    """

    def __init__(self, env_vars: dict) -> None:
        super().__init__(os.environ)
        self.old_env = dict(self)
        self.update(env_vars)

    def __enter__(self) -> None:
        os.environ.clear()
        os.environ.update(self)

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> None:
        os.environ.clear()
        os.environ.update(self.old_env)
