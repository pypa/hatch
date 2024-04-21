from __future__ import annotations

from typing import TYPE_CHECKING

from hatchling.metadata.utils import get_normalized_dependency

if TYPE_CHECKING:
    from packaging.requirements import Requirement

    from hatch.env.plugin.interface import EnvironmentInterface


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


def get_project_dependencies_complex(
    environment: EnvironmentInterface,
) -> tuple[dict[str, Requirement], dict[str, dict[str, Requirement]]]:
    from hatchling.dep.core import dependencies_in_sync

    dependencies_complex = {}
    optional_dependencies_complex = {}

    if not environment.metadata.hatch.metadata.hook_config or dependencies_in_sync(
        environment.metadata.build.requires_complex
    ):
        dependencies_complex.update(environment.metadata.core.dependencies_complex)
        optional_dependencies_complex.update(environment.metadata.core.optional_dependencies_complex)
    else:
        try:
            environment.check_compatibility()
        except Exception as e:  # noqa: BLE001
            environment.app.abort(f'Environment `{environment.name}` is incompatible: {e}')

        import json

        from packaging.requirements import Requirement

        with environment.root.as_cwd(), environment.build_environment(environment.metadata.build.requires):
            command = ['python', '-u', '-W', 'ignore', '-m', 'hatchling', 'metadata', '--compact']
            output = environment.platform.check_command_output(
                command,
                # Only capture stdout
                stderr=environment.platform.modules.subprocess.PIPE,
            )
            project_metadata = json.loads(output)

            for dependency in project_metadata.get('dependencies', []):
                dependencies_complex[dependency] = Requirement(dependency)

            for feature, optional_dependencies in project_metadata.get('optional-dependencies', {}).items():
                optional_dependencies_complex[feature] = {
                    optional_dependency: Requirement(optional_dependency)
                    for optional_dependency in optional_dependencies
                }

    return dependencies_complex, optional_dependencies_complex
