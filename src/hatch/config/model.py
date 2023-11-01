from __future__ import annotations

import os
from typing import Any, Dict, List, cast

FIELD_TO_PARSE: object = object()


class ConfigurationError(Exception):
    def __init__(self, *args: Any, location: str) -> None:
        self.location = location
        super().__init__(*args)

    def __str__(self) -> str:
        return f'Error parsing config:\n{self.location}\n  {super().__str__()}'


def parse_config(obj: LazilyParsedConfig | list[Any] | dict[Any, Any]) -> None:
    if isinstance(obj, LazilyParsedConfig):
        obj.parse_fields()
    elif isinstance(obj, list):
        for o in obj:
            parse_config(o)
    elif isinstance(obj, dict):
        for o in obj.values():
            parse_config(o)


class LazilyParsedConfig:
    def __init__(self, config: dict, steps: tuple = ()) -> None:
        self.raw_data = config
        self.steps = steps

    def parse_fields(self) -> None:
        for attribute in self.__dict__:
            _, prefix, name = attribute.partition('_field_')
            if prefix:
                parse_config(getattr(self, name))

    def raise_error(self, message: str, *, extra_steps: tuple = ()) -> ConfigurationError:
        import inspect

        field = inspect.currentframe().f_back.f_code.co_name  # type: ignore
        raise ConfigurationError(message, location=' -> '.join([*self.steps, field, *extra_steps]))


