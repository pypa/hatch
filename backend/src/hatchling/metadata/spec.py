from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from hatchling.metadata.core import ProjectMetadata

DEFAULT_METADATA_VERSION = '2.3'
LATEST_METADATA_VERSION = '2.4'
CORE_METADATA_PROJECT_FIELDS = {
    'Author': ('authors',),
    'Author-email': ('authors',),
    'Classifier': ('classifiers',),
    'Description': ('readme',),
    'Description-Content-Type': ('readme',),
    'Dynamic': ('dynamic',),
    'Keywords': ('keywords',),
    'License': ('license',),
    'License-Expression': ('license',),
    'License-Files': ('license-files',),
    'Maintainer': ('maintainers',),
    'Maintainer-email': ('maintainers',),
    'Name': ('name',),
    'Provides-Extra': ('dependencies', 'optional-dependencies'),
    'Requires-Dist': ('dependencies',),
    'Requires-Python': ('requires-python',),
    'Summary': ('description',),
    'Project-URL': ('urls',),
    'Version': ('version',),
}
PROJECT_CORE_METADATA_FIELDS = {
    'authors': ('Author', 'Author-email'),
    'classifiers': ('Classifier',),
    'dependencies': ('Requires-Dist',),
    'dynamic': ('Dynamic',),
    'keywords': ('Keywords',),
    'license': ('License', 'License-Expression'),
    'license-files': ('License-Files',),
    'maintainers': ('Maintainer', 'Maintainer-email'),
    'name': ('Name',),
    'optional-dependencies': ('Requires-Dist', 'Provides-Extra'),
    'readme': ('Description', 'Description-Content-Type'),
    'requires-python': ('Requires-Python',),
    'description': ('Summary',),
    'urls': ('Project-URL',),
    'version': ('Version',),
}


def get_core_metadata_constructors() -> dict[str, Callable]:
    """
    https://packaging.python.org/specifications/core-metadata/
    """
    return {
        '1.2': construct_metadata_file_1_2,
        '2.1': construct_metadata_file_2_1,
        '2.2': construct_metadata_file_2_2,
        '2.3': construct_metadata_file_2_3,
        '2.4': construct_metadata_file_2_4,
    }


def project_metadata_from_core_metadata(core_metadata: str) -> dict[str, Any]:
    # https://packaging.python.org/en/latest/specifications/core-metadata/
    import email
    from email.headerregistry import HeaderRegistry

    header_registry = HeaderRegistry()

    message = email.message_from_string(core_metadata)
    metadata: dict[str, Any] = {}

    if name := message.get('Name'):
        metadata['name'] = name
    else:
        error_message = 'Missing required core metadata: Name'
        raise ValueError(error_message)

    if version := message.get('Version'):
        metadata['version'] = version
    else:
        error_message = 'Missing required core metadata: Version'
        raise ValueError(error_message)

    if (dynamic_fields := message.get_all('Dynamic')) is not None:
        # Use as an ordered set to retain bidirectional formatting.
        # This likely doesn't matter but we try hard around here.
        metadata['dynamic'] = list({
            project_field: None
            for core_metadata_field in dynamic_fields
            for project_field in CORE_METADATA_PROJECT_FIELDS.get(core_metadata_field, ())
        })

    if description := message.get_payload():
        metadata['readme'] = {
            'content-type': message.get('Description-Content-Type', 'text/plain'),
            'text': description,
        }

    if (license_expression := message.get('License-Expression')) is not None:
        metadata['license'] = license_expression
    elif (license_text := message.get('License')) is not None:
        metadata['license'] = {'text': license_text}

    if (license_files := message.get_all('License-File')) is not None:
        metadata['license-files'] = license_files

    if (summary := message.get('Summary')) is not None:
        metadata['description'] = summary

    if (keywords := message.get('Keywords')) is not None:
        metadata['keywords'] = keywords.split(',')

    if (classifiers := message.get_all('Classifier')) is not None:
        metadata['classifiers'] = classifiers

    if (project_urls := message.get_all('Project-URL')) is not None:
        urls = {}
        for project_url in project_urls:
            label, url = project_url.split(',', maxsplit=1)
            urls[label.strip()] = url.strip()
        metadata['urls'] = urls

    authors = []
    if (author := message.get('Author')) is not None:
        authors.append({'name': author})

    if (author_email := message.get('Author-email')) is not None:
        address_header = header_registry('resent-from', author_email)
        for address in address_header.addresses:  # type: ignore[attr-defined]
            data = {'email': address.addr_spec}
            if name := address.display_name:
                data['name'] = name
            authors.append(data)

    if authors:
        metadata['authors'] = authors

    maintainers = []
    if (maintainer := message.get('Maintainer')) is not None:
        maintainers.append({'name': maintainer})

    if (maintainer_email := message.get('Maintainer-email')) is not None:
        address_header = header_registry('resent-from', maintainer_email)
        for address in address_header.addresses:  # type: ignore[attr-defined]
            data = {'email': address.addr_spec}
            if name := address.display_name:
                data['name'] = name
            maintainers.append(data)

    if maintainers:
        metadata['maintainers'] = maintainers

    if (requires_python := message.get('Requires-Python')) is not None:
        metadata['requires-python'] = requires_python

    optional_dependencies: dict[str, list[str]] = {}
    if (extras := message.get_all('Provides-Extra')) is not None:
        for extra in extras:
            optional_dependencies[extra] = []

    if (requirements := message.get_all('Requires-Dist')) is not None:
        from packaging.requirements import Requirement

        dependencies = []
        for requirement in requirements:
            req = Requirement(requirement)
            if req.marker is None:
                dependencies.append(str(req))
                continue

            markers = req.marker._markers  # noqa: SLF001
            for i, marker in enumerate(markers):
                if isinstance(marker, tuple):
                    left, _, right = marker
                    if left.value == 'extra':
                        extra = right.value
                        del markers[i]  # noqa: B909
                        # If there was only one marker then there will be an unnecessary
                        # trailing semicolon in the string representation
                        if not markers:
                            req.marker = None
                        # Otherwise we need to remove the preceding `and` operation
                        else:
                            del markers[i - 1]

                        optional_dependencies.setdefault(extra, []).append(str(req))
                        break
            else:
                dependencies.append(str(req))

        metadata['dependencies'] = dependencies

    if optional_dependencies:
        metadata['optional-dependencies'] = optional_dependencies

    return metadata


