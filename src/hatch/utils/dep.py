from __future__ import annotations

from typing import TYPE_CHECKING, Any

from hatchling.metadata.utils import get_normalized_dependency, normalize_project_name

if TYPE_CHECKING:
    from collections.abc import Callable

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


def get_complex_dependency_group(
    dependency_groups: dict[str, Any], group: str, past_groups: tuple[str, ...] = ()
) -> list[Dependency]:
    from hatch.dep.core import Dependency

    if group in past_groups:
        msg = f"Cyclic dependency group include: {group} -> {past_groups}"
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
            realized_group.append(Dependency(item))
        elif isinstance(item, dict):
            if tuple(item.keys()) != ("include-group",):
                msg = f"Invalid dependency group item: {item}"
                raise ValueError(msg)

            include_group = normalize_project_name(next(iter(item.values())))
            realized_group.extend(get_complex_dependency_group(dependency_groups, include_group, (*past_groups, group)))
        else:
            msg = f"Invalid dependency group item: {item}"
            raise TypeError(msg)

    return realized_group


def resolve_extras(
    deps: list[str],
    local_projects: dict[str, dict[str, list[str]]],
    *,
    warn: Callable[[str], object] | None = None,
) -> list[str]:
    """Expand extras on local-project dependencies transitively.

    Parameters
    ----------
    deps:
        Raw PEP 508 dependency strings to resolve.
    local_projects:
        Mapping of normalized project name → raw optional-dependencies dict.
        Self-referencing extras within each project AND cross-project extras
        are expanded in a single BFS pass.
    warn:
        Warning callback for undefined extras.

    Returns only dependency strings that do not reference any local project.
    """
    from collections import deque

    from packaging.requirements import Requirement

    from hatchling.metadata.utils import normalize_project_name

    external: list[str] = []
    seen: set[str] = set()
    queue: deque[str] = deque(deps)

    # Pre-build normalized lookups for each project's optional-deps keys.
    normalized_lookups: dict[str, dict[str, list[str]]] = {}
    for project_name, optional_deps in local_projects.items():
        lookup: dict[str, list[str]] = {}
        for key, value in optional_deps.items():
            lookup[key] = value
            norm_key = normalize_project_name(key)
            if norm_key != key:
                lookup.setdefault(norm_key, value)
        normalized_lookups[project_name] = lookup

    while queue:
        dep_str = queue.popleft()
        if dep_str in seen:
            continue
        seen.add(dep_str)

        req = Requirement(dep_str)
        name = normalize_project_name(req.name)

        if name not in local_projects:
            external.append(dep_str)
            continue

        if not req.extras:
            continue

        lookup = normalized_lookups[name]
        for extra in req.extras:
            norm_extra = normalize_project_name(extra)
            extra_deps = lookup.get(extra) or lookup.get(norm_extra)
            if extra_deps is None:
                if warn is not None:
                    warn(
                        f"Dependency `{dep_str}` refers to extra "
                        f"`{extra}`, which local project `{name}` does not define"
                    )
            else:
                queue.extend(extra_deps)

    return external