class RootConfig(LazilyParsedConfig):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._field_mode = FIELD_TO_PARSE
        self._field_project = FIELD_TO_PARSE
        self._field_shell = FIELD_TO_PARSE
        self._field_dirs = FIELD_TO_PARSE
        self._field_projects = FIELD_TO_PARSE
        self._field_publish = FIELD_TO_PARSE
        self._field_template = FIELD_TO_PARSE
        self._field_terminal = FIELD_TO_PARSE

    @property
    def mode(self) -> str:
        if self._field_mode is FIELD_TO_PARSE:
            if 'mode' in self.raw_data:
                mode = self.raw_data['mode']
                if not isinstance(mode, str):
                    self.raise_error('must be a string')

                valid_modes = ('aware', 'local', 'project')
                if mode not in valid_modes:
                    self.raise_error(f'must be one of: {", ".join(valid_modes)}')

                self._field_mode = mode
            else:
                self._field_mode = self.raw_data['mode'] = 'local'

        return cast(str, self._field_mode)

    @mode.setter
    def mode(self, value: str) -> None:
        self.raw_data['mode'] = value
        self._field_mode = FIELD_TO_PARSE

    @property
    def project(self) -> str:
        if self._field_project is FIELD_TO_PARSE:
            if 'project' in self.raw_data:
                project = self.raw_data['project']
                if not isinstance(project, str):
                    self.raise_error('must be a string')

                self._field_project = project
            else:
                self._field_project = self.raw_data['project'] = ''

        return cast(str, self._field_project)

    @project.setter
    def project(self, value: str) -> None:
        self.raw_data['project'] = value
        self._field_project = FIELD_TO_PARSE

    @property
    def shell(self) -> ShellConfig:
        if self._field_shell is FIELD_TO_PARSE:
            if 'shell' in self.raw_data:
                shell = self.raw_data['shell']
                if isinstance(shell, str):
                    self._field_shell = ShellConfig({'name': shell}, ('shell',))
                elif isinstance(shell, dict):
                    self._field_shell = ShellConfig(shell, ('shell',))
                else:
                    self.raise_error('must be a string or table')
            else:
                self.raw_data['shell'] = ''
                self._field_shell = ShellConfig({'name': ''}, ('shell',))

        return cast(ShellConfig, self._field_shell)

    @shell.setter
    def shell(self, value: ShellConfig) -> None:
        self.raw_data['shell'] = value
        self._field_shell = FIELD_TO_PARSE

    @property
    def dirs(self) -> DirsConfig:
        if self._field_dirs is FIELD_TO_PARSE:
            if 'dirs' in self.raw_data:
                dirs = self.raw_data['dirs']
                if not isinstance(dirs, dict):
                    self.raise_error('must be a table')

                self._field_dirs = DirsConfig(dirs, ('dirs',))
            else:
                dirs = {}
                self.raw_data['dirs'] = dirs
                self._field_dirs = DirsConfig(dirs, ('dirs',))

        return cast(DirsConfig, self._field_dirs)

    @dirs.setter
    def dirs(self, value: DirsConfig) -> None:
        self.raw_data['dirs'] = value
        self._field_dirs = FIELD_TO_PARSE

    @property
    def projects(self) -> dict[str, ProjectConfig]:
        if self._field_projects is FIELD_TO_PARSE:
            if 'projects' in self.raw_data:
                projects = self.raw_data['projects']
                if not isinstance(projects, dict):
                    self.raise_error('must be a table')

                project_data = {}
                for name, data in projects.items():
                    if isinstance(data, str):
                        project_data[name] = ProjectConfig({'location': data}, ('projects', name))
                    elif isinstance(data, dict):
                        project_data[name] = ProjectConfig(data, ('projects', name))
                    else:
                        self.raise_error('must be a string or table', extra_steps=(name,))

                self._field_projects = project_data
            else:
                self._field_projects = self.raw_data['projects'] = {}

        return cast(Dict[str, ProjectConfig], self._field_projects)

    @projects.setter
    def projects(self, value: dict[str, ProjectConfig]) -> None:
        self.raw_data['projects'] = value
        self._field_projects = FIELD_TO_PARSE

    @property
    def publish(self) -> dict[str, dict[str, str]]:
        if self._field_publish is FIELD_TO_PARSE:
            if 'publish' in self.raw_data:
                publish = self.raw_data['publish']
                if not isinstance(publish, dict):
                    self.raise_error('must be a table')

                for name, data in publish.items():
                    if not isinstance(data, dict):
                        self.raise_error('must be a table', extra_steps=(name,))

                self._field_publish = publish
            else:
                self._field_publish = self.raw_data['publish'] = {'index': {'repo': 'main'}}

        return cast(Dict[str, Dict[str, str]], self._field_publish)

    @publish.setter
    def publish(self, value: dict[str, dict[str, str]]) -> None:
        self.raw_data['publish'] = value
        self._field_publish = FIELD_TO_PARSE

    @property
    def template(self) -> TemplateConfig:
        if self._field_template is FIELD_TO_PARSE:
            if 'template' in self.raw_data:
                template = self.raw_data['template']
                if not isinstance(template, dict):
                    self.raise_error('must be a table')

                self._field_template = TemplateConfig(template, ('template',))
            else:
                template = {}
                self.raw_data['template'] = template
                self._field_template = TemplateConfig(template, ('template',))

        return cast(TemplateConfig, self._field_template)

    @template.setter
    def template(self, value: TemplateConfig) -> None:
        self.raw_data['template'] = value
        self._field_template = FIELD_TO_PARSE

    @property
    def terminal(self) -> TerminalConfig:
        if self._field_terminal is FIELD_TO_PARSE:
            if 'terminal' in self.raw_data:
                terminal = self.raw_data['terminal']
                if not isinstance(terminal, dict):
                    self.raise_error('must be a table')

                self._field_terminal = TerminalConfig(terminal, ('terminal',))
            else:
                terminal = {}
                self.raw_data['terminal'] = terminal
                self._field_terminal = TerminalConfig(terminal, ('terminal',))

        return cast(TerminalConfig, self._field_terminal)

    @terminal.setter
    def terminal(self, value: TerminalConfig) -> None:
        self.raw_data['terminal'] = value
        self._field_terminal = FIELD_TO_PARSE


