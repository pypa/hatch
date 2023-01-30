"""
Generate json schema for hatch
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, constr

CustomProperty = constr(regex=r'^.*$')


def to_short_term(string: str) -> str:
    return '-'.join(word for word in string.split('_'))


class Metadata(BaseModel):
    allow_direct_references: bool | None = Field(description='Whether to allow direct references.')
    allow_ambiguous_features: bool | None = Field(description='Whether to allow ambiguous features.')

    class Config:
        alias_generator = to_short_term


class Env(BaseModel):
    scripts: dict[str, Any] | None = Field(description='Dictionary of scripts to run.')
    overrides: dict[str, Any] | None = Field(description='Overrides for the environment.')
    env_vars: dict[str, Any] | None = Field(description='Environment variables to set.')
    matrix: dict[str, list[str]] | None = Field(description='Matrix of environments.')

    dependencies: list[str] | None = Field(description='List of dependencies to install in the environment.')
    extra_dependencies: list[str] | None = Field(
        description='List of extra dependencies to install in the environment.'
    )
    dev_mode: bool | None = Field(description='Whether to install the project in development mode.')
    env_exclude: list[str] | None = Field(description='List of environment variables to exclude.')
    env_include: list[str] | None = Field(description='List of environment variables to include.')
    features: list[str] | None = Field(description='List of features to install.')
    matrix_name_format: str | None = Field(description='Format string for matrix names.')
    platforms: list[str] | None = Field(description='List of platforms to build for.')
    post_install_commands: list[str] | None = Field(description='List of commands to run after installing the project.')
    pre_install_commands: list[str] | None = Field(description='List of commands to run before installing the project.')
    python: str | None = Field(description='Python version to use.')
    skip_install: bool | None = Field(description='Whether to skip installing the project.')
    type_: str | None = Field(alias='type', description='Type of environment.')
    detached: bool | None = Field(description='Make the environment self-referential.')
    template: str | None = Field(description='Template to use for the environment.')
    description: str | None = Field(description='Description of the environment.')

    class Config:
        alias_generator = to_short_term


class Envs(BaseModel):
    __root__: dict[CustomProperty, Env]


class Target(BaseModel):
    dependencies: list[str] | None = Field(description='List of dependencies to install in the environment.')
    require_runtime_dependencies: bool | None = Field(description='Whether to require runtime dependencies.')
    require_runtime_features: list[str] | None = Field(description='Whether to require runtime features.')
    versions: list[str] | None = Field(description='List of versions to build for.')

    class Config:
        alias_generator = to_short_term


class WheelTarget(BaseModel):
    packages: list[str] | None = Field(description='List of packages to build.')
    sources: list[str] | None = Field(description='List of sources to build.')
    only_include: list[str] | None = Field(description='List of files to include.')


class SdistTarget(BaseModel):
    exclude: list[str] | None = Field(description='List of files to exclude.')


class Targets(BaseModel):
    wheel: WheelTarget | None = Field(description='Wheel target.')


class CustomTargets(BaseModel):
    __root__: dict[CustomProperty, Target]


class Hook(BaseModel):
    dependencies: list[str] | None = Field(description='Dependencies installed for the hook environment.')
    require_runtime_dependencies: bool | None = Field(description='Whether to require runtime dependencies.')
    require_runtime_features: list[str] | None = Field(description='Whether to require runtime features.')
    enable_by_default: bool | None = Field(description='Whether to enable current hook.')

    class Config:
        alias_generator = to_short_term


class Hooks(BaseModel):
    __root__: dict[CustomProperty, Hook]


class Build(BaseModel):
    ignore_vcs: bool | None = Field(title='Ignore Vcs', description='Whether to ignore VCS files.')
    include: list[str] | None = Field(description='List of files to include.')
    exclude: list[str] | None = Field(description='List of files to exclude.')
    artifacts: list[str] | None = Field(description='List of artifacts to include.')
    only_packages: bool | None = Field(description='Whether to only include packages.')
    skip_excluded_dirs: bool | None = Field(description='Whether to skip excluded directories.')
    reproducible: bool | None = Field(description='Whether to make the build reproducible.')
    directory: str | None = Field(description='Directory to build in.')
    dev_mode_dirs: list[str] | None = Field(description='List of directories to install in development mode.')
    dev_mode_exact: bool | None = Field(description='Whether to install in development mode exactly.')
    targets: CustomTargets | CustomTargets | None = Field(description='Build targets.')
    sources: dict[str, str] | list[str] | None = Field(description='Dictionary of sources.')
    hooks: Hooks | None = Field(description='Build hooks.')

    class Config:
        alias_generator = to_short_term


class Version(BaseModel):
    path: str | None = Field(description='A relative path to a file containing the project version')
    pattern: str | None = Field(description='A regex pattern to extract the version')


class PublishIndex(BaseModel):
    disable: bool | None = Field(description='Disable publishing to index.')


class Publish(BaseModel):
    index: PublishIndex | None = Field(description='Publish index.')


class Hatch(BaseModel):
    metadata: Metadata | None = Field(description='Metadata for the project.')
    envs: Envs | None = Field(description='Dictionary of environments.')
    build: Build | None = Field(description='Build configuration.')
    version: Version | None = Field(description='Version configuration.')
    publish: Publish | None = Field(description='Publish configuration.')


def main():
    with open('hatch.schema.json', 'w') as fs:
        fs.write(Hatch.schema_json(indent=2))


if __name__ == '__main__':
    main()