def construct_metadata_file_1_2(metadata: ProjectMetadata, extra_dependencies: tuple[str] | None = None) -> str:
    """
    https://peps.python.org/pep-0345/
    """
    metadata_file = 'Metadata-Version: 1.2\n'
    metadata_file += f'Name: {metadata.core.raw_name}\n'
    metadata_file += f'Version: {metadata.version}\n'

    if metadata.core.description:
        metadata_file += f'Summary: {metadata.core.description}\n'

    if metadata.core.urls:
        for label, url in metadata.core.urls.items():
            metadata_file += f'Project-URL: {label}, {url}\n'

    authors_data = metadata.core.authors_data
    if authors_data['name']:
        metadata_file += f"Author: {', '.join(authors_data['name'])}\n"
    if authors_data['email']:
        metadata_file += f"Author-email: {', '.join(authors_data['email'])}\n"

    maintainers_data = metadata.core.maintainers_data
    if maintainers_data['name']:
        metadata_file += f"Maintainer: {', '.join(maintainers_data['name'])}\n"
    if maintainers_data['email']:
        metadata_file += f"Maintainer-email: {', '.join(maintainers_data['email'])}\n"

    if metadata.core.license:
        license_start = 'License: '
        indent = ' ' * (len(license_start) - 1)
        metadata_file += license_start

        for i, line in enumerate(metadata.core.license.splitlines()):
            if i == 0:
                metadata_file += f'{line}\n'
            else:
                metadata_file += f'{indent}{line}\n'
    elif metadata.core.license_expression:
        metadata_file += f'License: {metadata.core.license_expression}\n'

    if metadata.core.keywords:
        metadata_file += f"Keywords: {','.join(metadata.core.keywords)}\n"

    if metadata.core.classifiers:
        for classifier in metadata.core.classifiers:
            metadata_file += f'Classifier: {classifier}\n'

    if metadata.core.requires_python:
        metadata_file += f'Requires-Python: {metadata.core.requires_python}\n'

    if metadata.core.dependencies:
        for dependency in metadata.core.dependencies:
            metadata_file += f'Requires-Dist: {dependency}\n'

    if extra_dependencies:
        for dependency in extra_dependencies:
            metadata_file += f'Requires-Dist: {dependency}\n'

    return metadata_file