class ShellConfig(LazilyParsedConfig):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._field_name = FIELD_TO_PARSE
        self._field_path = FIELD_TO_PARSE
        self._field_args = FIELD_TO_PARSE

    @property
    def name(self) -> str:
        if self._field_name is FIELD_TO_PARSE:
            if 'name' in self.raw_data:
                name = self.raw_data['name']
                if not isinstance(name, str):
                    self.raise_error('must be a string')

                self._field_name = name
            else:
                self.raise_error('required field')

        return cast(str, self._field_name)

    @name.setter
    def name(self, value: str) -> None:
        self.raw_data['name'] = value
        self._field_name = FIELD_TO_PARSE

    @property
    def path(self) -> str:
        if self._field_path is FIELD_TO_PARSE:
            if 'path' in self.raw_data:
                path = self.raw_data['path']
                if not isinstance(path, str):
                    self.raise_error('must be a string')

                self._field_path = path
            else:
                self._field_path = self.raw_data['path'] = self.name

        return cast(str, self._field_path)

    @path.setter
    def path(self, value: str) -> None:
        self.raw_data['path'] = value
        self._field_path = FIELD_TO_PARSE

    @property
    def args(self) -> list[str]:
        if self._field_args is FIELD_TO_PARSE:
            if 'args' in self.raw_data:
                args = self.raw_data['args']
                if not isinstance(args, list):
                    self.raise_error('must be an array')

                for i, entry in enumerate(args, 1):
                    if not isinstance(entry, str):
                        self.raise_error('must be a string', extra_steps=(str(i),))

                self._field_args = args
            else:
                self._field_args = self.raw_data['args'] = []

        return cast(List[str], self._field_args)

    @args.setter
    def args(self, value: list[str]) -> None:
        self.raw_data['args'] = value
        self._field_args = FIELD_TO_PARSE


class DirsConfig(LazilyParsedConfig):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._field_project = FIELD_TO_PARSE
        self._field_env = FIELD_TO_PARSE
        self._field_python = FIELD_TO_PARSE
        self._field_data = FIELD_TO_PARSE
        self._field_cache = FIELD_TO_PARSE

    @property
    def project(self) -> list[str]:
        if self._field_project is FIELD_TO_PARSE:
            if 'project' in self.raw_data:
                project = self.raw_data['project']
                if not isinstance(project, list):
                    self.raise_error('must be an array')

                for i, entry in enumerate(project, 1):
                    if not isinstance(entry, str):
                        self.raise_error('must be a string', extra_steps=(str(i),))

                self._field_project = project
            else:
                self._field_project = self.raw_data['project'] = []

        return cast(List[str], self._field_project)

    @project.setter
    def project(self, value: list[str]) -> None:
        self.raw_data['project'] = value
        self._field_project = FIELD_TO_PARSE

    @property
    def env(self) -> dict[str, str]:
        if self._field_env is FIELD_TO_PARSE:
            if 'env' in self.raw_data:
                env = self.raw_data['env']
                if not isinstance(env, dict):
                    self.raise_error('must be a table')

                for key, value in env.items():
                    if not isinstance(value, str):
                        self.raise_error('must be a string', extra_steps=(key,))

                self._field_env = env
            else:
                self._field_env = self.raw_data['env'] = {}

        return cast(Dict[str, str], self._field_env)

    @env.setter
    def env(self, value: dict[str, str]) -> None:
        self.raw_data['env'] = value
        self._field_env = FIELD_TO_PARSE

    @property
    def python(self) -> str:
        if self._field_python is FIELD_TO_PARSE:
            if 'python' in self.raw_data:
                python = self.raw_data['python']
                if not isinstance(python, str):
                    self.raise_error('must be a string')

                self._field_python = python
            else:
                self._field_python = self.raw_data['python'] = 'shared'

        return cast(str, self._field_python)

    @python.setter
    def python(self, value: str) -> None:
        self.raw_data['python'] = value
        self._field_python = FIELD_TO_PARSE

    @property
    def data(self) -> str:
        if self._field_data is FIELD_TO_PARSE:
            if 'data' in self.raw_data:
                data = self.raw_data['data']
                if not isinstance(data, str):
                    self.raise_error('must be a string')

                self._field_data = data
            else:
                from platformdirs import user_data_dir

                self._field_data = self.raw_data['data'] = user_data_dir('hatch', appauthor=False)

        return cast(str, self._field_data)

    @data.setter
    def data(self, value: str) -> None:
        self.raw_data['data'] = value
        self._field_data = FIELD_TO_PARSE

    @property
    def cache(self) -> str:
        if self._field_cache is FIELD_TO_PARSE:
            if 'cache' in self.raw_data:
                cache = self.raw_data['cache']
                if not isinstance(cache, str):
                    self.raise_error('must be a string')

                self._field_cache = cache
            else:
                from platformdirs import user_cache_dir

                self._field_cache = self.raw_data['cache'] = user_cache_dir('hatch', appauthor=False)

        return cast(str, self._field_cache)

    @cache.setter
    def cache(self, value: str) -> None:
        self.raw_data['cache'] = value
        self._field_cache = FIELD_TO_PARSE


