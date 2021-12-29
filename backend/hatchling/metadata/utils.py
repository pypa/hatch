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
    https://www.python.org/dev/peps/pep-0345/
    """
    metadata_file = 'Metadata-Version: 1.2\n'
    metadata_file += 'Name: {}\n'.format(metadata.core.name)
    metadata_file += 'Version: {}\n'.format(metadata.version)

    if metadata.core.description:
        metadata_file += 'Summary: {}\n'.format(metadata.core.description)

    if metadata.core.urls:
        for label, url in metadata.core.urls.items():
            metadata_file += 'Project-URL: {}, {}\n'.format(label, url)

    authors_data = metadata.core.authors_data
    if authors_data['name']:
        metadata_file += 'Author: {}\n'.format(', '.join(authors_data['name']))
    if authors_data['email']:
        metadata_file += 'Author-email: {}\n'.format(', '.join(authors_data['email']))

    maintainers_data = metadata.core.maintainers_data
    if maintainers_data['name']:
        metadata_file += 'Maintainer: {}\n'.format(', '.join(maintainers_data['name']))
    if maintainers_data['email']:
        metadata_file += 'Maintainer-email: {}\n'.format(', '.join(maintainers_data['email']))

    if metadata.core.license:
        license_start = 'License: '
        indent = ' ' * (len(license_start) - 1)
        metadata_file += license_start

        for i, line in enumerate(metadata.core.license.splitlines()):
            if i == 0:
                metadata_file += '{}\n'.format(line)
            else:
                metadata_file += '{}{}\n'.format(indent, line)

    if metadata.core.keywords:
        metadata_file += 'Keywords: {}\n'.format(','.join(metadata.core.keywords))

    if metadata.core.classifiers:
        for classifier in metadata.core.classifiers:
            metadata_file += 'Classifier: {}\n'.format(classifier)

    if metadata.core.requires_python:
        metadata_file += 'Requires-Python: {}\n'.format(metadata.core.requires_python)

    if metadata.core.dependencies:
        for dependency in metadata.core.dependencies:
            metadata_file += 'Requires-Dist: {}\n'.format(dependency)

    if extra_dependencies:
        for dependency in extra_dependencies:
            metadata_file += 'Requires-Dist: {}\n'.format(dependency)

    return metadata_file


def construct_metadata_file_2_1(metadata, extra_dependencies=()):
    """
    https://www.python.org/dev/peps/pep-0566/
    """
    metadata_file = 'Metadata-Version: 2.1\n'
    metadata_file += 'Name: {}\n'.format(metadata.core.name)
    metadata_file += 'Version: {}\n'.format(metadata.version)

    if metadata.core.description:
        metadata_file += 'Summary: {}\n'.format(metadata.core.description)

    if metadata.core.urls:
        for label, url in metadata.core.urls.items():
            metadata_file += 'Project-URL: {}, {}\n'.format(label, url)

    authors_data = metadata.core.authors_data
    if authors_data['name']:
        metadata_file += 'Author: {}\n'.format(', '.join(authors_data['name']))
    if authors_data['email']:
        metadata_file += 'Author-email: {}\n'.format(', '.join(authors_data['email']))

    maintainers_data = metadata.core.maintainers_data
    if maintainers_data['name']:
        metadata_file += 'Maintainer: {}\n'.format(', '.join(maintainers_data['name']))
    if maintainers_data['email']:
        metadata_file += 'Maintainer-email: {}\n'.format(', '.join(maintainers_data['email']))

    if metadata.core.license:
        license_start = 'License: '
        indent = ' ' * (len(license_start) - 1)
        metadata_file += license_start

        for i, line in enumerate(metadata.core.license.splitlines()):
            if i == 0:
                metadata_file += '{}\n'.format(line)
            else:
                metadata_file += '{}{}\n'.format(indent, line)

    if metadata.core.keywords:
        metadata_file += 'Keywords: {}\n'.format(','.join(metadata.core.keywords))

    if metadata.core.classifiers:
        for classifier in metadata.core.classifiers:
            metadata_file += 'Classifier: {}\n'.format(classifier)

    if metadata.core.requires_python:
        metadata_file += 'Requires-Python: {}\n'.format(metadata.core.requires_python)

    if metadata.core.dependencies:
        for dependency in metadata.core.dependencies:
            metadata_file += 'Requires-Dist: {}\n'.format(dependency)

    if extra_dependencies:
        for dependency in extra_dependencies:
            metadata_file += 'Requires-Dist: {}\n'.format(dependency)

    if metadata.core.optional_dependencies:
        for option, dependencies in metadata.core.optional_dependencies.items():
            metadata_file += 'Provides-Extra: {}\n'.format(option)
            for dependency in dependencies:
                if ';' in dependency:
                    metadata_file += 'Requires-Dist: {} and extra == "{}"\n'.format(dependency, option)
                else:
                    metadata_file += 'Requires-Dist: {}; extra == "{}"\n'.format(dependency, option)

    if metadata.core.readme:
        metadata_file += 'Description-Content-Type: {}\n'.format(metadata.core.readme_content_type)
        metadata_file += '\n{}'.format(metadata.core.readme)

    return metadata_file


def construct_metadata_file_2_2(metadata, extra_dependencies=()):
    """
    https://www.python.org/dev/peps/pep-0643/
    """
    metadata_file = 'Metadata-Version: 2.2\n'
    metadata_file += 'Name: {}\n'.format(metadata.core.name)
    metadata_file += 'Version: {}\n'.format(metadata.version)

    if metadata.core.description:
        metadata_file += 'Summary: {}\n'.format(metadata.core.description)

    if metadata.core.urls:
        for label, url in metadata.core.urls.items():
            metadata_file += 'Project-URL: {}, {}\n'.format(label, url)

    authors_data = metadata.core.authors_data
    if authors_data['name']:
        metadata_file += 'Author: {}\n'.format(', '.join(authors_data['name']))
    if authors_data['email']:
        metadata_file += 'Author-email: {}\n'.format(', '.join(authors_data['email']))

    maintainers_data = metadata.core.maintainers_data
    if maintainers_data['name']:
        metadata_file += 'Maintainer: {}\n'.format(', '.join(maintainers_data['name']))
    if maintainers_data['email']:
        metadata_file += 'Maintainer-email: {}\n'.format(', '.join(maintainers_data['email']))

    if metadata.core.license:
        license_start = 'License: '
        indent = ' ' * (len(license_start) - 1)
        metadata_file += license_start

        for i, line in enumerate(metadata.core.license.splitlines()):
            if i == 0:
                metadata_file += '{}\n'.format(line)
            else:
                metadata_file += '{}{}\n'.format(indent, line)

    if metadata.core.keywords:
        metadata_file += 'Keywords: {}\n'.format(','.join(metadata.core.keywords))

    if metadata.core.classifiers:
        for classifier in metadata.core.classifiers:
            metadata_file += 'Classifier: {}\n'.format(classifier)

    if metadata.core.requires_python:
        metadata_file += 'Requires-Python: {}\n'.format(metadata.core.requires_python)

    if metadata.core.dependencies:
        for dependency in metadata.core.dependencies:
            metadata_file += 'Requires-Dist: {}\n'.format(dependency)

    if extra_dependencies:
        for dependency in extra_dependencies:
            metadata_file += 'Requires-Dist: {}\n'.format(dependency)

    if metadata.core.optional_dependencies:
        for option, dependencies in metadata.core.optional_dependencies.items():
            metadata_file += 'Provides-Extra: {}\n'.format(option)
            for dependency in dependencies:
                if ';' in dependency:
                    metadata_file += 'Requires-Dist: {} and extra == "{}"\n'.format(dependency, option)
                else:
                    metadata_file += 'Requires-Dist: {}; extra == "{}"\n'.format(dependency, option)

    if metadata.core.readme:
        metadata_file += 'Description-Content-Type: {}\n'.format(metadata.core.readme_content_type)
        metadata_file += '\n{}'.format(metadata.core.readme)

    return metadata_file


def construct_metadata_file_2_3(metadata, extra_dependencies=()):
    """
    https://www.python.org/dev/peps/pep-0639/
    """
    metadata_file = 'Metadata-Version: 2.3\n'
    metadata_file += 'Name: {}\n'.format(metadata.core.name)
    metadata_file += 'Version: {}\n'.format(metadata.version)

    if metadata.core.description:
        metadata_file += 'Summary: {}\n'.format(metadata.core.description)

    if metadata.core.urls:
        for label, url in metadata.core.urls.items():
            metadata_file += 'Project-URL: {}, {}\n'.format(label, url)

    authors_data = metadata.core.authors_data
    if authors_data['name']:
        metadata_file += 'Author: {}\n'.format(', '.join(authors_data['name']))
    if authors_data['email']:
        metadata_file += 'Author-email: {}\n'.format(', '.join(authors_data['email']))

    maintainers_data = metadata.core.maintainers_data
    if maintainers_data['name']:
        metadata_file += 'Maintainer: {}\n'.format(', '.join(maintainers_data['name']))
    if maintainers_data['email']:
        metadata_file += 'Maintainer-email: {}\n'.format(', '.join(maintainers_data['email']))

    if metadata.core.license_expression:
        metadata_file += 'License-Expression: {}\n'.format(metadata.core.license_expression)

    if metadata.core.license_files:
        for license_file in metadata.core.license_files:
            metadata_file += 'License-File: {}\n'.format(license_file)

    if metadata.core.keywords:
        metadata_file += 'Keywords: {}\n'.format(','.join(metadata.core.keywords))

    if metadata.core.classifiers:
        for classifier in metadata.core.classifiers:
            metadata_file += 'Classifier: {}\n'.format(classifier)

    if metadata.core.requires_python:
        metadata_file += 'Requires-Python: {}\n'.format(metadata.core.requires_python)

    if metadata.core.dependencies:
        for dependency in metadata.core.dependencies:
            metadata_file += 'Requires-Dist: {}\n'.format(dependency)

    if extra_dependencies:
        for dependency in extra_dependencies:
            metadata_file += 'Requires-Dist: {}\n'.format(dependency)

    if metadata.core.optional_dependencies:
        for option, dependencies in metadata.core.optional_dependencies.items():
            metadata_file += 'Provides-Extra: {}\n'.format(option)
            for dependency in dependencies:
                if ';' in dependency:
                    metadata_file += 'Requires-Dist: {} and extra == "{}"\n'.format(dependency, option)
                else:
                    metadata_file += 'Requires-Dist: {}; extra == "{}"\n'.format(dependency, option)

    if metadata.core.readme:
        metadata_file += 'Description-Content-Type: {}\n'.format(metadata.core.readme_content_type)
        metadata_file += '\n{}'.format(metadata.core.readme)

    return metadata_file
