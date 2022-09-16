from packaging.requirements import Requirement

from hatchling.metadata.utils import get_normalized_dependency


def normalize_marker_quoting(text):
    # All TOML writers use double quotes, so allow copy/pasting to avoid escaping
    return text.replace('"', "'")


def get_normalized_dependencies(dependencies, context = None):
    """Normalizes dependencies, optionally context can be provided to perform context
    formatting before normalization"""
    if context:
        dependencies = [context.format(dependency) for dependency in dependencies]

    normalized_dependencies = {get_normalized_dependency(Requirement(dependency)) for dependency in dependencies}
    return sorted(normalized_dependencies)
