from __future__ import annotations

import os
from typing import Literal

from platformdirs import user_cache_dir, user_data_dir
from pydantic import BaseModel

from hatch.utils.structures import PydanticSpinnerType, StyleType  # noqa: TCH001


class ConfigurationError(Exception):
    def __init__(self, *args, location):
        self.location = location
        super().__init__(*args)

    def __str__(self):
        return f'Error parsing config:\n{self.location}\n  {super().__str__()}'

type DeepDict = dict[str, bool | str | DeepDict]

class BaseConfig(BaseModel, validate_assignment=True, validate_default=True, validate_return=True):
    @property
    def raw_data(self) -> DeepDict:
        d: DeepDict = {}
        for k, v in self.__dict__.items():
            if v is not None:
                if hasattr(v, 'raw_data'):
                    d[k] = v.raw_data
                elif isinstance(v, dict):
                    d[k] = {i: (j.raw_data if hasattr(j, 'raw_data') else j) for i, j in v.items()}
                elif isinstance(v, list):
                    d[k] = [(i.raw_data if hasattr(i, 'raw_data') else i) for i in v]
                else:
                    d[k] = v
        return d


class DirsConfig(BaseConfig):
    python: str = 'isolated'
    cache: str = ''
    data: str = ''
    env: dict[str, str] = {}
    project: str | list[str] = []

    def model_post_init(self, _) -> None:
        if not self.cache:
            self.cache = user_cache_dir('hatch', appauthor=False)
        if not self.data:
            self.data = user_data_dir('hatch', appauthor=False)


class ShellConfig(BaseConfig):
    name: str = ''
    path: str = ''
    args: list[str] = []

    def model_post_init(self, _) -> None:
        if not self.path:
            self.path = self.name

    @property
    def raw_data(self) -> DeepDict:
        if not self.args and (self.name == self.path):
            return self.name
        return super().raw_data


class LicenseConfig(BaseConfig):
    headers: bool = True
    default: list[str] = ['MIT']


class TemplateConfig(BaseConfig):
    name: str = ''
    email: str = ''
    licenses: LicenseConfig = {}
    plugins: dict[str, dict[str, bool | str]] = {'default': {'ci': False, 'src-layout': True, 'tests': True}}

    def model_post_init(self, _) -> None:
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
    info: StyleType = 'bold'
    success: StyleType = 'bold cyan'
    error: StyleType = 'bold red'
    warning: StyleType = 'bold yellow'
    waiting: StyleType = 'bold magenta'
    debug: StyleType = 'bold'
    spinner: PydanticSpinnerType = 'simpleDotsScrolling'

class TerminalConfig(BaseConfig):
    styles: StylesConfig = {}

    def model_post_init(self, _) -> None:
        if not self.styles:
            self.styles = StylesConfig()


class ProjectConfig(BaseConfig):
    location: str

    @property
    def raw_data(self) -> str:
        return self.location


class RootConfig(BaseConfig):
    dirs: DirsConfig = {}
    mode: Literal['local', 'aware', 'project'] = 'local'
    project: str = ''
    projects: dict[str, ProjectConfig | str] = {}
    publish: dict[str, dict[str, str]] = {'index': {'repo': 'main'}}
    shell: str | ShellConfig = ''
    template: TemplateConfig = {}
    terminal: TerminalConfig = {}

    def model_post_init(self, _) -> None:
        if not self.template:
            self.template = TemplateConfig()
        if not self.terminal:
            self.terminal = TerminalConfig()
        if not self.dirs:
            self.dirs = DirsConfig()
        self.projects = {k: (ProjectConfig(location=v) if isinstance(v, str) else v) for k, v in self.projects.items()}

        if isinstance(self.shell, str):
            self.shell = ShellConfig(name=self.shell)