def construct_metadata_file_2_1(metadata: ProjectMetadata, extra_dependencies: tuple[str] | None = None) -> str:
    """
    https://peps.python.org/pep-0566/
    """
    metadata_file = 'Metadata-Version: 2.1\n'
    metadata_file += f'Name: {metadata.core.raw_name}\n'
    metadata_file += f'Version: {metadata.version}\n'

    if metadata.core.description:
        metadata_file += f'Summary: {metadata.core.description}\n'

    if metadata.core.urls:
        for label, url in metadata.core.urls.items():
            metadata_file += f'Project-URL: {label}, {url}\n'

    authors_data = metadata.core.authors_data
    if authors_data['name']:
        metadata_file += f"Author: {', '.join(authors_data['name'])}\n"
    if authors_data['email']:
        metadata_file += f"Author-email: {', '.join(authors_data['email'])}\n"

    maintainers_data = metadata.core.maintainers_data
    if maintainers_data['name']:
        metadata_file += f"Maintainer: {', '.join(maintainers_data['name'])}\n"
    if maintainers_data['email']:
        metadata_file += f"Maintainer-email: {', '.join(maintainers_data['email'])}\n"

    if metadata.core.license:
        license_start = 'License: '
        indent = ' ' * (len(license_start) - 1)
        metadata_file += license_start

        for i, line in enumerate(metadata.core.license.splitlines()):
            if i == 0:
                metadata_file += f'{line}\n'
            else:
                metadata_file += f'{indent}{line}\n'
    elif metadata.core.license_expression:
        metadata_file += f'License: {metadata.core.license_expression}\n'

    if metadata.core.keywords:
        metadata_file += f"Keywords: {','.join(metadata.core.keywords)}\n"

    if metadata.core.classifiers:
        for classifier in metadata.core.classifiers:
            metadata_file += f'Classifier: {classifier}\n'

    if metadata.core.requires_python:
        metadata_file += f'Requires-Python: {metadata.core.requires_python}\n'

    if metadata.core.dependencies:
        for dependency in metadata.core.dependencies:
            metadata_file += f'Requires-Dist: {dependency}\n'

    if extra_dependencies:
        for dependency in extra_dependencies:
            metadata_file += f'Requires-Dist: {dependency}\n'

    if metadata.core.optional_dependencies:
        for option, dependencies in metadata.core.optional_dependencies.items():
            metadata_file += f'Provides-Extra: {option}\n'
            for dependency in dependencies:
                if ';' in dependency:
                    dep_name, dep_env_marker = dependency.split(';', maxsplit=1)
                    metadata_file += f'Requires-Dist: {dep_name}; ({dep_env_marker.strip()}) and extra == {option!r}\n'
                elif '@ ' in dependency:
                    metadata_file += f'Requires-Dist: {dependency} ; extra == {option!r}\n'
                else:
                    metadata_file += f'Requires-Dist: {dependency}; extra == {option!r}\n'

    if metadata.core.readme:
        metadata_file += f'Description-Content-Type: {metadata.core.readme_content_type}\n'
        metadata_file += f'\n{metadata.core.readme}'

    return metadata_file


