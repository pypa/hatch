import os
import sys
from copy import deepcopy

from hatchling.metadata.utils import get_normalized_dependency, is_valid_project_name, normalize_project_name
from hatchling.utils.constants import DEFAULT_CONFIG_FILE
from hatchling.utils.fs import locate_file

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def load_toml(path):
    with open(path, encoding='utf-8') as f:
        return tomllib.loads(f.read())


class ProjectMetadata:
    def __init__(self, root, plugin_manager, config=None):
        self.root = root
        self.plugin_manager = plugin_manager
        self._config = config
        self._context = None
        self._build = None
        self._core = None
        self._hatch = None

        self._core_raw_metadata = None
        self._dynamic = None
        self._name = None
        self._version = None
        self._project_file = None

        # App already loaded config
        if config is not None and root is not None:
            self._project_file = os.path.join(root, 'pyproject.toml')

    def has_project_file(self):
        _ = self.config
        return os.path.isfile(self._project_file)

    @property
    def context(self):
        if self._context is None:
            from hatchling.utils.context import Context

            self._context = Context(self.root)

        return self._context

    @property
    def core_raw_metadata(self):
        if self._core_raw_metadata is None:
            if 'project' not in self.config:
                raise ValueError('Missing `project` metadata table in configuration')

            core_raw_metadata = self.config['project']
            if not isinstance(core_raw_metadata, dict):
                raise TypeError('The `project` configuration must be a table')

            self._core_raw_metadata = core_raw_metadata

        return self._core_raw_metadata

    @property
    def dynamic(self):
        # Keep track of the original dynamic fields before depopulation
        if self._dynamic is None:
            dynamic = self.core_raw_metadata.get('dynamic', [])
            if not isinstance(dynamic, list):
                raise TypeError('Field `project.dynamic` must be an array')

            for i, field in enumerate(dynamic, 1):
                if not isinstance(field, str):
                    raise TypeError(f'Field #{i} of field `project.dynamic` must be a string')

            self._dynamic = list(dynamic)

        return self._dynamic

    @property
    def name(self):
        # Duplicate the name parsing here for situations where it's
        # needed but metadata plugins might not be available
        if self._name is None:
            name = self.core_raw_metadata.get('name', '')
            if not name:
                raise ValueError('Missing required field `project.name`')

            self._name = normalize_project_name(name)

        return self._name

    @property
    def version(self):
        """
        https://peps.python.org/pep-0621/#version
        """
        if self._version is None:
            self._set_version()
            if 'version' in self.dynamic and 'version' in self.core_raw_metadata['dynamic']:
                self.core_raw_metadata['dynamic'].remove('version')

        return self._version

    @property
    def config(self):
        if self._config is None:
            project_file = locate_file(self.root, 'pyproject.toml')
            if project_file is None:
                self._config = {}
            else:
                self._project_file = project_file
                self._config = load_toml(project_file)

        return self._config

    @property
    def build(self):
        if self._build is None:
            build_metadata = self.config.get('build-system', {})
            if not isinstance(build_metadata, dict):
                raise TypeError('The `build-system` configuration must be a table')

            self._build = BuildMetadata(self.root, build_metadata)

        return self._build

    @property
    def core(self):
        if self._core is None:
            metadata = CoreMetadata(self.root, self.core_raw_metadata, self.hatch.metadata, self.context)

            # Save the fields
            _ = self.dynamic

            metadata_hooks = self.hatch.metadata.hooks
            if metadata_hooks:
                static_fields = set(self.core_raw_metadata)
                if 'version' in self.hatch.config:
                    self._set_version(metadata)
                    self.core_raw_metadata['version'] = self.version

                for metadata_hook in metadata_hooks.values():
                    metadata_hook.update(self.core_raw_metadata)
                    metadata.add_known_classifiers(metadata_hook.get_known_classifiers())

                new_fields = set(self.core_raw_metadata) - static_fields
                for new_field in new_fields:
                    if new_field in metadata.dynamic:
                        metadata.dynamic.remove(new_field)
                    else:
                        raise ValueError(
                            f'The field `{new_field}` was set dynamically and therefore must be '
                            f'listed in `project.dynamic`'
                        )

            self._core = metadata

        return self._core

    @property
    def hatch(self):
        if self._hatch is None:
            tool_config = self.config.get('tool', {})
            if not isinstance(tool_config, dict):
                raise TypeError('The `tool` configuration must be a table')

            hatch_config = tool_config.get('hatch', {})
            if not isinstance(hatch_config, dict):
                raise TypeError('The `tool.hatch` configuration must be a table')

            if self._project_file is not None:
                hatch_file = os.path.join(os.path.dirname(self._project_file), DEFAULT_CONFIG_FILE)
            else:
                hatch_file = locate_file(self.root, DEFAULT_CONFIG_FILE)

            if hatch_file and os.path.isfile(hatch_file):
                config = load_toml(hatch_file)
                hatch_config = hatch_config.copy()
                hatch_config.update(config)

            self._hatch = HatchMetadata(self.root, hatch_config, self.plugin_manager)

        return self._hatch

    def _set_version(self, core_metadata=None):
        if core_metadata is None:
            core_metadata = self.core

        version = core_metadata.version
        if version is None:
            version = self.hatch.version.cached
            source = f'source `{self.hatch.version.source_name}`'
            core_metadata._version_set = True
        else:
            source = 'field `project.version`'

        from packaging.version import InvalidVersion, Version

        try:
            normalized_version = str(Version(version))
        except InvalidVersion:
            raise ValueError(
                # Put text on its own line to prevent mostly duplicate output
                f'Invalid version `{version}` from {source}, see https://peps.python.org/pep-0440/'
            )
        else:
            self._version = normalized_version

    def validate_fields(self):
        _ = self.version
        self.core.validate_fields()


