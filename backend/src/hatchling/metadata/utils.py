import re

# NOTE: this module should rarely be changed because it is likely to be used by other packages like Hatch


def is_valid_project_name(project_name):
    # https://peps.python.org/pep-0508/#names
    return re.search('^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$', project_name, re.IGNORECASE) is not None


def normalize_project_name(project_name):
    # https://peps.python.org/pep-0503/#normalized-names
    return re.sub(r'[-_.]+', '-', project_name).lower()


def get_normalized_dependency(requirement):
    # Changes to this function affect reproducibility between versions
    from packaging.specifiers import SpecifierSet

    requirement.name = normalize_project_name(requirement.name)

    if requirement.specifier:
        requirement.specifier = SpecifierSet(str(requirement.specifier).lower())

    if requirement.extras:
        requirement.extras = {normalize_project_name(extra) for extra in requirement.extras}

    # All TOML writers use double quotes, so allow direct writing or copy/pasting to avoid escaping
    return str(requirement).replace('"', "'")


def resolve_metadata_fields(metadata):
    # https://packaging.python.org/en/latest/specifications/declaring-project-metadata/
    return {
        'name': metadata.core.name,
        'version': metadata.version,
        'description': metadata.core.description,
        'readme': {'content-type': metadata.core.readme_content_type, 'text': metadata.core.readme},
        'requires-python': metadata.core.requires_python,
        'license': metadata.core.license_expression or metadata.core.license,
        'authors': metadata.core.authors,
        'maintainers': metadata.core.maintainers,
        'keywords': metadata.core.keywords,
        'classifiers': metadata.core.classifiers,
        'urls': metadata.core.urls,
        'scripts': metadata.core.scripts,
        'gui-scripts': metadata.core.gui_scripts,
        'entry-points': metadata.core.entry_points,
        'dependencies': metadata.core.dependencies,
        'optional-dependencies': metadata.core.optional_dependencies,
    }