def construct_metadata_file_2_2(metadata: ProjectMetadata, extra_dependencies: tuple[str] | None = None) -> str:
    """
    https://peps.python.org/pep-0643/
    """
    metadata_file = 'Metadata-Version: 2.2\n'
    metadata_file += f'Name: {metadata.core.raw_name}\n'
    metadata_file += f'Version: {metadata.version}\n'

    if metadata.core.dynamic:
        # Ordered set
        for field in {
            core_metadata_field: None
            for project_field in metadata.core.dynamic
            for core_metadata_field in PROJECT_CORE_METADATA_FIELDS.get(project_field, ())
        }:
            metadata_file += f'Dynamic: {field}\n'

    if metadata.core.description:
        metadata_file += f'Summary: {metadata.core.description}\n'

    if metadata.core.urls:
        for label, url in metadata.core.urls.items():
            metadata_file += f'Project-URL: {label}, {url}\n'

    authors_data = metadata.core.authors_data
    if authors_data['name']:
        metadata_file += f"Author: {', '.join(authors_data['name'])}\n"
    if authors_data['email']:
        metadata_file += f"Author-email: {', '.join(authors_data['email'])}\n"

    maintainers_data = metadata.core.maintainers_data
    if maintainers_data['name']:
        metadata_file += f"Maintainer: {', '.join(maintainers_data['name'])}\n"
    if maintainers_data['email']:
        metadata_file += f"Maintainer-email: {', '.join(maintainers_data['email'])}\n"

    if metadata.core.license:
        license_start = 'License: '
        indent = ' ' * (len(license_start) - 1)
        metadata_file += license_start

        for i, line in enumerate(metadata.core.license.splitlines()):
            if i == 0:
                metadata_file += f'{line}\n'
            else:
                metadata_file += f'{indent}{line}\n'
    elif metadata.core.license_expression:
        metadata_file += f'License: {metadata.core.license_expression}\n'

    if metadata.core.keywords:
        metadata_file += f"Keywords: {','.join(metadata.core.keywords)}\n"

    if metadata.core.classifiers:
        for classifier in metadata.core.classifiers:
            metadata_file += f'Classifier: {classifier}\n'

    if metadata.core.requires_python:
        metadata_file += f'Requires-Python: {metadata.core.requires_python}\n'

    if metadata.core.dependencies:
        for dependency in metadata.core.dependencies:
            metadata_file += f'Requires-Dist: {dependency}\n'

    if extra_dependencies:
        for dependency in extra_dependencies:
            metadata_file += f'Requires-Dist: {dependency}\n'

    if metadata.core.optional_dependencies:
        for option, dependencies in metadata.core.optional_dependencies.items():
            metadata_file += f'Provides-Extra: {option}\n'
            for dependency in dependencies:
                if ';' in dependency:
                    dep_name, dep_env_marker = dependency.split(';', maxsplit=1)
                    metadata_file += f'Requires-Dist: {dep_name}; ({dep_env_marker.strip()}) and extra == {option!r}\n'
                elif '@ ' in dependency:
                    metadata_file += f'Requires-Dist: {dependency} ; extra == {option!r}\n'
                else:
                    metadata_file += f'Requires-Dist: {dependency}; extra == {option!r}\n'

    if metadata.core.readme:
        metadata_file += f'Description-Content-Type: {metadata.core.readme_content_type}\n'
        metadata_file += f'\n{metadata.core.readme}'

    return metadata_file


def construct_metadata_file_2_3(metadata: ProjectMetadata, extra_dependencies: tuple[str] | None = None) -> str:
    """
    https://peps.python.org/pep-0685/
    """
    metadata_file = 'Metadata-Version: 2.3\n'
    metadata_file += f'Name: {metadata.core.raw_name}\n'
    metadata_file += f'Version: {metadata.version}\n'

    if metadata.core.dynamic:
        # Ordered set
        for field in {
            core_metadata_field: None
            for project_field in metadata.core.dynamic
            for core_metadata_field in PROJECT_CORE_METADATA_FIELDS.get(project_field, ())
        }:
            metadata_file += f'Dynamic: {field}\n'

    if metadata.core.description:
        metadata_file += f'Summary: {metadata.core.description}\n'

    if metadata.core.urls:
        for label, url in metadata.core.urls.items():
            metadata_file += f'Project-URL: {label}, {url}\n'

    authors_data = metadata.core.authors_data
    if authors_data['name']:
        metadata_file += f"Author: {', '.join(authors_data['name'])}\n"
    if authors_data['email']:
        metadata_file += f"Author-email: {', '.join(authors_data['email'])}\n"

    maintainers_data = metadata.core.maintainers_data
    if maintainers_data['name']:
        metadata_file += f"Maintainer: {', '.join(maintainers_data['name'])}\n"
    if maintainers_data['email']:
        metadata_file += f"Maintainer-email: {', '.join(maintainers_data['email'])}\n"

    if metadata.core.license:
        license_start = 'License: '
        indent = ' ' * (len(license_start) - 1)
        metadata_file += license_start

        for i, line in enumerate(metadata.core.license.splitlines()):
            if i == 0:
                metadata_file += f'{line}\n'
            else:
                metadata_file += f'{indent}{line}\n'
    elif metadata.core.license_expression:
        metadata_file += f'License: {metadata.core.license_expression}\n'

    if metadata.core.keywords:
        metadata_file += f"Keywords: {','.join(metadata.core.keywords)}\n"

    if metadata.core.classifiers:
        for classifier in metadata.core.classifiers:
            metadata_file += f'Classifier: {classifier}\n'

    if metadata.core.requires_python:
        metadata_file += f'Requires-Python: {metadata.core.requires_python}\n'

    if metadata.core.dependencies:
        for dependency in metadata.core.dependencies:
            metadata_file += f'Requires-Dist: {dependency}\n'

    if extra_dependencies:
        for dependency in extra_dependencies:
            metadata_file += f'Requires-Dist: {dependency}\n'

    if metadata.core.optional_dependencies:
        for option, dependencies in metadata.core.optional_dependencies.items():
            metadata_file += f'Provides-Extra: {option}\n'
            for dependency in dependencies:
                if ';' in dependency:
                    dep_name, dep_env_marker = dependency.split(';', maxsplit=1)
                    metadata_file += f'Requires-Dist: {dep_name}; ({dep_env_marker.strip()}) and extra == {option!r}\n'
                elif '@ ' in dependency:
                    metadata_file += f'Requires-Dist: {dependency} ; extra == {option!r}\n'
                else:
                    metadata_file += f'Requires-Dist: {dependency}; extra == {option!r}\n'

    if metadata.core.readme:
        metadata_file += f'Description-Content-Type: {metadata.core.readme_content_type}\n'
        metadata_file += f'\n{metadata.core.readme}'

    return metadata_file


