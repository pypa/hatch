DEFAULT_METADATA_VERSION = '2.1'


def get_core_metadata_constructors():
    """
    https://packaging.python.org/specifications/core-metadata/
    """
    return {
        '1.2': construct_metadata_file_1_2,
        '2.1': construct_metadata_file_2_1,
        '2.2': construct_metadata_file_2_2,
        '2.3': construct_metadata_file_2_3,
    }


def construct_metadata_file_1_2(metadata, extra_dependencies=()):
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


def construct_metadata_file_2_1(metadata, extra_dependencies=()):
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
                    metadata_file += f'Requires-Dist: {dependency} and extra == {option!r}\n'
                elif '@ ' in dependency:
                    metadata_file += f'Requires-Dist: {dependency} ; extra == {option!r}\n'
                else:
                    metadata_file += f'Requires-Dist: {dependency}; extra == {option!r}\n'

    if metadata.core.readme:
        metadata_file += f'Description-Content-Type: {metadata.core.readme_content_type}\n'
        metadata_file += f'\n{metadata.core.readme}'

    return metadata_file


def construct_metadata_file_2_2(metadata, extra_dependencies=()):
    """
    https://peps.python.org/pep-0643/
    """
    metadata_file = 'Metadata-Version: 2.2\n'
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
                    metadata_file += f'Requires-Dist: {dependency} and extra == {option!r}\n'
                elif '@ ' in dependency:
                    metadata_file += f'Requires-Dist: {dependency} ; extra == {option!r}\n'
                else:
                    metadata_file += f'Requires-Dist: {dependency}; extra == {option!r}\n'

    if metadata.core.readme:
        metadata_file += f'Description-Content-Type: {metadata.core.readme_content_type}\n'
        metadata_file += f'\n{metadata.core.readme}'

    return metadata_file


def construct_metadata_file_2_3(metadata, extra_dependencies=()):
    """
    https://peps.python.org/pep-0639/
    """
    metadata_file = 'Metadata-Version: 2.3\n'
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
                    metadata_file += f'Requires-Dist: {dependency} and extra == {option!r}\n'
                elif '@ ' in dependency:
                    metadata_file += f'Requires-Dist: {dependency} ; extra == {option!r}\n'
                else:
                    metadata_file += f'Requires-Dist: {dependency}; extra == {option!r}\n'

    if metadata.core.readme:
        metadata_file += f'Description-Content-Type: {metadata.core.readme_content_type}\n'
        metadata_file += f'\n{metadata.core.readme}'

    return metadata_file
