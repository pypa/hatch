from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable

    from packaging.requirements import Requirement

    from hatchling.metadata.core import ProjectMetadata

# NOTE: this module should rarely be changed because it is likely to be used by other packages like Hatch


def is_valid_project_name(project_name: str) -> bool:
    # https://peps.python.org/pep-0508/#names
    return re.search("^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$", project_name, re.IGNORECASE) is not None


def normalize_project_name(project_name: str) -> str:
    # https://peps.python.org/pep-0503/#normalized-names
    return re.sub(r"[-_.]+", "-", project_name).lower()


def split_import_name_annotation(import_name: str) -> tuple[str, bool]:
    # https://packaging.python.org/en/latest/specifications/pyproject-toml/#import-names
    # https://packaging.python.org/en/latest/specifications/pyproject-toml/#import-namespaces
    #
    # An import name MAY be followed by `; private`, with any amount of whitespace surrounding
    # the semicolon. Returns the bare name and whether it was annotated private.
    if ";" not in import_name:
        return import_name, False

    name, annotation = import_name.split(";", 1)
    return name.strip(), annotation.strip() == "private"


def is_valid_import_name(import_name: str) -> bool:
    name, annotated_private = split_import_name_annotation(import_name)
    if ";" in import_name and not annotated_private:
        return False

    return all(module.isidentifier() for module in name.split("."))


def _escape_import_name_candidate(name: str) -> str:
    # Deliberately mirrors `BuilderInterface.normalize_file_name_component`
    # (hatchling/builders/plugin/interface.py), which escapes project names into candidate
    # on-disk directory/file names using the wheel filename escaping rule
    # (https://peps.python.org/pep-0427/#escaping-and-unicode). Reused here as-is, not because
    # import names are governed by PEP 427, but so that auto-detection searches for the exact
    # same candidate names the wheel builder's own package-detection heuristic would look for.
    # Cannot import the original directly without introducing a metadata -> builders cycle;
    # keep in sync if that changes.
    return re.sub(r"[^\w\d.]+", "_", name, flags=re.UNICODE)


def import_name_candidates(raw_name: str, name: str) -> tuple[str, ...]:
    return (_escape_import_name_candidate(raw_name), _escape_import_name_candidate(name))


def detect_import_names(root: str, candidates: Iterable[str]) -> list[str]:
    """
    Best-effort detection of the import name a project ships, based on common layouts
    (flat, src/, single-module). Returns an empty list if nothing matches; never raises.
    """
    for project_name in candidates:
        if os.path.isfile(os.path.join(root, project_name, "__init__.py")):
            return [project_name]

        if os.path.isfile(os.path.join(root, "src", project_name, "__init__.py")):
            return [project_name]

        if os.path.isfile(os.path.join(root, f"{project_name}.py")):
            return [project_name]

    return []


def detect_import_namespaces(root: str, candidates: Iterable[str]) -> tuple[list[str], list[str]]:
    """
    Best-effort detection of a single, unambiguous namespace-package layout
    (`<namespace>/<project_name>/__init__.py`). Returns a `(import_names, import_namespaces)`
    pair, both possibly empty; never raises.
    """
    from glob import glob

    for project_name in candidates:
        matches = glob(os.path.join(root, "*", project_name, "__init__.py"))
        if len(matches) == 1:
            namespace = os.path.relpath(matches[0], root).split(os.sep)[0]
            return [f"{namespace}.{project_name}"], [namespace]

    return [], []


def normalize_requirement(requirement: Requirement) -> None:
    # Changes to this function affect reproducibility between versions
    from packaging.specifiers import SpecifierSet

    requirement.name = normalize_project_name(requirement.name)

    if requirement.specifier:
        requirement.specifier = SpecifierSet(str(requirement.specifier).lower())

    if requirement.extras:
        requirement.extras = {normalize_project_name(extra) for extra in requirement.extras}


def format_dependency(requirement: Requirement) -> str:
    # All TOML writers use double quotes, so allow direct writing or copy/pasting to avoid escaping
    return str(requirement).replace('"', "'")


def get_normalized_dependency(requirement: Requirement) -> str:
    normalize_requirement(requirement)
    return format_dependency(requirement)


def resolve_metadata_fields(metadata: ProjectMetadata) -> dict[str, Any]:
    # https://packaging.python.org/en/latest/specifications/declaring-project-metadata/
    return {
        "name": metadata.core.name,
        "version": metadata.version,
        "description": metadata.core.description,
        "readme": {"content-type": metadata.core.readme_content_type, "text": metadata.core.readme},
        "requires-python": metadata.core.requires_python,
        "license": metadata.core.license_expression or metadata.core.license,
        "authors": metadata.core.authors,
        "maintainers": metadata.core.maintainers,
        "keywords": metadata.core.keywords,
        "classifiers": metadata.core.classifiers,
        "urls": metadata.core.urls,
        "scripts": metadata.core.scripts,
        "gui-scripts": metadata.core.gui_scripts,
        "entry-points": metadata.core.entry_points,
        "dependencies": metadata.core.dependencies,
        "optional-dependencies": metadata.core.optional_dependencies,
    }