class ProjectConfig(LazilyParsedConfig):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._field_location = FIELD_TO_PARSE

    @property
    def location(self) -> str:
        if self._field_location is FIELD_TO_PARSE:
            if 'location' in self.raw_data:
                location = self.raw_data['location']
                if not isinstance(location, str):
                    self.raise_error('must be a string')

                self._field_location = location
            else:
                self.raise_error('required field')

        return cast(str, self._field_location)

    @location.setter
    def location(self, value: str) -> None:
        self.raw_data['location'] = value
        self._field_location = FIELD_TO_PARSE


class TemplateConfig(LazilyParsedConfig):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._field_name = FIELD_TO_PARSE
        self._field_email = FIELD_TO_PARSE
        self._field_licenses = FIELD_TO_PARSE
        self._field_plugins = FIELD_TO_PARSE

    @property
    def name(self) -> str:
        if self._field_name is FIELD_TO_PARSE:
            if 'name' in self.raw_data:
                name = self.raw_data['name']
                if not isinstance(name, str):
                    self.raise_error('must be a string')

                self._field_name = name
            else:
                name = os.environ.get('GIT_AUTHOR_NAME')
                if name is None:
                    import subprocess

                    try:
                        name = subprocess.check_output(['git', 'config', '--get', 'user.name'], text=True).strip()
                    except Exception:
                        name = 'U.N. Owen'

                self._field_name = self.raw_data['name'] = name

        return cast(str, self._field_name)

    @name.setter
    def name(self, value: str) -> None:
        self.raw_data['name'] = value
        self._field_name = FIELD_TO_PARSE

    @property
    def email(self) -> str:
        if self._field_email is FIELD_TO_PARSE:
            if 'email' in self.raw_data:
                email = self.raw_data['email']
                if not isinstance(email, str):
                    self.raise_error('must be a string')

                self._field_email = email
            else:
                email = os.environ.get('GIT_AUTHOR_EMAIL')
                if email is None:
                    import subprocess

                    try:
                        email = subprocess.check_output(['git', 'config', '--get', 'user.email'], text=True).strip()
                    except Exception:
                        email = 'void@some.where'

                self._field_email = self.raw_data['email'] = email

        return cast(str, self._field_email)

    @email.setter
    def email(self, value: str) -> None:
        self.raw_data['email'] = value
        self._field_email = FIELD_TO_PARSE

    @property
    def licenses(self) -> LicensesConfig:
        if self._field_licenses is FIELD_TO_PARSE:
            if 'licenses' in self.raw_data:
                licenses = self.raw_data['licenses']
                if not isinstance(licenses, dict):
                    self.raise_error('must be a table')

                self._field_licenses = LicensesConfig(licenses, (*self.steps, 'licenses'))
            else:
                licenses = {}
                self.raw_data['licenses'] = licenses
                self._field_licenses = LicensesConfig(licenses, (*self.steps, 'licenses'))

        return cast(LicensesConfig, self._field_licenses)

    @licenses.setter
    def licenses(self, value: LicensesConfig) -> None:
        self.raw_data['licenses'] = value
        self._field_licenses = FIELD_TO_PARSE

    @property
    def plugins(self) -> dict[str, dict[str, bool]]:
        if self._field_plugins is FIELD_TO_PARSE:
            if 'plugins' in self.raw_data:
                plugins = self.raw_data['plugins']
                if not isinstance(plugins, dict):
                    self.raise_error('must be a table')

                for name, data in plugins.items():
                    if not isinstance(data, dict):
                        self.raise_error('must be a table', extra_steps=(name,))

                self._field_plugins = plugins
            else:
                self._field_plugins = self.raw_data['plugins'] = {
                    'default': {'tests': True, 'ci': False, 'src-layout': True}
                }

        return cast(Dict[str, Dict[str, bool]], self._field_plugins)

    @plugins.setter
    def plugins(self, value: dict[str, dict[str, bool]]) -> None:
        self.raw_data['plugins'] = value
        self._field_plugins = FIELD_TO_PARSE


