import os
import sys
from collections import OrderedDict
from copy import deepcopy

from ..utils.fs import locate_file
from .utils import get_normalized_dependency, is_valid_project_name, normalize_project_name

# TODO: remove when we drop Python 2
if sys.version_info[0] < 3:  # no cov
    from io import open

    import toml

    from ..utils.compat import byteify_object

    def load_toml(path):
        with open(path, 'r', encoding='utf-8') as f:
            # this is to support any `isinstance(metadata_entry, str)`
            return byteify_object(toml.loads(f.read()))

    def ensure_string(obj):
        if not isinstance(obj, bytes):
            return obj.encode('utf-8')
        return obj

else:
    import tomli

    def load_toml(path):
        with open(path, 'r', encoding='utf-8') as f:
            return tomli.loads(f.read())

    def ensure_string(obj):
        return obj


class ProjectMetadata(object):
    def __init__(self, root, plugin_manager, config=None):
        self.root = root
        self.plugin_manager = plugin_manager
        self._config = config
        self._build = None
        self._core = None
        self._hatch = None

        self._version = None
        self._project_file = None

        # App already loaded config
        if config is not None and root is not None:
            self._project_file = os.path.join(root, 'pyproject.toml')

    @property
    def version(self):
        """
        https://www.python.org/dev/peps/pep-0621/#version
        """
        if self._version is None:
            self._set_version()

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
            if 'project' not in self.config:
                raise ValueError('Missing `project` metadata table in configuration')

            core_metadata = self.config['project']
            if not isinstance(core_metadata, dict):
                raise TypeError('The `project` configuration must be a table')

            metadata = CoreMetadata(self.root, core_metadata, self.hatch.metadata)

            metadata_hooks = self.hatch.metadata.hooks
            if metadata_hooks:
                static_fields = set(core_metadata)
                self._set_version(metadata)
                core_metadata['version'] = self.version

                for metadata_hook in metadata_hooks.values():
                    metadata_hook.update(core_metadata)

                new_fields = set(core_metadata) - set(static_fields)
                for new_field in new_fields:
                    if new_field in metadata.dynamic:
                        metadata.dynamic.remove(new_field)
                    else:
                        raise ValueError(
                            'The field `{}` was set dynamically and therefore must '
                            'be listed in `project.dynamic`'.format(new_field)
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
                hatch_file = os.path.join(os.path.dirname(self._project_file), 'hatch.toml')
            else:
                hatch_file = locate_file(self.root, 'hatch.toml')

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
            version = self.hatch.version

        from packaging.version import Version

        self._version = str(Version(version))


class BuildMetadata(object):
    """
    https://www.python.org/dev/peps/pep-0517/
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
                    raise TypeError('Dependency #{} of field `build-system.requires` must be a string'.format(i))

                try:
                    requires_complex.append(Requirement(entry))
                except InvalidRequirement as e:
                    raise ValueError('Dependency #{} of field `build-system.requires` is invalid: {}'.format(i, e))

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
                    raise TypeError('Entry #{} of field `build-system.backend-path` must be a string'.format(i))

            self._backend_path = backend_path

        return self._backend_path


class CoreMetadata(object):
    """
    https://www.python.org/dev/peps/pep-0621/
    """

    def __init__(self, root, config, hatch_metadata):
        self.root = root
        self.config = config
        self.hatch_metadata = hatch_metadata

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
        self._urls = None
        self._scripts = None
        self._gui_scripts = None
        self._entry_points = None
        self._dependencies_complex = None
        self._dependencies = None
        self._optional_dependencies = None
        self._dynamic = None

    @property
    def name(self):
        """
        https://www.python.org/dev/peps/pep-0621/#name
        """
        if self._name is None:
            if 'name' in self.dynamic:
                raise ValueError('Static metadata field `name` cannot be present in field `project.dynamic`')
            elif 'name' in self.config:
                name = self.config['name']
            else:
                name = ''

            if not name:
                raise ValueError('Missing required field `project.name`')
            elif not isinstance(name, str):
                raise TypeError('Field `project.name` must be a string')

            if not is_valid_project_name(name):
                raise ValueError(
                    'Required field `project.name` must only contain ASCII letters/digits, underscores, '
                    'hyphens, and periods, and must begin and end with ASCII letters/digits.'
                )

            self._name = normalize_project_name(name)

        return self._name

    @property
    def version(self):
        """
        https://www.python.org/dev/peps/pep-0621/#version
        """
        if self._version is None:
            if 'version' not in self.config:
                if 'version' not in self.dynamic:
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
        https://www.python.org/dev/peps/pep-0621/#description
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
        https://www.python.org/dev/peps/pep-0621/#readme
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
                        'Unable to determine the content-type based on the extension of readme file: {}'.format(readme)
                    )

                readme_path = os.path.normpath(os.path.join(self.root, readme))
                if not os.path.isfile(readme_path):
                    raise OSError('Readme file does not exist: {}'.format(readme))

                with open(readme_path, 'r', encoding='utf-8') as f:
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
                        raise OSError('Readme file does not exist: {}'.format(relative_path))

                    with open(path, 'r', encoding=readme.get('charset', 'utf-8')) as f:
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

            self._readme = ensure_string(self._readme)

        return self._readme

    @property
    def readme_content_type(self):
        """
        https://www.python.org/dev/peps/pep-0621/#readme
        """
        if self._readme_content_type is None:
            _ = self.readme

        return self._readme_content_type

    @property
    def readme_path(self):
        """
        https://www.python.org/dev/peps/pep-0621/#readme
        """
        if self._readme_path is None:
            _ = self.readme

        return self._readme_path

    @property
    def requires_python(self):
        """
        https://www.python.org/dev/peps/pep-0621/#requires-python
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
                raise ValueError('Field `project.requires-python` is invalid: {}'.format(e))

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
        https://www.python.org/dev/peps/pep-0621/#license
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
                from ..licenses.parse import normalize_license_expression

                self._license_expression = normalize_license_expression(data)
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
                        raise OSError('License file does not exist: {}'.format(relative_path))

                    with open(path, 'r', encoding='utf-8') as f:
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
        https://www.python.org/dev/peps/pep-0639/
        """
        if self._license_expression is None:
            _ = self.license

        return self._license_expression

    @property
    def license_files(self):
        """
        https://www.python.org/dev/peps/pep-0639/
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
                            'Entry #{} in field `paths` in the `project.license-files` table must be a string'.format(i)
                        )

                    path = os.path.normpath(os.path.join(self.root, relative_path))
                    if not os.path.isfile(path):
                        raise OSError('License file does not exist: {}'.format(relative_path))

                    license_files.append(os.path.relpath(path, self.root).replace('\\', '/'))
            elif 'globs' in data:
                from glob import glob

                globs = data['globs']
                if not isinstance(globs, list):
                    raise TypeError('Field `globs` in the `project.license-files` table must be an array')

                for i, pattern in enumerate(globs, 1):
                    if not isinstance(pattern, str):
                        raise TypeError(
                            'Entry #{} in field `globs` in the `project.license-files` table must be a string'.format(i)
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
        https://www.python.org/dev/peps/pep-0621/#authors-maintainers
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

            try:
                from email.headerregistry import Address
            # TODO: remove when we drop Python 2
            except ImportError:  # no cov
                Address = (
                    lambda display_name='', addr_spec='': addr_spec
                    if not display_name
                    else '{} <{}>'.format(display_name, addr_spec)
                )

            authors = deepcopy(authors)
            authors_data = {'name': [], 'email': []}

            for i, data in enumerate(authors, 1):
                if not isinstance(data, dict):
                    raise TypeError('Author #{} of field `project.authors` must be an inline table'.format(i))

                name = data.get('name', '')
                if not isinstance(name, str):
                    raise TypeError('Name of author #{} of field `project.authors` must be a string'.format(i))

                email = data.get('email', '')
                if not isinstance(email, str):
                    raise TypeError('Email of author #{} of field `project.authors` must be a string'.format(i))

                if name and email:
                    authors_data['email'].append(str(Address(display_name=name, addr_spec=email)))
                elif email:
                    authors_data['email'].append(str(Address(addr_spec=email)))
                elif name:
                    authors_data['name'].append(name)
                else:
                    raise ValueError(
                        'Author #{} of field `project.authors` must specify either `name` or `email`'.format(i)
                    )

            self._authors = authors
            self._authors_data = authors_data

        return self._authors

    @property
    def authors_data(self):
        """
        https://www.python.org/dev/peps/pep-0621/#authors-maintainers
        """
        if self._authors_data is None:
            _ = self.authors

        return self._authors_data

    @property
    def maintainers(self):
        """
        https://www.python.org/dev/peps/pep-0621/#authors-maintainers
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

            try:
                from email.headerregistry import Address
            # TODO: remove when we drop Python 2
            except ImportError:  # no cov
                Address = (
                    lambda display_name='', addr_spec='': addr_spec
                    if not display_name
                    else '{} <{}>'.format(display_name, addr_spec)
                )

            maintainers = deepcopy(maintainers)
            maintainers_data = {'name': [], 'email': []}

            for i, data in enumerate(maintainers, 1):
                if not isinstance(data, dict):
                    raise TypeError('Maintainer #{} of field `project.maintainers` must be an inline table'.format(i))

                name = data.get('name', '')
                if not isinstance(name, str):
                    raise TypeError('Name of maintainer #{} of field `project.maintainers` must be a string'.format(i))

                email = data.get('email', '')
                if not isinstance(email, str):
                    raise TypeError('Email of maintainer #{} of field `project.maintainers` must be a string'.format(i))

                if name and email:
                    maintainers_data['email'].append(str(Address(display_name=name, addr_spec=email)))
                elif email:
                    maintainers_data['email'].append(str(Address(addr_spec=email)))
                elif name:
                    maintainers_data['name'].append(name)
                else:
                    raise ValueError(
                        'Maintainer #{} of field `project.maintainers` must specify either `name` or `email`'.format(i)
                    )

            self._maintainers = maintainers
            self._maintainers_data = maintainers_data

        return self._maintainers

    @property
    def maintainers_data(self):
        """
        https://www.python.org/dev/peps/pep-0621/#authors-maintainers
        """
        if self._maintainers_data is None:
            _ = self.maintainers

        return self._maintainers_data

    @property
    def keywords(self):
        """
        https://www.python.org/dev/peps/pep-0621/#keywords
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
                    raise TypeError('Keyword #{} of field `project.keywords` must be a string'.format(i))

                unique_keywords.add(keyword)

            self._keywords = sorted(unique_keywords)

        return self._keywords

    @property
    def classifiers(self):
        """
        https://www.python.org/dev/peps/pep-0621/#classifiers
        """
        if self._classifiers is None:
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

            unique_classifiers = set()

            for i, classifier in enumerate(classifiers, 1):
                if not isinstance(classifier, str):
                    raise TypeError('Classifier #{} of field `project.classifiers` must be a string'.format(i))

                unique_classifiers.add(classifier)

            self._classifiers = sorted(unique_classifiers)

        return self._classifiers

    @property
    def urls(self):
        """
        https://www.python.org/dev/peps/pep-0621/#urls
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

            sorted_urls = OrderedDict()

            for label, url in sorted(urls.items()):
                if not isinstance(url, str):
                    raise TypeError('URL `{}` of field `project.urls` must be a string'.format(label))

                sorted_urls[label] = url

            self._urls = sorted_urls

        return self._urls

    @property
    def scripts(self):
        """
        https://www.python.org/dev/peps/pep-0621/#entry-points
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

            sorted_scripts = OrderedDict()

            for name, object_ref in sorted(scripts.items()):
                if not isinstance(object_ref, str):
                    raise TypeError('Object reference `{}` of field `project.scripts` must be a string'.format(name))

                sorted_scripts[name] = object_ref

            self._scripts = sorted_scripts

        return self._scripts

    @property
    def gui_scripts(self):
        """
        https://www.python.org/dev/peps/pep-0621/#entry-points
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

            sorted_gui_scripts = OrderedDict()

            for name, object_ref in sorted(gui_scripts.items()):
                if not isinstance(object_ref, str):
                    raise TypeError(
                        'Object reference `{}` of field `project.gui-scripts` must be a string'.format(name)
                    )

                sorted_gui_scripts[name] = object_ref

            self._gui_scripts = sorted_gui_scripts

        return self._gui_scripts

    @property
    def entry_points(self):
        """
        https://www.python.org/dev/peps/pep-0621/#entry-points
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
                        'Field `{0}` must be defined as `project.{0}` instead of in '
                        'the `project.entry-points` table'.format(forbidden_field)
                    )

            entry_point_groups = OrderedDict()

            for group, entry_point_data in sorted(defined_entry_point_groups.items()):
                if not isinstance(entry_point_data, dict):
                    raise TypeError('Field `project.entry-points.{}` must be a table'.format(group))

                entry_points = OrderedDict()

                for name, object_ref in sorted(entry_point_data.items()):
                    if not isinstance(object_ref, str):
                        raise TypeError(
                            'Object reference `{}` of field `project.entry-points.{}` '
                            'must be a string'.format(name, group)
                        )

                    entry_points[name] = object_ref

                if entry_points:
                    entry_point_groups[group] = entry_points

            self._entry_points = entry_point_groups

        return self._entry_points

    @property
    def dependencies_complex(self):
        """
        https://www.python.org/dev/peps/pep-0621/#dependencies-optional-dependencies
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

            dependencies_complex = OrderedDict()

            for i, entry in enumerate(dependencies, 1):
                if not isinstance(entry, str):
                    raise TypeError('Dependency #{} of field `project.dependencies` must be a string'.format(i))

                try:
                    requirement = Requirement(entry)
                except InvalidRequirement as e:
                    raise ValueError('Dependency #{} of field `project.dependencies` is invalid: {}'.format(i, e))
                else:
                    if requirement.url and not self.hatch_metadata.allow_direct_references:
                        raise ValueError(
                            'Dependency #{} of field `project.dependencies` cannot be a direct reference'.format(i)
                        )

                    dependencies_complex[get_normalized_dependency(requirement)] = requirement

            self._dependencies_complex = dependencies_complex

        return self._dependencies_complex

    @property
    def dependencies(self):
        """
        https://www.python.org/dev/peps/pep-0621/#dependencies-optional-dependencies
        """
        if self._dependencies is None:
            self._dependencies = sorted(self.dependencies_complex)

        return self._dependencies

    @property
    def optional_dependencies(self):
        """
        https://www.python.org/dev/peps/pep-0621/#dependencies-optional-dependencies
        """
        if self._optional_dependencies is None:
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
                        'Optional dependency group `{}` of field `project.optional-dependencies` must only contain '
                        'ASCII letters/digits, underscores, hyphens, and periods, and must begin and end with '
                        'ASCII letters/digits.'.format(option)
                    )
                elif not isinstance(dependencies, list):
                    raise TypeError(
                        'Dependencies for option `{}` of field `project.optional-dependencies` '
                        'must be an array'.format(option)
                    )

                entries = set()

                for i, entry in enumerate(dependencies, 1):
                    if not isinstance(entry, str):
                        raise TypeError(
                            'Dependency #{} of option `{}` of field `project.optional-dependencies` '
                            'must be a string'.format(i, option)
                        )

                    try:
                        requirement = Requirement(entry)
                    except InvalidRequirement as e:
                        raise ValueError(
                            'Dependency #{} of option `{}` of field `project.optional-dependencies` '
                            'is invalid: {}'.format(i, option, e)
                        )
                    else:
                        if requirement.url and not self.hatch_metadata.allow_direct_references:
                            raise ValueError(
                                'Dependency #{} of option `{}` of field `project.optional-dependencies` '
                                'cannot be a direct reference'.format(i, option)
                            )

                        entries.add(get_normalized_dependency(requirement))

                normalized_option = normalize_project_name(option)
                if normalized_option in normalized_options:
                    raise ValueError(
                        'Optional dependency groups `{}` and `{}` of field `project.optional-dependencies` both '
                        'evaluate to `{}`.'.format(normalized_options[normalized_option], option, normalized_option)
                    )

                normalized_options[normalized_option] = option
                optional_dependency_entries[normalized_option] = sorted(entries)

            self._optional_dependencies = OrderedDict(sorted(optional_dependency_entries.items()))

        return self._optional_dependencies

    @property
    def dynamic(self):
        """
        https://www.python.org/dev/peps/pep-0621/#dynamic
        """
        if self._dynamic is None:
            dynamic = self.config.get('dynamic', [])
            if not isinstance(dynamic, list):
                raise TypeError('Field `project.dynamic` must be an array')

            for i, field in enumerate(dynamic, 1):
                if not isinstance(field, str):
                    raise TypeError('Field #{} of field `project.dynamic` must be a string'.format(i))

            self._dynamic = dynamic

        return self._dynamic

    def validate_fields(self):
        # Trigger validation for everything
        for attribute in dir(self):
            getattr(self, attribute)


class HatchMetadata(object):
    def __init__(self, root, config, plugin_manager):
        self.root = root
        self.config = config
        self.plugin_manager = plugin_manager

        self._metadata = None
        self._build_config = None
        self._build_targets = None
        self._version_source = None
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
            try:
                self._version = self.version_source.get_version_data()['version']
            except Exception as e:
                raise type(e)(
                    'Error getting the version from source `{}`: {}'.format(self.version_source.PLUGIN_NAME, e)
                )  # TODO: from None

        return self._version

    @property
    def version_source(self):
        if self._version_source is None:
            if 'version' not in self.config:
                raise ValueError('Missing `tool.hatch.version` configuration')

            options = self.config['version']
            if not isinstance(options, dict):
                raise TypeError('Field `tool.hatch.version` must be a table')

            options = deepcopy(options)

            source = options.get('source', 'regex')
            if not source:
                raise ValueError(
                    'The `source` option under the `tool.hatch.version` table must not be empty if defined'
                )
            elif not isinstance(source, str):
                raise TypeError('Field `tool.hatch.version.source` must be a string')

            version_source = self.plugin_manager.version_source.get(source)
            if version_source is None:
                raise ValueError('Unknown version source: {}'.format(source))

            self._version_source = version_source(self.root, options)

        return self._version_source


class HatchMetadataSettings(object):
    def __init__(self, root, config, plugin_manager):
        self.root = root
        self.config = config
        self.plugin_manager = plugin_manager

        self._allow_direct_references = None
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

            configured_hooks = OrderedDict()
            for hook_name, config in hook_config.items():
                metadata_hook = self.plugin_manager.metadata_hook.get(hook_name)
                if metadata_hook is None:
                    raise ValueError('Unknown metadata hook: {}'.format(hook_name))

                configured_hooks[hook_name] = metadata_hook(self.root, config)

            self._hooks = configured_hooks

        return self._hooks
