from __future__ import annotations

from collections import deque
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
    optional_dependencies: dict[str, list[str]],
    project_name: str,
    *,
    warn: Callable[[str], object] | None = None,
) -> dict[str, list[str]]:
    from packaging.requirements import Requirement

    normalized_project = normalize_project_name(project_name)

    # Build a lookup that indexes extras by both as-written and normalized name.
    extras_lookup: dict[str, list[str]] = {}
    for key, deps in optional_dependencies.items():
        extras_lookup[key] = deps
        normalized_key = normalize_project_name(key)
        if normalized_key != key:
            extras_lookup.setdefault(normalized_key, deps)

    def _lookup_extra(name: str) -> list[str] | None:
        """Find deps for an extra, preferring the as-written key."""
        if name in extras_lookup:
            return extras_lookup[name]
        normalized = normalize_project_name(name)
        return extras_lookup.get(normalized)

    # Resolve each extra independently: expand all self-references via BFS.
    resolved: dict[str, list[str]] = {}

    for extra_name, raw_deps in optional_dependencies.items():
        external_deps: list[str] = []
        seen_extras: set[str] = set()  # normalized extra names already visited
        queue: deque[str] = deque(raw_deps)

        while queue:
            dep_str = queue.popleft()
            req = Requirement(dep_str)
            dep_name_normalized = normalize_project_name(req.name)

            # Not a self-reference → keep as external dep
            if dep_name_normalized != normalized_project:
                external_deps.append(dep_str)
                continue

            # Self-reference without extras (e.g. bare "pkg") → drop silently
            if not req.extras:
                continue

            # Self-reference with extras → expand each referenced extra
            for referenced_extra in sorted(req.extras):
                norm_ref = normalize_project_name(referenced_extra)
                if norm_ref in seen_extras:
                    continue
                seen_extras.add(norm_ref)

                ref_deps = _lookup_extra(referenced_extra)
                if ref_deps is None:
                    if warn is not None:
                        warn(
                            f"Optional dependency group `{extra_name}` references "
                            f"extra `{referenced_extra}` which is not defined in "
                            f"project `{project_name}`"
                        )
                else:
                    queue.extend(ref_deps)

        resolved[extra_name] = external_deps

    return resolved