class LicensesConfig(LazilyParsedConfig):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._field_headers = FIELD_TO_PARSE
        self._field_default = FIELD_TO_PARSE

    @property
    def headers(self) -> bool:
        if self._field_headers is FIELD_TO_PARSE:
            if 'headers' in self.raw_data:
                headers = self.raw_data['headers']
                if not isinstance(headers, bool):
                    self.raise_error('must be a boolean')

                self._field_headers = headers
            else:
                self._field_headers = self.raw_data['headers'] = True

        return cast(bool, self._field_headers)

    @headers.setter
    def headers(self, value: bool) -> None:  # noqa: FBT001
        self.raw_data['headers'] = value
        self._field_headers = FIELD_TO_PARSE

    @property
    def default(self) -> list[str]:
        if self._field_default is FIELD_TO_PARSE:
            if 'default' in self.raw_data:
                default = self.raw_data['default']
                if not isinstance(default, list):
                    self.raise_error('must be an array')

                for i, entry in enumerate(default, 1):
                    if not isinstance(entry, str):
                        self.raise_error('must be a string', extra_steps=(str(i),))

                self._field_default = default
            else:
                self._field_default = self.raw_data['default'] = ['MIT']

        return cast(List[str], self._field_default)

    @default.setter
    def default(self, value: list[str]) -> None:
        self.raw_data['default'] = value
        self._field_default = FIELD_TO_PARSE


class TerminalConfig(LazilyParsedConfig):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._field_styles = FIELD_TO_PARSE

    @property
    def styles(self) -> StylesConfig:
        if self._field_styles is FIELD_TO_PARSE:
            if 'styles' in self.raw_data:
                styles = self.raw_data['styles']
                if not isinstance(styles, dict):
                    self.raise_error('must be a table')

                self._field_styles = StylesConfig(styles, (*self.steps, 'styles'))
            else:
                styles = {}
                self.raw_data['styles'] = styles
                self._field_styles = StylesConfig(styles, (*self.steps, 'styles'))

        return cast(StylesConfig, self._field_styles)

    @styles.setter
    def styles(self, value: StylesConfig) -> None:
        self.raw_data['styles'] = value
        self._field_styles = FIELD_TO_PARSE


