from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
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


def resolve_metadata_fields(metadata: ProjectMetadata[Any]) -> dict[str, Any]:
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
