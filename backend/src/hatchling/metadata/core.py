from __future__ import annotations

import os
import sys
from contextlib import suppress
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Generic, cast

from hatchling.metadata.utils import (
    format_dependency,
    is_valid_project_name,
    normalize_project_name,
    normalize_requirement,
)
from hatchling.plugin.manager import PluginManagerBound
from hatchling.utils.constants import DEFAULT_CONFIG_FILE
from hatchling.utils.fs import locate_file

if TYPE_CHECKING:
    from packaging.requirements import Requirement
    from packaging.specifiers import SpecifierSet

    from hatchling.metadata.plugin.interface import MetadataHookInterface
    from hatchling.utils.context import Context
    from hatchling.version.scheme.plugin.interface import VersionSchemeInterface
    from hatchling.version.source.plugin.interface import VersionSourceInterface

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def load_toml(path: str) -> dict[str, Any]:
    with open(path, encoding='utf-8') as f:
        return tomllib.loads(f.read())


class ProjectMetadata(Generic[PluginManagerBound]):
    def __init__(
        self,
        root: str,
        plugin_manager: PluginManagerBound | None,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.root = root
        self.plugin_manager = plugin_manager
        self._config = config

        self._context: Context | None = None
        self._build: BuildMetadata | None = None
        self._core: CoreMetadata | None = None
        self._hatch: HatchMetadata | None = None

        self._core_raw_metadata: dict[str, Any] | None = None
        self._dynamic: list[str] | None = None
        self._name: str | None = None
        self._version: str | None = None
        self._project_file: str | None = None

        # App already loaded config
        if config is not None and root is not None:
            self._project_file = os.path.join(root, 'pyproject.toml')

    def has_project_file(self) -> bool:
        _ = self.config
        if self._project_file is None:
            return False
        return os.path.isfile(self._project_file)

    @property
    def context(self) -> Context:
        if self._context is None:
            from hatchling.utils.context import Context

            self._context = Context(self.root)

        return self._context

    @property
    def core_raw_metadata(self) -> dict[str, Any]:
        if self._core_raw_metadata is None:
            if 'project' not in self.config:
                message = 'Missing `project` metadata table in configuration'
                raise ValueError(message)

            core_raw_metadata = self.config['project']
            if not isinstance(core_raw_metadata, dict):
                message = 'The `project` configuration must be a table'
                raise TypeError(message)

            core_raw_metadata = deepcopy(core_raw_metadata)
            pkg_info = os.path.join(self.root, 'PKG-INFO')
            if os.path.isfile(pkg_info):
                from hatchling.metadata.spec import PROJECT_CORE_METADATA_FIELDS, project_metadata_from_core_metadata

                with open(pkg_info, encoding='utf-8') as f:
                    pkg_info_contents = f.read()

                base_metadata = project_metadata_from_core_metadata(pkg_info_contents)
                defined_dynamic = core_raw_metadata.get('dynamic', [])
                for field in list(defined_dynamic):
                    if field in PROJECT_CORE_METADATA_FIELDS and field in base_metadata:
                        core_raw_metadata[field] = base_metadata[field]
                        defined_dynamic.remove(field)

            self._core_raw_metadata = core_raw_metadata

        return self._core_raw_metadata

    @property
    def dynamic(self) -> list[str]:
        # Keep track of the original dynamic fields before depopulation
        if self._dynamic is None:
            dynamic = self.core_raw_metadata.get('dynamic', [])
            if not isinstance(dynamic, list):
                message = 'Field `project.dynamic` must be an array'
                raise TypeError(message)

            for i, field in enumerate(dynamic, 1):
                if not isinstance(field, str):
                    message = f'Field #{i} of field `project.dynamic` must be a string'
                    raise TypeError(message)

            self._dynamic = list(dynamic)

        return self._dynamic

    @property
    def name(self) -> str:
        # Duplicate the name parsing here for situations where it's
        # needed but metadata plugins might not be available
        if self._name is None:
            name = self.core_raw_metadata.get('name', '')
            if not name:
                message = 'Missing required field `project.name`'
                raise ValueError(message)

            self._name = normalize_project_name(name)

        return self._name

    @property
    def version(self) -> str:
        """
        https://peps.python.org/pep-0621/#version
        """
        if self._version is None:
            self._version = self._get_version()
            with suppress(ValueError):
                self.core.dynamic.remove('version')

        return self._version

    @property
    def config(self) -> dict[str, Any]:
        if self._config is None:
            project_file = locate_file(self.root, 'pyproject.toml')
            if project_file is None:
                self._config = {}
            else:
                self._project_file = project_file
                self._config = load_toml(project_file)

        return self._config

    @property
    def build(self) -> BuildMetadata:
        if self._build is None:
            build_metadata = self.config.get('build-system', {})
            if not isinstance(build_metadata, dict):
                message = 'The `build-system` configuration must be a table'
                raise TypeError(message)

            self._build = BuildMetadata(self.root, build_metadata)

        return self._build

    @property
    def core(self) -> CoreMetadata:
        if self._core is None:
            metadata = CoreMetadata(self.root, self.core_raw_metadata, self.hatch.metadata, self.context)

            # Save the fields
            _ = self.dynamic

            metadata_hooks = self.hatch.metadata.hooks
            if metadata_hooks:
                static_fields = set(self.core_raw_metadata)
                if 'version' in self.hatch.config:
                    self._version = self._get_version(metadata)
                    self.core_raw_metadata['version'] = self.version

                if metadata.dynamic:
                    for metadata_hook in metadata_hooks.values():
                        metadata_hook.update(self.core_raw_metadata)
                        metadata.add_known_classifiers(metadata_hook.get_known_classifiers())

                    new_fields = set(self.core_raw_metadata) - static_fields
                    for new_field in new_fields:
                        if new_field in metadata.dynamic:
                            metadata.dynamic.remove(new_field)
                        else:
                            message = (
                                f'The field `{new_field}` was set dynamically and therefore must be '
                                f'listed in `project.dynamic`'
                            )
                            raise ValueError(message)

            self._core = metadata

        return self._core

    @property
    def hatch(self) -> HatchMetadata:
        if self._hatch is None:
            tool_config = self.config.get('tool', {})
            if not isinstance(tool_config, dict):
                message = 'The `tool` configuration must be a table'
                raise TypeError(message)

            hatch_config = tool_config.get('hatch', {})
            if not isinstance(hatch_config, dict):
                message = 'The `tool.hatch` configuration must be a table'
                raise TypeError(message)

            hatch_file = (
                os.path.join(os.path.dirname(self._project_file), DEFAULT_CONFIG_FILE)
                if self._project_file is not None
                else locate_file(self.root, DEFAULT_CONFIG_FILE) or ''
            )

            if hatch_file and os.path.isfile(hatch_file):
                config = load_toml(hatch_file)
                hatch_config = hatch_config.copy()
                hatch_config.update(config)

            self._hatch = HatchMetadata(self.root, hatch_config, self.plugin_manager)

        return self._hatch

    def _get_version(self, core_metadata: CoreMetadata | None = None) -> str:
        if core_metadata is None:
            core_metadata = self.core

        version = core_metadata.version
        if version is None:
            version = self.hatch.version.cached
            source = f'source `{self.hatch.version.source_name}`'
            core_metadata._version_set = True  # noqa: SLF001
        else:
            source = 'field `project.version`'

        from packaging.version import InvalidVersion, Version

        try:
            normalized_version = str(Version(version))
        except InvalidVersion:
            message = f'Invalid version `{version}` from {source}, see https://peps.python.org/pep-0440/'
            raise ValueError(message) from None
        else:
            return normalized_version

    def validate_fields(self) -> None:
        _ = self.version
        self.core.validate_fields()


class BuildMetadata:
    """
    https://peps.python.org/pep-0517/
    """

    def __init__(self, root: str, config: dict[str, str | list[str]]) -> None:
        self.root = root
        self.config = config

        self._requires: list[str] | None = None
        self._requires_complex: list[Requirement] | None = None
        self._build_backend: str | None = None
        self._backend_path: list[str] | None = None

    @property
    def requires_complex(self) -> list[Requirement]:
        if self._requires_complex is None:
            from packaging.requirements import InvalidRequirement, Requirement

            requires = self.config.get('requires', [])
            if not isinstance(requires, list):
                message = 'Field `build-system.requires` must be an array'
                raise TypeError(message)

            requires_complex = []

            for i, entry in enumerate(requires, 1):
                if not isinstance(entry, str):
                    message = f'Dependency #{i} of field `build-system.requires` must be a string'
                    raise TypeError(message)

                try:
                    requires_complex.append(Requirement(entry))
                except InvalidRequirement as e:
                    message = f'Dependency #{i} of field `build-system.requires` is invalid: {e}'
                    raise ValueError(message) from None

            self._requires_complex = requires_complex

        return self._requires_complex

    @property
    def requires(self) -> list[str]:
        if self._requires is None:
            self._requires = [str(r) for r in self.requires_complex]

        return self._requires

    @property
    def build_backend(self) -> str:
        if self._build_backend is None:
            build_backend = self.config.get('build-backend', '')
            if not isinstance(build_backend, str):
                message = 'Field `build-system.build-backend` must be a string'
                raise TypeError(message)

            self._build_backend = build_backend

        return self._build_backend

    @property
    def backend_path(self) -> list[str]:
        if self._backend_path is None:
            backend_path = self.config.get('backend-path', [])
            if not isinstance(backend_path, list):
                message = 'Field `build-system.backend-path` must be an array'
                raise TypeError(message)

            for i, entry in enumerate(backend_path, 1):
                if not isinstance(entry, str):
                    message = f'Entry #{i} of field `build-system.backend-path` must be a string'
                    raise TypeError(message)

            self._backend_path = backend_path

        return self._backend_path


class CoreMetadata:
    """
    https://peps.python.org/pep-0621/
    """

    def __init__(
        self,
        root: str,
        config: dict[str, Any],
        hatch_metadata: HatchMetadataSettings,
        context: Context,
    ) -> None:
        self.root = root
        self.config = config
        self.hatch_metadata = hatch_metadata
        self.context = context

        self._raw_name: str | None = None
        self._name: str | None = None
        self._version: str | None = None
        self._description: str | None = None
        self._readme: str | None = None
        self._readme_content_type: str | None = None
        self._readme_path: str | None = None
        self._requires_python: str | None = None
        self._python_constraint: SpecifierSet | None = None
        self._license: str | None = None
        self._license_expression: str | None = None
        self._license_files: list[str] | None = None
        self._authors: list[str] | None = None
        self._authors_data: dict[str, list[str]] | None = None
        self._maintainers: list[str] | None = None
        self._maintainers_data: dict[str, list[str]] | None = None
        self._keywords: list[str] | None = None
        self._classifiers: list[str] | None = None
        self._extra_classifiers: set[str] = set()
        self._urls: dict[str, str] | None = None
        self._scripts: dict[str, str] | None = None
        self._gui_scripts: dict[str, str] | None = None
        self._entry_points: dict[str, dict[str, str]] | None = None
        self._dependencies_complex: dict[str, Requirement] | None = None
        self._dependencies: list[str] | None = None
        self._optional_dependencies_complex: dict[str, dict[str, Requirement]] | None = None
        self._optional_dependencies: dict[str, list[str]] | None = None
        self._dynamic: list[str] | None = None

        # Indicates that the version has been successfully set dynamically
        self._version_set: bool = False

    @property
    def raw_name(self) -> str:
        """
        https://peps.python.org/pep-0621/#name
        """
        if self._raw_name is None:
            if 'name' in self.dynamic:
                message = 'Static metadata field `name` cannot be present in field `project.dynamic`'
                raise ValueError(message)

            raw_name = self.config.get('name', '')
            if not raw_name:
                message = 'Missing required field `project.name`'
                raise ValueError(message)

            if not isinstance(raw_name, str):
                message = 'Field `project.name` must be a string'
                raise TypeError(message)

            if not is_valid_project_name(raw_name):
                message = (
                    'Required field `project.name` must only contain ASCII letters/digits, underscores, '
                    'hyphens, and periods, and must begin and end with ASCII letters/digits.'
                )
                raise ValueError(message)

            self._raw_name = raw_name

        return self._raw_name

    @property
    def name(self) -> str:
        """
        https://peps.python.org/pep-0621/#name
        """
        if self._name is None:
            self._name = normalize_project_name(self.raw_name)

        return self._name

    @property
    def version(self) -> str:
        """
        https://peps.python.org/pep-0621/#version
        """
        version: str

        if self._version is None:
            if 'version' not in self.config:
                if not self._version_set and 'version' not in self.dynamic:
                    message = (
                        'Field `project.version` can only be resolved dynamically '
                        'if `version` is in field `project.dynamic`'
                    )
                    raise ValueError(message)
            else:
                if 'version' in self.dynamic:
                    message = (
                        'Metadata field `version` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )
                    raise ValueError(message)

                version = self.config['version']
                if not isinstance(version, str):
                    message = 'Field `project.version` must be a string'
                    raise TypeError(message)

                self._version = version

        return cast(str, self._version)

    @property
    def description(self) -> str:
        """
        https://peps.python.org/pep-0621/#description
        """
        if self._description is None:
            if 'description' in self.config:
                description = self.config['description']
                if 'description' in self.dynamic:
                    message = (
                        'Metadata field `description` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )
                    raise ValueError(message)
            else:
                description = ''

            if not isinstance(description, str):
                message = 'Field `project.description` must be a string'
                raise TypeError(message)
            self._description = ' '.join(description.splitlines())

        return self._description

    @property
    def readme(self) -> str:
        """
        https://peps.python.org/pep-0621/#readme
        """
        readme: str | dict[str, str] | None
        content_type: str | None

        if self._readme is None:
            if 'readme' in self.config:
                readme = self.config['readme']
                if 'readme' in self.dynamic:
                    message = (
                        'Metadata field `readme` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )
                    raise ValueError(message)
            else:
                readme = None

            if readme is None:
                self._readme = ''
                self._readme_content_type = 'text/markdown'
                self._readme_path = ''
            elif isinstance(readme, str):
                normalized_path = readme.lower()
                if normalized_path.endswith('.md'):
                    content_type = 'text/markdown'
                elif normalized_path.endswith('.rst'):
                    content_type = 'text/x-rst'
                elif normalized_path.endswith('.txt'):
                    content_type = 'text/plain'
                else:
                    message = f'Unable to determine the content-type based on the extension of readme file: {readme}'
                    raise TypeError(message)

                readme_path = os.path.normpath(os.path.join(self.root, readme))
                if not os.path.isfile(readme_path):
                    message = f'Readme file does not exist: {readme}'
                    raise OSError(message)

                with open(readme_path, encoding='utf-8') as f:
                    self._readme = f.read()

                self._readme_content_type = content_type
                self._readme_path = readme
            elif isinstance(readme, dict):
                content_type = readme.get('content-type')
                if content_type is None:
                    message = 'Field `content-type` is required in the `project.readme` table'
                    raise ValueError(message)

                if not isinstance(content_type, str):
                    message = 'Field `content-type` in the `project.readme` table must be a string'
                    raise TypeError(message)

                if content_type not in {'text/markdown', 'text/x-rst', 'text/plain'}:
                    message = (
                        'Field `content-type` in the `project.readme` table must be one of the following: '
                        'text/markdown, text/x-rst, text/plain'
                    )
                    raise ValueError(message)

                if 'file' in readme and 'text' in readme:
                    message = 'Cannot specify both `file` and `text` in the `project.readme` table'
                    raise ValueError(message)

                if 'file' in readme:
                    relative_path = readme['file']
                    if not isinstance(relative_path, str):
                        message = 'Field `file` in the `project.readme` table must be a string'
                        raise TypeError(message)

                    path = os.path.normpath(os.path.join(self.root, relative_path))
                    if not os.path.isfile(path):
                        message = f'Readme file does not exist: {relative_path}'
                        raise OSError(message)

                    with open(path, encoding=readme.get('charset', 'utf-8')) as f:
                        contents = f.read()

                    readme_path = relative_path
                elif 'text' in readme:
                    contents = readme['text']
                    if not isinstance(contents, str):
                        message = 'Field `text` in the `project.readme` table must be a string'
                        raise TypeError(message)

                    readme_path = ''
                else:
                    message = 'Must specify either `file` or `text` in the `project.readme` table'
                    raise ValueError(message)

                self._readme = contents
                self._readme_content_type = content_type
                self._readme_path = readme_path
            else:
                message = 'Field `project.readme` must be a string or a table'
                raise TypeError(message)

        return self._readme

    @property
    def readme_content_type(self) -> str:
        """
        https://peps.python.org/pep-0621/#readme
        """
        if self._readme_content_type is None:
            _ = self.readme

        return cast(str, self._readme_content_type)

    @property
    def readme_path(self) -> str:
        """
        https://peps.python.org/pep-0621/#readme
        """
        if self._readme_path is None:
            _ = self.readme

        return cast(str, self._readme_path)

    @property
    def requires_python(self) -> str:
        """
        https://peps.python.org/pep-0621/#requires-python
        """
        if self._requires_python is None:
            from packaging.specifiers import InvalidSpecifier, SpecifierSet

            if 'requires-python' in self.config:
                requires_python = self.config['requires-python']
                if 'requires-python' in self.dynamic:
                    message = (
                        'Metadata field `requires-python` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )
                    raise ValueError(message)
            else:
                requires_python = ''

            if not isinstance(requires_python, str):
                message = 'Field `project.requires-python` must be a string'
                raise TypeError(message)

            try:
                self._python_constraint = SpecifierSet(requires_python)
            except InvalidSpecifier as e:
                message = f'Field `project.requires-python` is invalid: {e}'
                raise ValueError(message) from None

            self._requires_python = str(self._python_constraint)

        return self._requires_python

    @property
    def python_constraint(self) -> SpecifierSet:
        from packaging.specifiers import SpecifierSet

        if self._python_constraint is None:
            _ = self.requires_python

        return cast(SpecifierSet, self._python_constraint)

    @property
    def license(self) -> str:
        """
        https://peps.python.org/pep-0621/#license
        """
        if self._license is None:
            if 'license' in self.config:
                data = self.config['license']
                if 'license' in self.dynamic:
                    message = (
                        'Metadata field `license` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )
                    raise ValueError(message)
            else:
                data = None

            if data is None:
                self._license = ''
                self._license_expression = ''
            elif isinstance(data, str):
                from packaging.licenses import canonicalize_license_expression

                try:
                    self._license_expression = str(canonicalize_license_expression(data))
                except ValueError as e:
                    message = f'Error parsing field `project.license` - {e}'
                    raise ValueError(message) from None

                self._license = ''
            elif isinstance(data, dict):
                if 'file' in data and 'text' in data:
                    message = 'Cannot specify both `file` and `text` in the `project.license` table'
                    raise ValueError(message)

                if 'file' in data:
                    relative_path = data['file']
                    if not isinstance(relative_path, str):
                        message = 'Field `file` in the `project.license` table must be a string'
                        raise TypeError(message)

                    path = os.path.normpath(os.path.join(self.root, relative_path))
                    if not os.path.isfile(path):
                        message = f'License file does not exist: {relative_path}'
                        raise OSError(message)

                    with open(path, encoding='utf-8') as f:
                        contents = f.read()
                elif 'text' in data:
                    contents = data['text']
                    if not isinstance(contents, str):
                        message = 'Field `text` in the `project.license` table must be a string'
                        raise TypeError(message)
                else:
                    message = 'Must specify either `file` or `text` in the `project.license` table'
                    raise ValueError(message)

                self._license = contents
                self._license_expression = ''
            else:
                message = 'Field `project.license` must be a string or a table'
                raise TypeError(message)

        return self._license

    @property
    def license_expression(self) -> str:
        """
        https://peps.python.org/pep-0639/
        """
        if self._license_expression is None:
            _ = self.license

        return cast(str, self._license_expression)

    @property
    def license_files(self) -> list[str]:
        """
        https://peps.python.org/pep-0639/
        """
        if self._license_files is None:
            if 'license-files' in self.config:
                globs = self.config['license-files']
                if 'license-files' in self.dynamic:
                    message = (
                        'Metadata field `license-files` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )
                    raise ValueError(message)

                if isinstance(globs, dict):
                    globs = globs.get('globs', globs.get('paths', []))
            else:
                globs = ['LICEN[CS]E*', 'COPYING*', 'NOTICE*', 'AUTHORS*']

            from glob import glob

            license_files: list[str] = []
            if not isinstance(globs, list):
                message = 'Field `project.license-files` must be an array'
                raise TypeError(message)

            for i, pattern in enumerate(globs, 1):
                if not isinstance(pattern, str):
                    message = f'Entry #{i} of field `project.license-files` must be a string'
                    raise TypeError(message)

                full_pattern = os.path.normpath(os.path.join(self.root, pattern))
                license_files.extend(
                    os.path.relpath(path, self.root).replace('\\', '/')
                    for path in glob(full_pattern)
                    if os.path.isfile(path)
                )

            self._license_files = sorted(license_files)

        return self._license_files

    @property
    def authors(self) -> list[str]:
        """
        https://peps.python.org/pep-0621/#authors-maintainers
        """
        authors: list[str]
        authors_data: dict[str, list[str]]

        if self._authors is None:
            if 'authors' in self.config:
                authors = self.config['authors']
                if 'authors' in self.dynamic:
                    message = (
                        'Metadata field `authors` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )
                    raise ValueError(message)
            else:
                authors = []

            if not isinstance(authors, list):
                message = 'Field `project.authors` must be an array'
                raise TypeError(message)

            from email.headerregistry import Address

            authors = deepcopy(authors)
            authors_data = {'name': [], 'email': []}

            for i, data in enumerate(authors, 1):
                if not isinstance(data, dict):
                    message = f'Author #{i} of field `project.authors` must be an inline table'
                    raise TypeError(message)

                name = data.get('name', '')
                if not isinstance(name, str):
                    message = f'Name of author #{i} of field `project.authors` must be a string'
                    raise TypeError(message)

                email = data.get('email', '')
                if not isinstance(email, str):
                    message = f'Email of author #{i} of field `project.authors` must be a string'
                    raise TypeError(message)

                if name and email:
                    authors_data['email'].append(str(Address(display_name=name, addr_spec=email)))
                elif email:
                    authors_data['email'].append(str(Address(addr_spec=email)))
                elif name:
                    authors_data['name'].append(name)
                else:
                    message = f'Author #{i} of field `project.authors` must specify either `name` or `email`'
                    raise ValueError(message)

            self._authors = authors
            self._authors_data = authors_data

        return self._authors

    @property
    def authors_data(self) -> dict[str, list[str]]:
        """
        https://peps.python.org/pep-0621/#authors-maintainers
        """
        if self._authors_data is None:
            _ = self.authors

        return cast(dict, self._authors_data)

    @property
    def maintainers(self) -> list[str]:
        """
        https://peps.python.org/pep-0621/#authors-maintainers
        """
        maintainers: list[str]

        if self._maintainers is None:
            if 'maintainers' in self.config:
                maintainers = self.config['maintainers']
                if 'maintainers' in self.dynamic:
                    message = (
                        'Metadata field `maintainers` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )
                    raise ValueError(message)
            else:
                maintainers = []

            if not isinstance(maintainers, list):
                message = 'Field `project.maintainers` must be an array'
                raise TypeError(message)

            from email.headerregistry import Address

            maintainers = deepcopy(maintainers)
            maintainers_data: dict[str, list[str]] = {'name': [], 'email': []}

            for i, data in enumerate(maintainers, 1):
                if not isinstance(data, dict):
                    message = f'Maintainer #{i} of field `project.maintainers` must be an inline table'
                    raise TypeError(message)

                name = data.get('name', '')
                if not isinstance(name, str):
                    message = f'Name of maintainer #{i} of field `project.maintainers` must be a string'
                    raise TypeError(message)

                email = data.get('email', '')
                if not isinstance(email, str):
                    message = f'Email of maintainer #{i} of field `project.maintainers` must be a string'
                    raise TypeError(message)

                if name and email:
                    maintainers_data['email'].append(str(Address(display_name=name, addr_spec=email)))
                elif email:
                    maintainers_data['email'].append(str(Address(addr_spec=email)))
                elif name:
                    maintainers_data['name'].append(name)
                else:
                    message = f'Maintainer #{i} of field `project.maintainers` must specify either `name` or `email`'
                    raise ValueError(message)

            self._maintainers = maintainers
            self._maintainers_data = maintainers_data

        return self._maintainers

    @property
    def maintainers_data(self) -> dict[str, list[str]]:
        """
        https://peps.python.org/pep-0621/#authors-maintainers
        """
        if self._maintainers_data is None:
            _ = self.maintainers

        return cast(dict, self._maintainers_data)

    @property
    def keywords(self) -> list[str]:
        """
        https://peps.python.org/pep-0621/#keywords
        """
        if self._keywords is None:
            if 'keywords' in self.config:
                keywords = self.config['keywords']
                if 'keywords' in self.dynamic:
                    message = (
                        'Metadata field `keywords` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )
                    raise ValueError(message)
            else:
                keywords = []

            if not isinstance(keywords, list):
                message = 'Field `project.keywords` must be an array'
                raise TypeError(message)

            unique_keywords = set()

            for i, keyword in enumerate(keywords, 1):
                if not isinstance(keyword, str):
                    message = f'Keyword #{i} of field `project.keywords` must be a string'
                    raise TypeError(message)

                unique_keywords.add(keyword)

            self._keywords = sorted(unique_keywords)

        return self._keywords

    @property
    def classifiers(self) -> list[str]:
        """
        https://peps.python.org/pep-0621/#classifiers
        """
        if self._classifiers is None:
            import bisect

            if 'classifiers' in self.config:
                classifiers = self.config['classifiers']
                if 'classifiers' in self.dynamic:
                    message = (
                        'Metadata field `classifiers` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )
                    raise ValueError(message)
            else:
                classifiers = []

            if not isinstance(classifiers, list):
                message = 'Field `project.classifiers` must be an array'
                raise TypeError(message)

            verify_classifiers = not os.environ.get('HATCH_METADATA_CLASSIFIERS_NO_VERIFY')
            if verify_classifiers:
                import trove_classifiers

                known_classifiers = trove_classifiers.classifiers | self._extra_classifiers
                sorted_classifiers = list(trove_classifiers.sorted_classifiers)

                for classifier in sorted(self._extra_classifiers - trove_classifiers.classifiers):
                    bisect.insort(sorted_classifiers, classifier)

            unique_classifiers = set()

            for i, classifier in enumerate(classifiers, 1):
                if not isinstance(classifier, str):
                    message = f'Classifier #{i} of field `project.classifiers` must be a string'
                    raise TypeError(message)

                if (
                    not self.__classifier_is_private(classifier)
                    and verify_classifiers
                    and classifier not in known_classifiers
                ):
                    message = f'Unknown classifier in field `project.classifiers`: {classifier}'
                    raise ValueError(message)

                unique_classifiers.add(classifier)

            if not verify_classifiers:
                import re

                # combined text-numeric sort that ensures that Python versions sort correctly
                split_re = re.compile(r'(\D*)(\d*)')
                sorted_classifiers = sorted(
                    classifiers,
                    key=lambda value: ([(a, int(b) if b else None) for a, b in split_re.findall(value)]),
                )

            self._classifiers = sorted(
                unique_classifiers, key=lambda c: -1 if self.__classifier_is_private(c) else sorted_classifiers.index(c)
            )

        return self._classifiers

    @property
    def urls(self) -> dict[str, str]:
        """
        https://peps.python.org/pep-0621/#urls
        """
        if self._urls is None:
            if 'urls' in self.config:
                urls = self.config['urls']
                if 'urls' in self.dynamic:
                    message = (
                        'Metadata field `urls` cannot be both statically defined and listed in field `project.dynamic`'
                    )
                    raise ValueError(message)
            else:
                urls = {}

            if not isinstance(urls, dict):
                message = 'Field `project.urls` must be a table'
                raise TypeError(message)

            sorted_urls = {}

            for label, url in urls.items():
                if not isinstance(url, str):
                    message = f'URL `{label}` of field `project.urls` must be a string'
                    raise TypeError(message)

                sorted_urls[label] = url

            self._urls = sorted_urls

        return self._urls

    @property
    def scripts(self) -> dict[str, str]:
        """
        https://peps.python.org/pep-0621/#entry-points
        """
        if self._scripts is None:
            if 'scripts' in self.config:
                scripts = self.config['scripts']
                if 'scripts' in self.dynamic:
                    message = (
                        'Metadata field `scripts` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )
                    raise ValueError(message)
            else:
                scripts = {}

            if not isinstance(scripts, dict):
                message = 'Field `project.scripts` must be a table'
                raise TypeError(message)

            sorted_scripts = {}

            for name, object_ref in sorted(scripts.items()):
                if not isinstance(object_ref, str):
                    message = f'Object reference `{name}` of field `project.scripts` must be a string'
                    raise TypeError(message)

                sorted_scripts[name] = object_ref

            self._scripts = sorted_scripts

        return self._scripts

    @property
    def gui_scripts(self) -> dict[str, str]:
        """
        https://peps.python.org/pep-0621/#entry-points
        """
        if self._gui_scripts is None:
            if 'gui-scripts' in self.config:
                gui_scripts = self.config['gui-scripts']
                if 'gui-scripts' in self.dynamic:
                    message = (
                        'Metadata field `gui-scripts` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )
                    raise ValueError(message)
            else:
                gui_scripts = {}

            if not isinstance(gui_scripts, dict):
                message = 'Field `project.gui-scripts` must be a table'
                raise TypeError(message)

            sorted_gui_scripts = {}

            for name, object_ref in sorted(gui_scripts.items()):
                if not isinstance(object_ref, str):
                    message = f'Object reference `{name}` of field `project.gui-scripts` must be a string'
                    raise TypeError(message)

                sorted_gui_scripts[name] = object_ref

            self._gui_scripts = sorted_gui_scripts

        return self._gui_scripts

    @property
    def entry_points(self) -> dict[str, dict[str, str]]:
        """
        https://peps.python.org/pep-0621/#entry-points
        """
        if self._entry_points is None:
            if 'entry-points' in self.config:
                defined_entry_point_groups = self.config['entry-points']
                if 'entry-points' in self.dynamic:
                    message = (
                        'Metadata field `entry-points` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )
                    raise ValueError(message)
            else:
                defined_entry_point_groups = {}

            if not isinstance(defined_entry_point_groups, dict):
                message = 'Field `project.entry-points` must be a table'
                raise TypeError(message)

            for forbidden_field, expected_field in (('console_scripts', 'scripts'), ('gui-scripts', 'gui-scripts')):
                if forbidden_field in defined_entry_point_groups:
                    message = (
                        f'Field `{forbidden_field}` must be defined as `project.{expected_field}` '
                        f'instead of in the `project.entry-points` table'
                    )
                    raise ValueError(message)

            entry_point_groups = {}

            for group, entry_point_data in sorted(defined_entry_point_groups.items()):
                if not isinstance(entry_point_data, dict):
                    message = f'Field `project.entry-points.{group}` must be a table'
                    raise TypeError(message)

                entry_points = {}

                for name, object_ref in sorted(entry_point_data.items()):
                    if not isinstance(object_ref, str):
                        message = f'Object reference `{name}` of field `project.entry-points.{group}` must be a string'
                        raise TypeError(message)

                    entry_points[name] = object_ref

                if entry_points:
                    entry_point_groups[group] = entry_points

            self._entry_points = entry_point_groups

        return self._entry_points

    @property
    def dependencies_complex(self) -> dict[str, Requirement]:
        """
        https://peps.python.org/pep-0621/#dependencies-optional-dependencies
        """
        if self._dependencies_complex is None:
            from packaging.requirements import InvalidRequirement, Requirement

            if 'dependencies' in self.config:
                dependencies = self.config['dependencies']
                if 'dependencies' in self.dynamic:
                    message = (
                        'Metadata field `dependencies` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )
                    raise ValueError(message)
            else:
                dependencies = []

            if not isinstance(dependencies, list):
                message = 'Field `project.dependencies` must be an array'
                raise TypeError(message)

            dependencies_complex = {}

            for i, entry in enumerate(dependencies, 1):
                if not isinstance(entry, str):
                    message = f'Dependency #{i} of field `project.dependencies` must be a string'
                    raise TypeError(message)

                try:
                    requirement = Requirement(self.context.format(entry))
                except InvalidRequirement as e:
                    message = f'Dependency #{i} of field `project.dependencies` is invalid: {e}'
                    raise ValueError(message) from None
                else:
                    if requirement.url and not self.hatch_metadata.allow_direct_references:
                        message = (
                            f'Dependency #{i} of field `project.dependencies` cannot be a direct reference unless '
                            f'field `tool.hatch.metadata.allow-direct-references` is set to `true`'
                        )
                        raise ValueError(message)

                    normalize_requirement(requirement)
                    dependencies_complex[format_dependency(requirement)] = requirement

            self._dependencies_complex = dict(sorted(dependencies_complex.items()))

        return self._dependencies_complex

    @property
    def dependencies(self) -> list[str]:
        """
        https://peps.python.org/pep-0621/#dependencies-optional-dependencies
        """
        if self._dependencies is None:
            self._dependencies = list(self.dependencies_complex)

        return self._dependencies

    @property
    def optional_dependencies_complex(self) -> dict[str, dict[str, Requirement]]:
        """
        https://peps.python.org/pep-0621/#dependencies-optional-dependencies
        """
        if self._optional_dependencies_complex is None:
            from packaging.requirements import InvalidRequirement, Requirement

            if 'optional-dependencies' in self.config:
                optional_dependencies = self.config['optional-dependencies']
                if 'optional-dependencies' in self.dynamic:
                    message = (
                        'Metadata field `optional-dependencies` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )
                    raise ValueError(message)
            else:
                optional_dependencies = {}

            if not isinstance(optional_dependencies, dict):
                message = 'Field `project.optional-dependencies` must be a table'
                raise TypeError(message)

            normalized_options: dict[str, str] = {}
            optional_dependency_entries = {}
            inherited_options: dict[str, set[str]] = {}

            for option, dependencies in optional_dependencies.items():
                if not is_valid_project_name(option):
                    message = (
                        f'Optional dependency group `{option}` of field `project.optional-dependencies` must only '
                        f'contain ASCII letters/digits, underscores, hyphens, and periods, and must begin and end with '
                        f'ASCII letters/digits.'
                    )
                    raise ValueError(message)

                normalized_option = (
                    option if self.hatch_metadata.allow_ambiguous_features else normalize_project_name(option)
                )
                if normalized_option in normalized_options:
                    message = (
                        f'Optional dependency groups `{normalized_options[normalized_option]}` and `{option}` of '
                        f'field `project.optional-dependencies` both evaluate to `{normalized_option}`.'
                    )
                    raise ValueError(message)

                if not isinstance(dependencies, list):
                    message = (
                        f'Dependencies for option `{option}` of field `project.optional-dependencies` must be an array'
                    )
                    raise TypeError(message)

                entries = {}

                for i, entry in enumerate(dependencies, 1):
                    if not isinstance(entry, str):
                        message = (
                            f'Dependency #{i} of option `{option}` of field `project.optional-dependencies` '
                            f'must be a string'
                        )
                        raise TypeError(message)

                    try:
                        requirement = Requirement(self.context.format(entry))
                    except InvalidRequirement as e:
                        message = (
                            f'Dependency #{i} of option `{option}` of field `project.optional-dependencies` '
                            f'is invalid: {e}'
                        )
                        raise ValueError(message) from None
                    else:
                        if requirement.url and not self.hatch_metadata.allow_direct_references:
                            message = (
                                f'Dependency #{i} of option `{option}` of field `project.optional-dependencies` '
                                f'cannot be a direct reference unless field '
                                f'`tool.hatch.metadata.allow-direct-references` is set to `true`'
                            )
                            raise ValueError(message)

                        normalize_requirement(requirement)
                        if requirement.name == self.name:
                            if normalized_option in inherited_options:
                                inherited_options[normalized_option].update(requirement.extras)
                            else:
                                inherited_options[normalized_option] = set(requirement.extras)
                        else:
                            entries[format_dependency(requirement)] = requirement

                normalized_options[normalized_option] = option
                optional_dependency_entries[normalized_option] = entries

            visited: set[str] = set()
            resolved: set[str] = set()
            for dependent_option in inherited_options:
                _resolve_optional_dependencies(
                    optional_dependency_entries, dependent_option, inherited_options, visited, resolved
                )

            self._optional_dependencies_complex = {
                option: dict(sorted(entries.items())) for option, entries in sorted(optional_dependency_entries.items())
            }

        return self._optional_dependencies_complex

    @property
    def optional_dependencies(self) -> dict[str, list[str]]:
        """
        https://peps.python.org/pep-0621/#dependencies-optional-dependencies
        """
        if self._optional_dependencies is None:
            self._optional_dependencies = {
                option: list(entries) for option, entries in self.optional_dependencies_complex.items()
            }

        return self._optional_dependencies

    @property
    def dynamic(self) -> list[str]:
        """
        https://peps.python.org/pep-0621/#dynamic
        """
        if self._dynamic is None:
            dynamic = self.config.get('dynamic', [])

            if not isinstance(dynamic, list):
                message = 'Field `project.dynamic` must be an array'
                raise TypeError(message)

            if not all(isinstance(entry, str) for entry in dynamic):
                message = 'Field `project.dynamic` must only contain strings'
                raise TypeError(message)

            self._dynamic = sorted(dynamic)

        return self._dynamic

    def add_known_classifiers(self, classifiers: list[str]) -> None:
        self._extra_classifiers.update(classifiers)

    def validate_fields(self) -> None:
        # Trigger validation for everything
        for attribute in dir(self):
            getattr(self, attribute)

    @staticmethod
    def __classifier_is_private(classifier: str) -> bool:
        return classifier.lower().startswith('private ::')


class HatchMetadata(Generic[PluginManagerBound]):
    def __init__(self, root: str, config: dict[str, dict[str, Any]], plugin_manager: PluginManagerBound) -> None:
        self.root = root
        self.config = config
        self.plugin_manager = plugin_manager

        self._metadata: HatchMetadataSettings | None = None
        self._build_config: dict[str, Any] | None = None
        self._build_targets: dict[str, Any] | None = None
        self._version: HatchVersionConfig | None = None

    @property
    def metadata(self) -> HatchMetadataSettings:
        if self._metadata is None:
            metadata_config = self.config.get('metadata', {})
            if not isinstance(metadata_config, dict):
                message = 'Field `tool.hatch.metadata` must be a table'
                raise TypeError(message)

            self._metadata = HatchMetadataSettings(self.root, metadata_config, self.plugin_manager)

        return self._metadata

    @property
    def build_config(self) -> dict[str, Any]:
        if self._build_config is None:
            build_config = self.config.get('build', {})
            if not isinstance(build_config, dict):
                message = 'Field `tool.hatch.build` must be a table'
                raise TypeError(message)

            self._build_config = build_config

        return self._build_config

    @property
    def build_targets(self) -> dict[str, Any]:
        if self._build_targets is None:
            build_targets: dict = self.build_config.get('targets', {})
            if not isinstance(build_targets, dict):
                message = 'Field `tool.hatch.build.targets` must be a table'
                raise TypeError(message)

            self._build_targets = build_targets

        return self._build_targets

    @property
    def version(self) -> HatchVersionConfig:
        if self._version is None:
            if 'version' not in self.config:
                message = 'Missing `tool.hatch.version` configuration'
                raise ValueError(message)

            options = self.config['version']
            if not isinstance(options, dict):
                message = 'Field `tool.hatch.version` must be a table'
                raise TypeError(message)

            self._version = HatchVersionConfig(self.root, deepcopy(options), self.plugin_manager)

        return self._version


class HatchVersionConfig(Generic[PluginManagerBound]):
    def __init__(self, root: str, config: dict[str, Any], plugin_manager: PluginManagerBound) -> None:
        self.root = root
        self.config = config
        self.plugin_manager = plugin_manager

        self._cached: str | None = None
        self._source_name: str | None = None
        self._scheme_name: str | None = None
        self._source: VersionSourceInterface | None = None
        self._scheme: VersionSchemeInterface | None = None

    @property
    def cached(self) -> str:
        if self._cached is None:
            try:
                self._cached = self.source.get_version_data()['version']
            except Exception as e:  # noqa: BLE001
                message = f'Error getting the version from source `{self.source.PLUGIN_NAME}`: {e}'
                raise type(e)(message) from None

        return self._cached

    @property
    def source_name(self) -> str:
        if self._source_name is None:
            source: str = self.config.get('source', 'regex')
            if not source:
                message = 'The `source` option under the `tool.hatch.version` table must not be empty if defined'
                raise ValueError(message)

            if not isinstance(source, str):
                message = 'Field `tool.hatch.version.source` must be a string'
                raise TypeError(message)

            self._source_name = source

        return self._source_name

    @property
    def scheme_name(self) -> str:
        if self._scheme_name is None:
            scheme: str = self.config.get('scheme', 'standard')
            if not scheme:
                message = 'The `scheme` option under the `tool.hatch.version` table must not be empty if defined'
                raise ValueError(message)

            if not isinstance(scheme, str):
                message = 'Field `tool.hatch.version.scheme` must be a string'
                raise TypeError(message)

            self._scheme_name = scheme

        return self._scheme_name

    @property
    def source(self) -> VersionSourceInterface:
        if self._source is None:
            from copy import deepcopy

            source_name = self.source_name
            version_source = self.plugin_manager.version_source.get(source_name)
            if version_source is None:
                from hatchling.plugin.exceptions import UnknownPluginError

                message = f'Unknown version source: {source_name}'
                raise UnknownPluginError(message)

            self._source = version_source(self.root, deepcopy(self.config))

        return self._source

    @property
    def scheme(self) -> VersionSchemeInterface:
        if self._scheme is None:
            from copy import deepcopy

            scheme_name = self.scheme_name
            version_scheme = self.plugin_manager.version_scheme.get(scheme_name)
            if version_scheme is None:
                from hatchling.plugin.exceptions import UnknownPluginError

                message = f'Unknown version scheme: {scheme_name}'
                raise UnknownPluginError(message)

            self._scheme = version_scheme(self.root, deepcopy(self.config))

        return self._scheme


class HatchMetadataSettings(Generic[PluginManagerBound]):
    def __init__(self, root: str, config: dict[str, Any], plugin_manager: PluginManagerBound) -> None:
        self.root = root
        self.config = config
        self.plugin_manager = plugin_manager

        self._allow_direct_references: bool | None = None
        self._allow_ambiguous_features: bool | None = None
        self._hook_config: dict[str, Any] | None = None
        self._hooks: dict[str, MetadataHookInterface] | None = None

    @property
    def allow_direct_references(self) -> bool:
        if self._allow_direct_references is None:
            allow_direct_references: bool = self.config.get('allow-direct-references', False)
            if not isinstance(allow_direct_references, bool):
                message = 'Field `tool.hatch.metadata.allow-direct-references` must be a boolean'
                raise TypeError(message)

            self._allow_direct_references = allow_direct_references

        return self._allow_direct_references

    @property
    def allow_ambiguous_features(self) -> bool:
        # TODO: remove in the first minor release after Jan 1, 2024
        if self._allow_ambiguous_features is None:
            allow_ambiguous_features: bool = self.config.get('allow-ambiguous-features', False)
            if not isinstance(allow_ambiguous_features, bool):
                message = 'Field `tool.hatch.metadata.allow-ambiguous-features` must be a boolean'
                raise TypeError(message)

            self._allow_ambiguous_features = allow_ambiguous_features

        return self._allow_ambiguous_features

    @property
    def hook_config(self) -> dict[str, Any]:
        if self._hook_config is None:
            hook_config: dict[str, Any] = self.config.get('hooks', {})
            if not isinstance(hook_config, dict):
                message = 'Field `tool.hatch.metadata.hooks` must be a table'
                raise TypeError(message)

            self._hook_config = hook_config

        return self._hook_config

    @property
    def hooks(self) -> dict[str, MetadataHookInterface]:
        if self._hooks is None:
            hook_config = self.hook_config

            configured_hooks = {}
            for hook_name, config in hook_config.items():
                metadata_hook = self.plugin_manager.metadata_hook.get(hook_name)
                if metadata_hook is None:
                    from hatchling.plugin.exceptions import UnknownPluginError

                    message = f'Unknown metadata hook: {hook_name}'
                    raise UnknownPluginError(message)

                configured_hooks[hook_name] = metadata_hook(self.root, config)

            self._hooks = configured_hooks

        return self._hooks


def _resolve_optional_dependencies(
    optional_dependencies_complex, dependent_option, inherited_options, visited, resolved
):
    if dependent_option in resolved:
        return

    if dependent_option in visited:
        message = f'Field `project.optional-dependencies` defines a circular dependency group: {dependent_option}'
        raise ValueError(message)

    visited.add(dependent_option)
    if dependent_option in inherited_options:
        for selected_option in inherited_options[dependent_option]:
            _resolve_optional_dependencies(
                optional_dependencies_complex, selected_option, inherited_options, visited, resolved
            )
            if selected_option not in optional_dependencies_complex:
                message = (
                    f'Unknown recursive dependency group in field `project.optional-dependencies`: {selected_option}'
                )
                raise ValueError(message)

            optional_dependencies_complex[dependent_option].update(optional_dependencies_complex[selected_option])

    resolved.add(dependent_option)
    visited.remove(dependent_option)