class StylesConfig(LazilyParsedConfig):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._field_info = FIELD_TO_PARSE
        self._field_success = FIELD_TO_PARSE
        self._field_error = FIELD_TO_PARSE
        self._field_warning = FIELD_TO_PARSE
        self._field_waiting = FIELD_TO_PARSE
        self._field_debug = FIELD_TO_PARSE
        self._field_spinner = FIELD_TO_PARSE

    @property
    def info(self) -> str:
        if self._field_info is FIELD_TO_PARSE:
            if 'info' in self.raw_data:
                info = self.raw_data['info']
                if not isinstance(info, str):
                    self.raise_error('must be a string')

                self._field_info = info
            else:
                self._field_info = self.raw_data['info'] = 'bold'

        return cast(str, self._field_info)

    @info.setter
    def info(self, value: str) -> None:
        self.raw_data['info'] = value
        self._field_info = FIELD_TO_PARSE

    @property
    def success(self) -> str:
        if self._field_success is FIELD_TO_PARSE:
            if 'success' in self.raw_data:
                success = self.raw_data['success']
                if not isinstance(success, str):
                    self.raise_error('must be a string')

                self._field_success = success
            else:
                self._field_success = self.raw_data['success'] = 'bold cyan'

        return cast(str, self._field_success)

    @success.setter
    def success(self, value: str) -> None:
        self.raw_data['success'] = value
        self._field_success = FIELD_TO_PARSE

    @property
    def error(self) -> str:
        if self._field_error is FIELD_TO_PARSE:
            if 'error' in self.raw_data:
                error = self.raw_data['error']
                if not isinstance(error, str):
                    self.raise_error('must be a string')

                self._field_error = error
            else:
                self._field_error = self.raw_data['error'] = 'bold red'

        return cast(str, self._field_error)

    @error.setter
    def error(self, value: str) -> None:
        self.raw_data['error'] = value
        self._field_error = FIELD_TO_PARSE

    @property
    def warning(self) -> str:
        if self._field_warning is FIELD_TO_PARSE:
            if 'warning' in self.raw_data:
                warning = self.raw_data['warning']
                if not isinstance(warning, str):
                    self.raise_error('must be a string')

                self._field_warning = warning
            else:
                self._field_warning = self.raw_data['warning'] = 'bold yellow'

        return cast(str, self._field_warning)

    @warning.setter
    def warning(self, value: str) -> None:
        self.raw_data['warning'] = value
        self._field_warning = FIELD_TO_PARSE

    @property
    def waiting(self) -> str:
        if self._field_waiting is FIELD_TO_PARSE:
            if 'waiting' in self.raw_data:
                waiting = self.raw_data['waiting']
                if not isinstance(waiting, str):
                    self.raise_error('must be a string')

                self._field_waiting = waiting
            else:
                self._field_waiting = self.raw_data['waiting'] = 'bold magenta'

        return cast(str, self._field_waiting)

    @waiting.setter
    def waiting(self, value: str) -> None:
        self.raw_data['waiting'] = value
        self._field_waiting = FIELD_TO_PARSE

    @property
    def debug(self) -> str:
        if self._field_debug is FIELD_TO_PARSE:
            if 'debug' in self.raw_data:
                debug = self.raw_data['debug']
                if not isinstance(debug, str):
                    self.raise_error('must be a string')

                self._field_debug = debug
            else:
                self._field_debug = self.raw_data['debug'] = 'bold'

        return cast(str, self._field_debug)

    @debug.setter
    def debug(self, value: str) -> None:
        self.raw_data['debug'] = value
        self._field_debug = FIELD_TO_PARSE

    @property
    def spinner(self) -> str:
        if self._field_spinner is FIELD_TO_PARSE:
            if 'spinner' in self.raw_data:
                spinner = self.raw_data['spinner']
                if not isinstance(spinner, str):
                    self.raise_error('must be a string')

                self._field_spinner = spinner
            else:
                self._field_spinner = self.raw_data['spinner'] = 'simpleDotsScrolling'

        return cast(str, self._field_spinner)

    @spinner.setter
    def spinner(self, value: str) -> None:
        self.raw_data['spinner'] = value
        self._field_spinner = FIELD_TO_PARSE
