from __future__ import annotations

from typing import TYPE_CHECKING

from hatchling.metadata.utils import get_normalized_dependency

if TYPE_CHECKING:
    from packaging.requirements import Requirement

    from hatch.dep.core import Dependency


def normalize_marker_quoting(text: str) -> str:
    # All TOML writers use double quotes, so allow copy/pasting to avoid escaping
    return text.replace('"', "'")


def get_normalized_dependencies(requirements: list[Requirement]) -> list[str]:
    normalized_dependencies = {get_normalized_dependency(requirement) for requirement in requirements}
    return sorted(normalized_dependencies)


def hash_dependencies(requirements: list[Dependency]) -> str:
    from hashlib import sha256

    data = "".join(
        sorted(
            # Internal spacing is ignored by PEP 440
            normalized_dependency.replace(" ", "")
            for normalized_dependency in {get_normalized_dependency(req) for req in requirements}
        )
    ).encode("utf-8")

    return sha256(data).hexdigest()


def get_complex_dependencies(dependencies: list[str]) -> dict[str, Dependency]:
    from hatch.dep.core import Dependency

    dependencies_complex = {}
    for dependency in dependencies:
        dependencies_complex[dependency] = Dependency(dependency)

    return dependencies_complex


def get_complex_features(features: dict[str, list[str]]) -> dict[str, dict[str, Dependency]]:
    from hatch.dep.core import Dependency

    optional_dependencies_complex = {}
    for feature, optional_dependencies in features.items():
        optional_dependencies_complex[feature] = {
            optional_dependency: Dependency(optional_dependency) for optional_dependency in optional_dependencies
        }

    return optional_dependencies_complex