class BuildMetadata:
    """
    https://peps.python.org/pep-0517/
    """

    def __init__(self, root, config):
        self.root = root
        self.config = config

        self._requires = None
        self._requires_complex = None
        self._build_backend = None
        self._backend_path = None

    @property
    def requires_complex(self):
        if self._requires_complex is None:
            from packaging.requirements import InvalidRequirement, Requirement

            requires = self.config.get('requires', [])
            if not isinstance(requires, list):
                raise TypeError('Field `build-system.requires` must be an array')

            requires_complex = []

            for i, entry in enumerate(requires, 1):
                if not isinstance(entry, str):
                    raise TypeError(f'Dependency #{i} of field `build-system.requires` must be a string')

                try:
                    requires_complex.append(Requirement(entry))
                except InvalidRequirement as e:
                    raise ValueError(f'Dependency #{i} of field `build-system.requires` is invalid: {e}')

            self._requires_complex = requires_complex

        return self._requires_complex

    @property
    def requires(self):
        if self._requires is None:
            self._requires = [str(r) for r in self.requires_complex]

        return self._requires

    @property
    def build_backend(self):
        if self._build_backend is None:
            build_backend = self.config.get('build-backend', '')
            if not isinstance(build_backend, str):
                raise TypeError('Field `build-system.build-backend` must be a string')

            self._build_backend = build_backend

        return self._build_backend

    @property
    def backend_path(self):
        if self._backend_path is None:
            backend_path = self.config.get('backend-path', [])
            if not isinstance(backend_path, list):
                raise TypeError('Field `build-system.backend-path` must be an array')

            for i, entry in enumerate(backend_path, 1):
                if not isinstance(entry, str):
                    raise TypeError(f'Entry #{i} of field `build-system.backend-path` must be a string')

            self._backend_path = backend_path

        return self._backend_path


