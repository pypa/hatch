import re

from packaging.requirements import Requirement


def get_normalized_dependencies(dependencies):
    normalized_dependencies = set()
    for dependency in dependencies:
        requirement = Requirement(dependency)

        # https://www.python.org/dev/peps/pep-0503/#normalized-names
        requirement.name = re.sub(r'[-_.]+', '-', requirement.name)
        normalized_dependency = str(requirement).lower()

        # All TOML writers use double quotes, so allow copy/pasting to avoid escaping
        normalized_dependencies.add(normalized_dependency.replace('"', "'"))

    return sorted(normalized_dependencies)
