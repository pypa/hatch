from __future__ import annotations

import os
from typing import Literal

from platformdirs import user_cache_dir, user_data_dir
from pydantic import BaseModel


class ConfigurationError(Exception):
    def __init__(self, *args, location):
        self.location = location
        super().__init__(*args)

    def __str__(self):
        return f'Error parsing config:\n{self.location}\n  {super().__str__()}'


class BaseConfig(BaseModel, validate_assignment=True):
    @property
    def raw_data(self):
        d = {}
        for k, v in self.__dict__.items():
            if v is not None:
                if isinstance(v, BaseConfig):
                    d[k] = v.raw_data
                elif isinstance(v, dict):
                    d[k] = {j: (i.raw_data if isinstance(i, BaseConfig) else i) for j, i in v.items()}
                elif isinstance(v, list):
                    d[k] = [(i.raw_data if isinstance(i, BaseConfig) else i) for i in v]
                else:
                    d[k] = v
        return d

    # @raw_data.setter
    # def raw_data(self, _):
    #     pass


class DirsConfig(BaseConfig):
    python: str = 'isolated'
    cache: str = None
    data: str = None
    env: dict[str, str] = {}
    project: str | list[str] = []

    def model_post_init(self, _):
        if not self.cache:
            self.cache = user_cache_dir('hatch', appauthor=False)
        if not self.data:
            self.data = user_data_dir('hatch', appauthor=False)


class ShellConfig(BaseConfig):
    name: str = ''
    path: str = ''
    args: list[str] = []

    def model_post_init(self, _):
        if not self.path:
            self.path = self.name

    @property
    def raw_data(self):
        if not self.args and (self.name == self.path):
            return self.name
        return super().raw_data


class LicenseConfig(BaseConfig):
    headers: bool = True
    default: list[str] = ['MIT']


class TemplateConfig(BaseConfig):
    name: str = ''
    email: str = ''
    licenses: LicenseConfig = None
    plugins: dict[str, dict[str, bool | str]] = {'default': {'ci': False, 'src-layout': True, 'tests': True}}

    def model_post_init(self, _):
        if not self.licenses:
            self.licenses = LicenseConfig()

        for i in ['name', 'email']:
            if not getattr(self, i):
                try:
                    item = os.getenv(f'GIT_AUTHOR_{i.upper()}')
                    setattr(self, i, item)
                except ValueError:  # ValidationError:
                    try:
                        _ = subprocess.DEVNULL
                    except NameError:
                        import subprocess
                    try:
                        setattr(
                            self,
                            i,
                            subprocess.check_output(
                                ['git', 'config', '--get', f'user.{i}'],  # noqa: S607
                                text=True,
                            ).strip(),
                        )
                    except Exception:  # noqa: BLE001
                        if i == 'name':
                            setattr(self, i, 'U.N. Owen')
                        else:
                            setattr(self, i, 'void@some.where')


class StylesConfig(BaseConfig):
    info: str = 'bold'
    success: str = 'bold cyan'
    error: str = 'bold red'
    warning: str = 'bold yellow'
    waiting: str = 'bold magenta'
    debug: str = 'bold'
    spinner: str = 'simpleDotsScrolling'


class TerminalConfig(BaseConfig):
    styles: StylesConfig = StylesConfig()

    def model_post_init(self, _):
        if not self.styles:
            self.styles = StylesConfig()


class ProjectConfig(BaseConfig):
    location: str

    @property
    def raw_data(self):
        return self.location


class RootConfig(BaseConfig):
    dirs: DirsConfig = None
    mode: Literal['local', 'aware', 'project'] = 'local'
    project: str = ''
    projects: dict[str, ProjectConfig | str] = {}
    publish: dict[str, dict[str, str]] = {'index': {'repo': 'main'}}
    shell: str | ShellConfig = ''
    template: TemplateConfig = None
    terminal: TerminalConfig = None

    def model_post_init(self, _):
        if not self.template:
            self.template = TemplateConfig()
        if not self.terminal:
            self.terminal = TerminalConfig()
        if not self.dirs:
            self.dirs = DirsConfig()
        self.projects = {k: (ProjectConfig(location=v) if isinstance(v, str) else v) for k, v in self.projects.items()}

        if isinstance(self.shell, str):
            self.shell = ShellConfig(name=self.shell)