def construct_metadata_file_2_4(metadata: ProjectMetadata, extra_dependencies: tuple[str] | None = None) -> str:
    """
    https://peps.python.org/pep-0639/
    """
    metadata_file = 'Metadata-Version: 2.4\n'
    metadata_file += f'Name: {metadata.core.raw_name}\n'
    metadata_file += f'Version: {metadata.version}\n'

    if metadata.core.dynamic:
        # Ordered set
        for field in {
            core_metadata_field: None
            for project_field in metadata.core.dynamic
            for core_metadata_field in PROJECT_CORE_METADATA_FIELDS.get(project_field, ())
        }:
            metadata_file += f'Dynamic: {field}\n'

    if metadata.core.description:
        metadata_file += f'Summary: {metadata.core.description}\n'

    if metadata.core.urls:
        for label, url in metadata.core.urls.items():
            metadata_file += f'Project-URL: {label}, {url}\n'

    authors_data = metadata.core.authors_data
    if authors_data['name']:
        metadata_file += f"Author: {', '.join(authors_data['name'])}\n"
    if authors_data['email']:
        metadata_file += f"Author-email: {', '.join(authors_data['email'])}\n"

    maintainers_data = metadata.core.maintainers_data
    if maintainers_data['name']:
        metadata_file += f"Maintainer: {', '.join(maintainers_data['name'])}\n"
    if maintainers_data['email']:
        metadata_file += f"Maintainer-email: {', '.join(maintainers_data['email'])}\n"

    if metadata.core.license:
        license_start = 'License: '
        indent = ' ' * (len(license_start) - 1)
        metadata_file += license_start

        for i, line in enumerate(metadata.core.license.splitlines()):
            if i == 0:
                metadata_file += f'{line}\n'
            else:
                metadata_file += f'{indent}{line}\n'

    if metadata.core.license_expression:
        metadata_file += f'License-Expression: {metadata.core.license_expression}\n'

    if metadata.core.license_files:
        for license_file in metadata.core.license_files:
            metadata_file += f'License-File: {license_file}\n'

    if metadata.core.keywords:
        metadata_file += f"Keywords: {','.join(metadata.core.keywords)}\n"

    if metadata.core.classifiers:
        for classifier in metadata.core.classifiers:
            metadata_file += f'Classifier: {classifier}\n'

    if metadata.core.requires_python:
        metadata_file += f'Requires-Python: {metadata.core.requires_python}\n'

    if metadata.core.dependencies:
        for dependency in metadata.core.dependencies:
            metadata_file += f'Requires-Dist: {dependency}\n'

    if extra_dependencies:
        for dependency in extra_dependencies:
            metadata_file += f'Requires-Dist: {dependency}\n'

    if metadata.core.optional_dependencies:
        for option, dependencies in metadata.core.optional_dependencies.items():
            metadata_file += f'Provides-Extra: {option}\n'
            for dependency in dependencies:
                if ';' in dependency:
                    dep_name, dep_env_marker = dependency.split(';', maxsplit=1)
                    metadata_file += f'Requires-Dist: {dep_name}; ({dep_env_marker.strip()}) and extra == {option!r}\n'
                elif '@ ' in dependency:
                    metadata_file += f'Requires-Dist: {dependency} ; extra == {option!r}\n'
                else:
                    metadata_file += f'Requires-Dist: {dependency}; extra == {option!r}\n'

    if metadata.core.readme:
        metadata_file += f'Description-Content-Type: {metadata.core.readme_content_type}\n'
        metadata_file += f'\n{metadata.core.readme}'

    return metadata_file
