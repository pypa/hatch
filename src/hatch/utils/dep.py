from __future__ import annotations

from typing import Any

from packaging.requirements import Requirement

from hatchling.metadata.utils import get_normalized_dependency, normalize_project_name


def normalize_marker_quoting(text: str) -> str:
    # All TOML writers use double quotes, so allow copy/pasting to avoid escaping
    return text.replace('"', "'")


def get_normalized_dependencies(requirements: list[Requirement]) -> list[str]:
    normalized_dependencies = {get_normalized_dependency(requirement) for requirement in requirements}
    return sorted(normalized_dependencies)


def hash_dependencies(requirements: list[Requirement]) -> str:
    from hashlib import sha256

    data = ''.join(
        sorted(
            # Internal spacing is ignored by PEP 440
            normalized_dependency.replace(' ', '')
            for normalized_dependency in {get_normalized_dependency(req) for req in requirements}
        )
    ).encode('utf-8')

    return sha256(data).hexdigest()


def get_complex_dependencies(dependencies: list[str]) -> dict[str, Requirement]:
    from packaging.requirements import Requirement

    dependencies_complex = {}
    for dependency in dependencies:
        dependencies_complex[dependency] = Requirement(dependency)

    return dependencies_complex


def get_complex_features(features: dict[str, list[str]]) -> dict[str, dict[str, Requirement]]:
    from packaging.requirements import Requirement

    optional_dependencies_complex = {}
    for feature, optional_dependencies in features.items():
        optional_dependencies_complex[feature] = {
            optional_dependency: Requirement(optional_dependency) for optional_dependency in optional_dependencies
        }

    return optional_dependencies_complex


def get_complex_dependency_group(
    dependency_groups: dict[str, Any], group: str, past_groups: tuple[str, ...] = ()
) -> list[Requirement]:
    if group in past_groups:
        msg = f'Cyclic dependency group include: {group} -> {past_groups}'
        raise ValueError(msg)

    if group not in dependency_groups:
        msg = f"Dependency group '{group}' not found"
        raise LookupError(msg)

    raw_group = dependency_groups[group]
    if not isinstance(raw_group, list):
        msg = f"Dependency group '{group}' is not a list"
        raise TypeError(msg)

    realized_group = []
    for item in raw_group:
        if isinstance(item, str):
            realized_group.append(Requirement(item))
        elif isinstance(item, dict):
            if tuple(item.keys()) != ('include-group',):
                msg = f'Invalid dependency group item: {item}'
                raise ValueError(msg)

            include_group = normalize_project_name(next(iter(item.values())))
            realized_group.extend(get_complex_dependency_group(dependency_groups, include_group, (*past_groups, group)))
        else:
            msg = f'Invalid dependency group item: {item}'
            raise TypeError(msg)

    return realized_group
