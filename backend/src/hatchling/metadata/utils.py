import re

# NOTE: this module should rarely be changed because it is likely to be used by other packages like Hatch


def is_valid_project_name(project_name):
    # https://www.python.org/dev/peps/pep-0508/#names
    return re.search('^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$', project_name, re.IGNORECASE) is not None


def normalize_project_name(project_name):
    # https://www.python.org/dev/peps/pep-0503/#normalized-names
    return re.sub(r'[-_.]+', '-', project_name).lower()


def get_normalized_dependency(requirement):
    # Changes to this function affect reproducibility between versions
    requirement.name = normalize_project_name(requirement.name)

    if requirement.extras:
        requirement.extras = {normalize_project_name(extra) for extra in requirement.extras}

    # All TOML writers use double quotes, so allow direct writing or copy/pasting to avoid escaping
    return str(requirement).lower().replace('"', "'")
