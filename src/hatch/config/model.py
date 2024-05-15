from __future__ import annotations

import os
from typing import Any, Literal

from platformdirs import user_cache_dir, user_data_dir
from pydantic import BaseModel, Field, computed_field, field_validator, ValidationError

from rich.errors import StyleSyntaxError
from hatch.utils.pydantic import SpinnerType, StyleType, validate_bool, validate_string, validate_string_strict  # noqa: TCH001

from pydantic_core import core_schema
from rich.spinner import Spinner
from rich.style import Style
from typing_extensions import Annotated

from collections.abc import MutableMapping, Mapping

from tomlkit.items import Bool, String, Item

class BaseConfig(
    BaseModel,
    # Mapping,
    MutableMapping,
    validate_assignment=True,
    validate_default=True,
    validate_return=True,
    extra='allow',
    strict=True
):
    # Class for configurations
    # @computed_field
    @property
    def raw_data(self) -> DeepDict:
        d: DeepDict = {}
        for k, v in self.items():
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

    def update(self, **data) -> None:
        newself = self.model_validate(data, from_attributes=True)
        for k, v in newself.items():
            if k not in self:
                self.__setattr__(k, v)

    def __len__(self) -> int:
        return self.model_fields_set.__len__()

    def __iter__(self):
        return (i for i in self.model_dump().keys())

    def __getitem__(self, key: Any) -> Any:
        try:
            return self.__getattribute__(key)
        except AttributeError as e:
            try:
                return self.__getattr__(key)
            except AttributeError as f:
                raise KeyError(e, f)


    # def get(self, key: str, default=None) -> Any:
    #     try:
    #         return self.__getitem__(key)
    #     except (KeyError, AttributeError) as e:
    #         return default

    def __setitem__(self, key: str, value: Any) -> None:
        return self.__setattr__(key, value)

    def __delitem__(self, key: str) -> None:
        return self.__delattr__(key)


class ConfigurationError(Exception):
    def __init__(self, *args, location):
        self.location = location
        super().__init__(*args)

    def __str__(self):
        return f'Error parsing config:\n{self.location}\n  {super().__str__()}'

type DeepDict = dict[str, bool | str | DeepDict]


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

    # @computed_field
    @property
    def raw_data(self) -> DeepDict:
        if not self.args and (self.name == self.path):
            return self.name
        return super().raw_data


class LicenseConfig(BaseConfig, ):
    headers: bool = Field(default=True)
    default: list[str] = Field(default=['MIT'])

    _validate_headers = field_validator('headers', mode='before')(validate_bool)


class TemplateConfig(BaseConfig):
    name: str = Field(default='')
    email: str = Field(default='')
    licenses: LicenseConfig = Field(default_factory=LicenseConfig)
    plugins: dict[str, dict[str, bool | str]] = Field(
        default={'default': {'ci': False, 'src-layout': True, 'tests': True}})

    def _try_git(self, var: str, default: str = ''):
        attr = f'{var}'
        try:
            item = os.getenv(f'GIT_AUTHOR_{var}')
            setattr(self, attr, item)
        except (ValidationError, ValueError, TypeError, KeyError) as e:
            import subprocess
            try:
                setattr(
                    self, attr,
                    subprocess.check_output(
                        ['git', 'config', '--get', f'user.{var}']
                    ).strip().decode()
                )
            except:
                setattr(self, attr, default)

    def model_post_init(self, _) -> None:
        for k, v in [('name', 'U.N. Owen'), ('email', 'void@some.where')]:
            if not getattr(self, k):
                self._try_git(k, v)

class StylesConfig(BaseConfig):
    info: StyleType      = Field('bold')
    success: StyleType   = Field('bold cyan')
    error: StyleType     = Field('bold red')
    warning: StyleType   = Field('bold yellow')
    waiting: StyleType   = Field('bold magenta')
    debug: StyleType     = Field('bold')
    spinner: SpinnerType = Field('simpleDotsScrolling')


class TerminalConfig(BaseConfig):
    styles: StylesConfig = {}

    def model_post_init(self, _) -> None:
        if not self.styles:
            self.styles = StylesConfig()


class ProjectConfig(BaseConfig):
    location: str = Field(default='')

    @property
    def raw_data(self) -> str:
        return self.location


class PluginConfig(BaseConfig):
    pass


class RootConfig(BaseConfig):
    dirs: DirsConfig = Field(default_factory=DirsConfig)
    mode: Literal['local', 'aware', 'project'] = Field(default='local')
    project: str = Field(default='')
    projects: dict[str, ProjectConfig] = Field(default_factory=dict)
    publish: dict[str, dict[str, str]] = {'index': {'repo': 'main'}}
    shell: str | ShellConfig = Field(default='')
    template: TemplateConfig = Field(default_factory=TemplateConfig)
    terminal: TerminalConfig = Field(default_factory=TerminalConfig)

    _normalize_strings = field_validator('mode', 'project', mode='before')(validate_string_strict)

    @field_validator('projects', mode='before')
    @classmethod
    def _fixup_projects(cls, projs: dict[str, ProjectConfig | str]) -> dict[str, ProjectConfig]:
        if not isinstance(projs, dict):
            raise TypeError(f'Projects ({projs!r}) is not a dictionary.')
        if not projs:
            return {}
        r: dict[str, ProjectConfig] = dict()
        for k, v in projs.items():
            if not v:
                raise TypeError(f'Project {k} has no location ({v!r})')
            if isinstance(v, str):
                r[k] = ProjectConfig(location=v)
            else:
                r[k] = v
        return r

    def model_post_init(self, _) -> None:
        if not self.template:
            self.template = TemplateConfig()
        if not self.terminal:
            self.terminal = TerminalConfig()
        if not self.dirs:
            self.dirs = DirsConfig()

        if isinstance(self.shell, str):
            self.shell = ShellConfig(name=self.shell)