class CoreMetadata:
    """
    https://peps.python.org/pep-0621/
    """

    def __init__(self, root, config, hatch_metadata, context):
        self.root = root
        self.config = config
        self.hatch_metadata = hatch_metadata
        self.context = context

        self._raw_name = None
        self._name = None
        self._version = None
        self._description = None
        self._readme = None
        self._readme_content_type = None
        self._readme_path = None
        self._requires_python = None
        self._python_constraint = None
        self._license = None
        self._license_expression = None
        self._license_files = None
        self._authors = None
        self._authors_data = None
        self._maintainers = None
        self._maintainers_data = None
        self._keywords = None
        self._classifiers = None
        self._extra_classifiers = set()
        self._urls = None
        self._scripts = None
        self._gui_scripts = None
        self._entry_points = None
        self._dependencies_complex = None
        self._dependencies = None
        self._optional_dependencies_complex = None
        self._optional_dependencies = None
        self._dynamic = None

        # Indicates that the version has been successfully set dynamically
        self._version_set = False

    @property
    def raw_name(self):
        """
        https://peps.python.org/pep-0621/#name
        """
        if self._raw_name is None:
            if 'name' in self.dynamic:
                raise ValueError('Static metadata field `name` cannot be present in field `project.dynamic`')
            elif 'name' in self.config:
                raw_name = self.config['name']
            else:
                raw_name = ''

            if not raw_name:
                raise ValueError('Missing required field `project.name`')
            elif not isinstance(raw_name, str):
                raise TypeError('Field `project.name` must be a string')

            if not is_valid_project_name(raw_name):
                raise ValueError(
                    'Required field `project.name` must only contain ASCII letters/digits, underscores, '
                    'hyphens, and periods, and must begin and end with ASCII letters/digits.'
                )

            self._raw_name = raw_name

        return self._raw_name

    @property
    def name(self):
        """
        https://peps.python.org/pep-0621/#name
        """
        if self._name is None:
            self._name = normalize_project_name(self.raw_name)

        return self._name

    @property
    def version(self):
        """
        https://peps.python.org/pep-0621/#version
        """
        if self._version is None:
            if 'version' not in self.config:
                if not self._version_set and 'version' not in self.dynamic:
                    raise ValueError(
                        'Field `project.version` can only be resolved dynamically '
                        'if `version` is in field `project.dynamic`'
                    )
            else:
                if 'version' in self.dynamic:
                    raise ValueError(
                        'Metadata field `version` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )

                version = self.config['version']
                if not isinstance(version, str):
                    raise TypeError('Field `project.version` must be a string')

                self._version = version

        return self._version

    @property
    def description(self):
        """
        https://peps.python.org/pep-0621/#description
        """
        if self._description is None:
            if 'description' in self.config:
                description = self.config['description']
                if 'description' in self.dynamic:
                    raise ValueError(
                        'Metadata field `description` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )
            else:
                description = ''

            if not isinstance(description, str):
                raise TypeError('Field `project.description` must be a string')

            self._description = description

        return self._description

    @property
    def readme(self):
        """
        https://peps.python.org/pep-0621/#readme
        """
        if self._readme is None:
            if 'readme' in self.config:
                readme = self.config['readme']
                if 'readme' in self.dynamic:
                    raise ValueError(
                        'Metadata field `readme` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )
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
                    raise TypeError(
                        f'Unable to determine the content-type based on the extension of readme file: {readme}'
                    )

                readme_path = os.path.normpath(os.path.join(self.root, readme))
                if not os.path.isfile(readme_path):
                    raise OSError(f'Readme file does not exist: {readme}')

                with open(readme_path, encoding='utf-8') as f:
                    self._readme = f.read()

                self._readme_content_type = content_type
                self._readme_path = readme
            elif isinstance(readme, dict):
                content_type = readme.get('content-type')
                if content_type is None:
                    raise ValueError('Field `content-type` is required in the `project.readme` table')
                elif not isinstance(content_type, str):
                    raise TypeError('Field `content-type` in the `project.readme` table must be a string')
                elif content_type not in ('text/markdown', 'text/x-rst', 'text/plain'):
                    raise ValueError(
                        'Field `content-type` in the `project.readme` table must be one of the following: '
                        'text/markdown, text/x-rst, text/plain'
                    )

                if 'file' in readme and 'text' in readme:
                    raise ValueError('Cannot specify both `file` and `text` in the `project.readme` table')

                if 'file' in readme:
                    relative_path = readme['file']
                    if not isinstance(relative_path, str):
                        raise TypeError('Field `file` in the `project.readme` table must be a string')

                    path = os.path.normpath(os.path.join(self.root, relative_path))
                    if not os.path.isfile(path):
                        raise OSError(f'Readme file does not exist: {relative_path}')

                    with open(path, encoding=readme.get('charset', 'utf-8')) as f:
                        contents = f.read()

                    readme_path = relative_path
                elif 'text' in readme:
                    contents = readme['text']
                    if not isinstance(contents, str):
                        raise TypeError('Field `text` in the `project.readme` table must be a string')

                    readme_path = ''
                else:
                    raise ValueError('Must specify either `file` or `text` in the `project.readme` table')

                self._readme = contents
                self._readme_content_type = content_type
                self._readme_path = readme_path
            else:
                raise TypeError('Field `project.readme` must be a string or a table')

            self._readme = self._readme

        return self._readme

    @property
    def readme_content_type(self):
        """
        https://peps.python.org/pep-0621/#readme
        """
        if self._readme_content_type is None:
            _ = self.readme

        return self._readme_content_type

    @property
    def readme_path(self):
        """
        https://peps.python.org/pep-0621/#readme
        """
        if self._readme_path is None:
            _ = self.readme

        return self._readme_path

    @property
    def requires_python(self):
        """
        https://peps.python.org/pep-0621/#requires-python
        """
        if self._requires_python is None:
            from packaging.specifiers import InvalidSpecifier, SpecifierSet

            if 'requires-python' in self.config:
                requires_python = self.config['requires-python']
                if 'requires-python' in self.dynamic:
                    raise ValueError(
                        'Metadata field `requires-python` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )
            else:
                requires_python = ''

            if not isinstance(requires_python, str):
                raise TypeError('Field `project.requires-python` must be a string')

            try:
                self._python_constraint = SpecifierSet(requires_python)
            except InvalidSpecifier as e:
                raise ValueError(f'Field `project.requires-python` is invalid: {e}')

            self._requires_python = str(self._python_constraint)

        return self._requires_python

    @property
    def python_constraint(self):
        if self._python_constraint is None:
            _ = self.requires_python

        return self._python_constraint

    @property
    def license(self):
        """
        https://peps.python.org/pep-0621/#license
        """
        if self._license is None:
            if 'license' in self.config:
                data = self.config['license']
                if 'license' in self.dynamic:
                    raise ValueError(
                        'Metadata field `license` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )
            else:
                data = None

            if data is None:
                self._license = ''
                self._license_expression = ''
            elif isinstance(data, str):
                from hatchling.licenses.parse import normalize_license_expression

                try:
                    self._license_expression = normalize_license_expression(data)
                except ValueError as e:
                    raise ValueError(f'Error parsing field `project.license` - {e}') from None

                self._license = ''
            elif isinstance(data, dict):
                if 'file' in data and 'text' in data:
                    raise ValueError('Cannot specify both `file` and `text` in the `project.license` table')

                if 'file' in data:
                    relative_path = data['file']
                    if not isinstance(relative_path, str):
                        raise TypeError('Field `file` in the `project.license` table must be a string')

                    path = os.path.normpath(os.path.join(self.root, relative_path))
                    if not os.path.isfile(path):
                        raise OSError(f'License file does not exist: {relative_path}')

                    with open(path, encoding='utf-8') as f:
                        contents = f.read()
                elif 'text' in data:
                    contents = data['text']
                    if not isinstance(contents, str):
                        raise TypeError('Field `text` in the `project.license` table must be a string')
                else:
                    raise ValueError('Must specify either `file` or `text` in the `project.license` table')

                self._license = contents
                self._license_expression = ''
            else:
                raise TypeError('Field `project.license` must be a string or a table')

        return self._license

    @property
    def license_expression(self):
        """
        https://peps.python.org/pep-0639/
        """
        if self._license_expression is None:
            _ = self.license

        return self._license_expression

    @property
    def license_files(self):
        """
        https://peps.python.org/pep-0639/
        """
        if self._license_files is None:
            if 'license-files' not in self.config:
                data = {'globs': ['LICEN[CS]E*', 'COPYING*', 'NOTICE*', 'AUTHORS*']}
            else:
                if 'license-files' in self.dynamic:
                    raise ValueError(
                        'Metadata field `license-files` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )

                data = self.config['license-files']
                if not isinstance(data, dict):
                    raise TypeError('Field `project.license-files` must be a table')
                elif 'paths' in data and 'globs' in data:
                    raise ValueError('Cannot specify both `paths` and `globs` in the `project.license-files` table')

            license_files = []
            if 'paths' in data:
                paths = data['paths']
                if not isinstance(paths, list):
                    raise TypeError('Field `paths` in the `project.license-files` table must be an array')

                for i, relative_path in enumerate(paths, 1):
                    if not isinstance(relative_path, str):
                        raise TypeError(
                            f'Entry #{i} in field `paths` in the `project.license-files` table must be a string'
                        )

                    path = os.path.normpath(os.path.join(self.root, relative_path))
                    if not os.path.isfile(path):
                        raise OSError(f'License file does not exist: {relative_path}')

                    license_files.append(os.path.relpath(path, self.root).replace('\\', '/'))
            elif 'globs' in data:
                from glob import glob

                globs = data['globs']
                if not isinstance(globs, list):
                    raise TypeError('Field `globs` in the `project.license-files` table must be an array')

                for i, pattern in enumerate(globs, 1):
                    if not isinstance(pattern, str):
                        raise TypeError(
                            f'Entry #{i} in field `globs` in the `project.license-files` table must be a string'
                        )

                    full_pattern = os.path.normpath(os.path.join(self.root, pattern))
                    for path in glob(full_pattern):
                        if os.path.isfile(path):
                            license_files.append(os.path.relpath(path, self.root).replace('\\', '/'))
            else:
                raise ValueError(
                    'Must specify either `paths` or `globs` in the `project.license-files` table if defined'
                )

            self._license_files = sorted(license_files)

        return self._license_files

    @property
    def authors(self):
        """
        https://peps.python.org/pep-0621/#authors-maintainers
        """
        if self._authors is None:
            if 'authors' in self.config:
                authors = self.config['authors']
                if 'authors' in self.dynamic:
                    raise ValueError(
                        'Metadata field `authors` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )
            else:
                authors = []

            if not isinstance(authors, list):
                raise TypeError('Field `project.authors` must be an array')

            from email.headerregistry import Address

            authors = deepcopy(authors)
            authors_data = {'name': [], 'email': []}

            for i, data in enumerate(authors, 1):
                if not isinstance(data, dict):
                    raise TypeError(f'Author #{i} of field `project.authors` must be an inline table')

                name = data.get('name', '')
                if not isinstance(name, str):
                    raise TypeError(f'Name of author #{i} of field `project.authors` must be a string')

                email = data.get('email', '')
                if not isinstance(email, str):
                    raise TypeError(f'Email of author #{i} of field `project.authors` must be a string')

                if name and email:
                    authors_data['email'].append(str(Address(display_name=name, addr_spec=email)))
                elif email:
                    authors_data['email'].append(str(Address(addr_spec=email)))
                elif name:
                    authors_data['name'].append(name)
                else:
                    raise ValueError(f'Author #{i} of field `project.authors` must specify either `name` or `email`')

            self._authors = authors
            self._authors_data = authors_data

        return self._authors

    @property
    def authors_data(self):
        """
        https://peps.python.org/pep-0621/#authors-maintainers
        """
        if self._authors_data is None:
            _ = self.authors

        return self._authors_data

    @property
    def maintainers(self):
        """
        https://peps.python.org/pep-0621/#authors-maintainers
        """
        if self._maintainers is None:
            if 'maintainers' in self.config:
                maintainers = self.config['maintainers']
                if 'maintainers' in self.dynamic:
                    raise ValueError(
                        'Metadata field `maintainers` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )
            else:
                maintainers = []

            if not isinstance(maintainers, list):
                raise TypeError('Field `project.maintainers` must be an array')

            from email.headerregistry import Address

            maintainers = deepcopy(maintainers)
            maintainers_data = {'name': [], 'email': []}

            for i, data in enumerate(maintainers, 1):
                if not isinstance(data, dict):
                    raise TypeError(f'Maintainer #{i} of field `project.maintainers` must be an inline table')

                name = data.get('name', '')
                if not isinstance(name, str):
                    raise TypeError(f'Name of maintainer #{i} of field `project.maintainers` must be a string')

                email = data.get('email', '')
                if not isinstance(email, str):
                    raise TypeError(f'Email of maintainer #{i} of field `project.maintainers` must be a string')

                if name and email:
                    maintainers_data['email'].append(str(Address(display_name=name, addr_spec=email)))
                elif email:
                    maintainers_data['email'].append(str(Address(addr_spec=email)))
                elif name:
                    maintainers_data['name'].append(name)
                else:
                    raise ValueError(
                        f'Maintainer #{i} of field `project.maintainers` must specify either `name` or `email`'
                    )

            self._maintainers = maintainers
            self._maintainers_data = maintainers_data

        return self._maintainers

    @property
    def maintainers_data(self):
        """
        https://peps.python.org/pep-0621/#authors-maintainers
        """
        if self._maintainers_data is None:
            _ = self.maintainers

        return self._maintainers_data

    @property
    def keywords(self):
        """
        https://peps.python.org/pep-0621/#keywords
        """
        if self._keywords is None:
            if 'keywords' in self.config:
                keywords = self.config['keywords']
                if 'keywords' in self.dynamic:
                    raise ValueError(
                        'Metadata field `keywords` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )
            else:
                keywords = []

            if not isinstance(keywords, list):
                raise TypeError('Field `project.keywords` must be an array')

            unique_keywords = set()

            for i, keyword in enumerate(keywords, 1):
                if not isinstance(keyword, str):
                    raise TypeError(f'Keyword #{i} of field `project.keywords` must be a string')

                unique_keywords.add(keyword)

            self._keywords = sorted(unique_keywords)

        return self._keywords

    @property
    def classifiers(self):
        """
        https://peps.python.org/pep-0621/#classifiers
        """
        if self._classifiers is None:
            import bisect

            from hatchling.metadata.classifiers import KNOWN_CLASSIFIERS, SORTED_CLASSIFIERS, is_private

            if 'classifiers' in self.config:
                classifiers = self.config['classifiers']
                if 'classifiers' in self.dynamic:
                    raise ValueError(
                        'Metadata field `classifiers` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )
            else:
                classifiers = []

            if not isinstance(classifiers, list):
                raise TypeError('Field `project.classifiers` must be an array')

            known_classifiers = KNOWN_CLASSIFIERS | self._extra_classifiers
            unique_classifiers = set()

            for i, classifier in enumerate(classifiers, 1):
                if not isinstance(classifier, str):
                    raise TypeError(f'Classifier #{i} of field `project.classifiers` must be a string')
                elif not is_private(classifier) and classifier not in known_classifiers:
                    raise ValueError(f'Unknown classifier in field `project.classifiers`: {classifier}')

                unique_classifiers.add(classifier)

            sorted_classifiers = list(SORTED_CLASSIFIERS)
            for classifier in sorted(self._extra_classifiers - KNOWN_CLASSIFIERS):
                bisect.insort(sorted_classifiers, classifier)

            self._classifiers = sorted(
                unique_classifiers, key=lambda c: -1 if is_private(c) else sorted_classifiers.index(c)
            )

        return self._classifiers

    @property
    def urls(self):
        """
        https://peps.python.org/pep-0621/#urls
        """
        if self._urls is None:
            if 'urls' in self.config:
                urls = self.config['urls']
                if 'urls' in self.dynamic:
                    raise ValueError(
                        'Metadata field `urls` cannot be both statically defined and listed in field `project.dynamic`'
                    )
            else:
                urls = {}

            if not isinstance(urls, dict):
                raise TypeError('Field `project.urls` must be a table')

            sorted_urls = {}

            for label, url in urls.items():
                if not isinstance(url, str):
                    raise TypeError(f'URL `{label}` of field `project.urls` must be a string')

                sorted_urls[label] = url

            self._urls = sorted_urls

        return self._urls

    @property
    def scripts(self):
        """
        https://peps.python.org/pep-0621/#entry-points
        """
        if self._scripts is None:
            if 'scripts' in self.config:
                scripts = self.config['scripts']
                if 'scripts' in self.dynamic:
                    raise ValueError(
                        'Metadata field `scripts` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )
            else:
                scripts = {}

            if not isinstance(scripts, dict):
                raise TypeError('Field `project.scripts` must be a table')

            sorted_scripts = {}

            for name, object_ref in sorted(scripts.items()):
                if not isinstance(object_ref, str):
                    raise TypeError(f'Object reference `{name}` of field `project.scripts` must be a string')

                sorted_scripts[name] = object_ref

            self._scripts = sorted_scripts

        return self._scripts

    @property
    def gui_scripts(self):
        """
        https://peps.python.org/pep-0621/#entry-points
        """
        if self._gui_scripts is None:
            if 'gui-scripts' in self.config:
                gui_scripts = self.config['gui-scripts']
                if 'gui-scripts' in self.dynamic:
                    raise ValueError(
                        'Metadata field `gui-scripts` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )
            else:
                gui_scripts = {}

            if not isinstance(gui_scripts, dict):
                raise TypeError('Field `project.gui-scripts` must be a table')

            sorted_gui_scripts = {}

            for name, object_ref in sorted(gui_scripts.items()):
                if not isinstance(object_ref, str):
                    raise TypeError(f'Object reference `{name}` of field `project.gui-scripts` must be a string')

                sorted_gui_scripts[name] = object_ref

            self._gui_scripts = sorted_gui_scripts

        return self._gui_scripts

    @property
    def entry_points(self):
        """
        https://peps.python.org/pep-0621/#entry-points
        """
        if self._entry_points is None:
            if 'entry-points' in self.config:
                defined_entry_point_groups = self.config['entry-points']
                if 'entry-points' in self.dynamic:
                    raise ValueError(
                        'Metadata field `entry-points` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )
            else:
                defined_entry_point_groups = {}

            if not isinstance(defined_entry_point_groups, dict):
                raise TypeError('Field `project.entry-points` must be a table')

            for forbidden_field in ('scripts', 'gui-scripts'):
                if forbidden_field in defined_entry_point_groups:
                    raise ValueError(
                        f'Field `{forbidden_field}` must be defined as `project.{forbidden_field}` '
                        f'instead of in the `project.entry-points` table'
                    )

            entry_point_groups = {}

            for group, entry_point_data in sorted(defined_entry_point_groups.items()):
                if not isinstance(entry_point_data, dict):
                    raise TypeError(f'Field `project.entry-points.{group}` must be a table')

                entry_points = {}

                for name, object_ref in sorted(entry_point_data.items()):
                    if not isinstance(object_ref, str):
                        raise TypeError(
                            f'Object reference `{name}` of field `project.entry-points.{group}` must be a string'
                        )

                    entry_points[name] = object_ref

                if entry_points:
                    entry_point_groups[group] = entry_points

            self._entry_points = entry_point_groups

        return self._entry_points

    @property
    def dependencies_complex(self):
        """
        https://peps.python.org/pep-0621/#dependencies-optional-dependencies
        """
        if self._dependencies_complex is None:
            from packaging.requirements import InvalidRequirement, Requirement

            if 'dependencies' in self.config:
                dependencies = self.config['dependencies']
                if 'dependencies' in self.dynamic:
                    raise ValueError(
                        'Metadata field `dependencies` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )
            else:
                dependencies = []

            if not isinstance(dependencies, list):
                raise TypeError('Field `project.dependencies` must be an array')

            dependencies_complex = {}

            for i, entry in enumerate(dependencies, 1):
                if not isinstance(entry, str):
                    raise TypeError(f'Dependency #{i} of field `project.dependencies` must be a string')

                try:
                    requirement = Requirement(self.context.format(entry))
                except InvalidRequirement as e:
                    raise ValueError(f'Dependency #{i} of field `project.dependencies` is invalid: {e}')
                else:
                    if requirement.url and not self.hatch_metadata.allow_direct_references:
                        raise ValueError(
                            f'Dependency #{i} of field `project.dependencies` cannot be a direct reference unless '
                            f'field `tool.hatch.metadata.allow-direct-references` is set to `true`'
                        )

                    dependencies_complex[get_normalized_dependency(requirement)] = requirement

            self._dependencies_complex = dict(sorted(dependencies_complex.items()))

        return self._dependencies_complex

    @property
    def dependencies(self):
        """
        https://peps.python.org/pep-0621/#dependencies-optional-dependencies
        """
        if self._dependencies is None:
            self._dependencies = list(self.dependencies_complex)

        return self._dependencies

    @property
    def optional_dependencies_complex(self):
        """
        https://peps.python.org/pep-0621/#dependencies-optional-dependencies
        """
        if self._optional_dependencies_complex is None:
            from packaging.requirements import InvalidRequirement, Requirement

            if 'optional-dependencies' in self.config:
                optional_dependencies = self.config['optional-dependencies']
                if 'optional-dependencies' in self.dynamic:
                    raise ValueError(
                        'Metadata field `optional-dependencies` cannot be both statically defined and '
                        'listed in field `project.dynamic`'
                    )
            else:
                optional_dependencies = {}

            if not isinstance(optional_dependencies, dict):
                raise TypeError('Field `project.optional-dependencies` must be a table')

            normalized_options = {}
            optional_dependency_entries = {}

            for option, dependencies in optional_dependencies.items():
                if not is_valid_project_name(option):
                    raise ValueError(
                        f'Optional dependency group `{option}` of field `project.optional-dependencies` must only '
                        f'contain ASCII letters/digits, underscores, hyphens, and periods, and must begin and end with '
                        f'ASCII letters/digits.'
                    )
                elif not isinstance(dependencies, list):
                    raise TypeError(
                        f'Dependencies for option `{option}` of field `project.optional-dependencies` must be an array'
                    )

                entries = {}

                for i, entry in enumerate(dependencies, 1):
                    if not isinstance(entry, str):
                        raise TypeError(
                            f'Dependency #{i} of option `{option}` of field `project.optional-dependencies` '
                            f'must be a string'
                        )

                    try:
                        requirement = Requirement(self.context.format(entry))
                    except InvalidRequirement as e:
                        raise ValueError(
                            f'Dependency #{i} of option `{option}` of field `project.optional-dependencies` '
                            f'is invalid: {e}'
                        )
                    else:
                        if requirement.url and not self.hatch_metadata.allow_direct_references:
                            raise ValueError(
                                f'Dependency #{i} of option `{option}` of field `project.optional-dependencies` '
                                f'cannot be a direct reference unless field '
                                f'`tool.hatch.metadata.allow-direct-references` is set to `true`'
                            )

                        entries[get_normalized_dependency(requirement)] = requirement

                if self.hatch_metadata.allow_ambiguous_features:
                    normalized_option = option
                else:
                    normalized_option = normalize_project_name(option)
                if normalized_option in normalized_options:
                    raise ValueError(
                        f'Optional dependency groups `{normalized_options[normalized_option]}` and `{option}` of '
                        f'field `project.optional-dependencies` both evaluate to `{normalized_option}`.'
                    )

                normalized_options[normalized_option] = option
                optional_dependency_entries[normalized_option] = dict(sorted(entries.items()))

            self._optional_dependencies_complex = dict(sorted(optional_dependency_entries.items()))

        return self._optional_dependencies_complex

    @property
    def optional_dependencies(self):
        """
        https://peps.python.org/pep-0621/#dependencies-optional-dependencies
        """
        if self._optional_dependencies is None:
            self._optional_dependencies = {
                option: list(entries) for option, entries in self.optional_dependencies_complex.items()
            }

        return self._optional_dependencies

    @property
    def dynamic(self):
        """
        https://peps.python.org/pep-0621/#dynamic
        """
        if self._dynamic is None:
            self._dynamic = self.config.get('dynamic', [])

        return self._dynamic

    def add_known_classifiers(self, classifiers):
        self._extra_classifiers.update(classifiers)

    def validate_fields(self):
        # Trigger validation for everything
        for attribute in dir(self):
            getattr(self, attribute)


class HatchMetadata:
    def __init__(self, root, config, plugin_manager):
        self.root = root
        self.config = config
        self.plugin_manager = plugin_manager

        self._metadata = None
        self._build_config = None
        self._build_targets = None
        self._version = None

    @property
    def metadata(self):
        if self._metadata is None:
            metadata_config = self.config.get('metadata', {})
            if not isinstance(metadata_config, dict):
                raise TypeError('Field `tool.hatch.metadata` must be a table')

            self._metadata = HatchMetadataSettings(self.root, metadata_config, self.plugin_manager)

        return self._metadata

    @property
    def build_config(self):
        if self._build_config is None:
            build_config = self.config.get('build', {})
            if not isinstance(build_config, dict):
                raise TypeError('Field `tool.hatch.build` must be a table')

            self._build_config = build_config

        return self._build_config

    @property
    def build_targets(self):
        if self._build_targets is None:
            build_targets = self.build_config.get('targets', {})
            if not isinstance(build_targets, dict):
                raise TypeError('Field `tool.hatch.build.targets` must be a table')

            self._build_targets = build_targets

        return self._build_targets

    @property
    def version(self):
        if self._version is None:
            if 'version' not in self.config:
                raise ValueError('Missing `tool.hatch.version` configuration')

            options = self.config['version']
            if not isinstance(options, dict):
                raise TypeError('Field `tool.hatch.version` must be a table')

            self._version = HatchVersionConfig(self.root, deepcopy(options), self.plugin_manager)

        return self._version


class HatchVersionConfig:
    def __init__(self, root, config, plugin_manager):
        self.root = root
        self.config = config
        self.plugin_manager = plugin_manager

        self._cached = None
        self._source_name = None
        self._scheme_name = None
        self._source = None
        self._scheme = None

    @property
    def cached(self):
        if self._cached is None:
            try:
                self._cached = self.source.get_version_data()['version']
            except Exception as e:
                raise type(e)(f'Error getting the version from source `{self.source.PLUGIN_NAME}`: {e}') from None

        return self._cached

    @property
    def source_name(self):
        if self._source_name is None:
            source = self.config.get('source', 'regex')
            if not source:
                raise ValueError(
                    'The `source` option under the `tool.hatch.version` table must not be empty if defined'
                )
            elif not isinstance(source, str):
                raise TypeError('Field `tool.hatch.version.source` must be a string')

            self._source_name = source

        return self._source_name

    @property
    def scheme_name(self):
        if self._scheme_name is None:
            scheme = self.config.get('scheme', 'standard')
            if not scheme:
                raise ValueError(
                    'The `scheme` option under the `tool.hatch.version` table must not be empty if defined'
                )
            elif not isinstance(scheme, str):
                raise TypeError('Field `tool.hatch.version.scheme` must be a string')

            self._scheme_name = scheme

        return self._scheme_name

    @property
    def source(self):
        if self._source is None:
            from copy import deepcopy

            source_name = self.source_name
            version_source = self.plugin_manager.version_source.get(source_name)
            if version_source is None:
                from hatchling.plugin.exceptions import UnknownPluginError

                raise UnknownPluginError(f'Unknown version source: {source_name}')

            self._source = version_source(self.root, deepcopy(self.config))

        return self._source

    @property
    def scheme(self):
        if self._scheme is None:
            from copy import deepcopy

            scheme_name = self.scheme_name
            version_scheme = self.plugin_manager.version_scheme.get(scheme_name)
            if version_scheme is None:
                from hatchling.plugin.exceptions import UnknownPluginError

                raise UnknownPluginError(f'Unknown version scheme: {scheme_name}')

            self._scheme = version_scheme(self.root, deepcopy(self.config))

        return self._scheme


class HatchMetadataSettings:
    def __init__(self, root, config, plugin_manager):
        self.root = root
        self.config = config
        self.plugin_manager = plugin_manager

        self._allow_direct_references = None
        self._allow_ambiguous_features = None
        self._hook_config = None
        self._hooks = None

    @property
    def allow_direct_references(self):
        if self._allow_direct_references is None:
            allow_direct_references = self.config.get('allow-direct-references', False)
            if not isinstance(allow_direct_references, bool):
                raise TypeError('Field `tool.hatch.metadata.allow-direct-references` must be a boolean')

            self._allow_direct_references = allow_direct_references

        return self._allow_direct_references

    @property
    def allow_ambiguous_features(self):
        # TODO: remove in the first minor release after Jan 1, 2024
        if self._allow_ambiguous_features is None:
            allow_ambiguous_features = self.config.get('allow-ambiguous-features', False)
            if not isinstance(allow_ambiguous_features, bool):
                raise TypeError('Field `tool.hatch.metadata.allow-ambiguous-features` must be a boolean')

            self._allow_ambiguous_features = allow_ambiguous_features

        return self._allow_ambiguous_features

    @property
    def hook_config(self):
        if self._hook_config is None:
            hook_config = self.config.get('hooks', {})
            if not isinstance(hook_config, dict):
                raise TypeError('Field `tool.hatch.metadata.hooks` must be a table')

            self._hook_config = hook_config

        return self._hook_config

    @property
    def hooks(self):
        if self._hooks is None:
            hook_config = self.hook_config

            configured_hooks = {}
            for hook_name, config in hook_config.items():
                metadata_hook = self.plugin_manager.metadata_hook.get(hook_name)
                if metadata_hook is None:
                    from hatchling.plugin.exceptions import UnknownPluginError

                    raise UnknownPluginError(f'Unknown metadata hook: {hook_name}')

                configured_hooks[hook_name] = metadata_hook(self.root, config)

            self._hooks = configured_hooks

        return self._hooks
