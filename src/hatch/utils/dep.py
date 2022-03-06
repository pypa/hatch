import re

from packaging.requirements import Requirement


def normalize_marker_quoting(text):
    # All TOML writers use double quotes, so allow copy/pasting to avoid escaping
    return text.replace('"', "'")


def get_normalized_dependencies(dependencies):
    normalized_dependencies = set()
    for dependency in dependencies:
        requirement = Requirement(dependency)

        # https://www.python.org/dev/peps/pep-0503/#normalized-names
        requirement.name = re.sub(r'[-_.]+', '-', requirement.name)

        normalized_dependencies.add(normalize_marker_quoting(str(requirement).lower()))

    return sorted(normalized_dependencies)
