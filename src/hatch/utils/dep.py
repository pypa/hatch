from hatchling.metadata.utils import get_normalized_dependency


def normalize_marker_quoting(text):
    # All TOML writers use double quotes, so allow copy/pasting to avoid escaping
    return text.replace('"', "'")


def get_normalized_dependencies(requirements):
    normalized_dependencies = {get_normalized_dependency(requirement) for requirement in requirements}
    return sorted(normalized_dependencies)


def get_project_dependencies_complex(environment):
    from hatchling.dep.core import dependencies_in_sync

    dependencies_complex = {}
    optional_dependencies_complex = {}

    dynamic_fields = environment.metadata.dynamic
    if 'dependencies' not in dynamic_fields and 'optional-dependencies' not in dynamic_fields:
        dependencies_complex.update(environment.metadata.core.dependencies_complex)
        optional_dependencies_complex.update(environment.metadata.core.optional_dependencies_complex)
    elif dependencies_in_sync(environment.metadata.build.requires_complex):
        dependencies_complex.update(environment.metadata.core.dependencies_complex)
        optional_dependencies_complex.update(environment.metadata.core.optional_dependencies_complex)
    else:
        try:
            environment.check_compatibility()
        except Exception as e:
            environment.app.abort(f'Environment `{environment.name}` is incompatible: {e}')

        import json

        from packaging.requirements import Requirement

        with environment.root.as_cwd(), environment.build_environment(environment.metadata.build.requires):
            command = ['python', '-u', '-m', 'hatchling', 'metadata', '--app', '--compact']
            process = environment.platform.capture_process(command)
            project_metadata = json.loads(environment.app.read_builder(process))

            for dependency in project_metadata.get('dependencies', []):
                dependencies_complex[dependency] = Requirement(dependency)

            for feature, optional_dependencies in project_metadata.get('optional-dependencies', {}).items():
                optional_dependencies_complex[feature] = {
                    optional_dependency: Requirement(optional_dependency)
                    for optional_dependency in optional_dependencies
                }

    return dependencies_complex, optional_dependencies_complex
