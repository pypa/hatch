from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from hatch.cli.application import Application


@click.command(short_help='Show the available environments')
@click.argument('envs', required=False, nargs=-1)
@click.option('--ascii', 'force_ascii', is_flag=True, help='Whether or not to only use ASCII characters')
@click.option('--json', 'as_json', is_flag=True, help='Whether or not to output in JSON format')
@click.option('--internal', '-i', is_flag=True, help='Show internal environments')
@click.option('--hide-titles', is_flag=True, hidden=True)
@click.pass_obj
def show(
    app: Application,
    *,
    envs: tuple[str, ...],
    force_ascii: bool,
    as_json: bool,
    internal: bool,
    hide_titles: bool,
):
    """Show the available environments."""
    app.ensure_environment_plugin_dependencies()

    from hatch.config.constants import AppEnvVars

    if as_json:
        import json

        contextual_config = {}
        for environments in (app.project.config.envs, app.project.config.internal_envs):
            for env_name, config in environments.items():
                environment = app.get_environment(env_name)
                new_config = contextual_config[env_name] = dict(config)

                env_vars = dict(environment.env_vars)
                env_vars.pop(AppEnvVars.ENV_ACTIVE)
                if env_vars:
                    new_config['env-vars'] = env_vars

                num_dependencies = len(config.get('dependencies', []))
                dependencies = environment.environment_dependencies[:num_dependencies]
                if dependencies:
                    new_config['dependencies'] = dependencies

                extra_dependencies = environment.environment_dependencies[num_dependencies:]
                if extra_dependencies:
                    new_config['extra-dependencies'] = extra_dependencies

                if environment.pre_install_commands:
                    new_config['pre-install-commands'] = list(
                        environment.resolve_commands(environment.pre_install_commands)
                    )

                if environment.post_install_commands:
                    new_config['post-install-commands'] = list(
                        environment.resolve_commands(environment.post_install_commands)
                    )

                if environment.scripts:
                    new_config['scripts'] = {
                        script: list(environment.resolve_commands([script])) for script in environment.scripts
                    }

        app.display(json.dumps(contextual_config, separators=(',', ':')))
        return

    from packaging.requirements import InvalidRequirement, Requirement

    from hatchling.metadata.utils import get_normalized_dependency, normalize_project_name

    if internal:
        target_standalone_envs = app.project.config.internal_envs
        target_matrices = app.project.config.internal_matrices
    else:
        target_standalone_envs = app.project.config.envs
        target_matrices = app.project.config.matrices

    for env_name in envs:
        if env_name not in target_standalone_envs and env_name not in target_matrices:
            app.abort(f'Environment `{env_name}` is not defined by project config')

    env_names = set(envs)

    matrix_columns: dict[str, dict[int, str]] = {
        'Name': {},
        'Type': {},
        'Envs': {},
        'Features': {},
        'Dependencies': {},
        'Environment variables': {},
        'Scripts': {},
        'Description': {},
    }
    matrix_envs = set()
    for i, (matrix_name, matrix_data) in enumerate(target_matrices.items()):
        matrix_envs.update(matrix_data['envs'])

        if env_names and matrix_name not in env_names:
            continue

        config = matrix_data['config']
        matrix_columns['Name'][i] = matrix_name
        matrix_columns['Type'][i] = config['type']
        matrix_columns['Envs'][i] = '\n'.join(matrix_data['envs'])

        if config.get('features'):
            if app.project.metadata.hatch.metadata.allow_ambiguous_features:
                matrix_columns['Features'][i] = '\n'.join(sorted(set(config['features'])))
            else:
                matrix_columns['Features'][i] = '\n'.join(
                    sorted({normalize_project_name(f) for f in config['features']})
                )

        dependencies = []
        if config.get('dependencies'):
            dependencies.extend(config['dependencies'])
        if config.get('extra-dependencies'):
            dependencies.extend(config['extra-dependencies'])
        if dependencies:
            normalized_dependencies = set()
            for dependency in dependencies:
                try:
                    req = Requirement(dependency)
                except InvalidRequirement:
                    normalized_dependencies.add(dependency)
                else:
                    normalized_dependencies.add(get_normalized_dependency(req))

            matrix_columns['Dependencies'][i] = '\n'.join(sorted(normalized_dependencies))

        if config.get('env-vars'):
            matrix_columns['Environment variables'][i] = '\n'.join(
                '='.join(item) for item in sorted(config['env-vars'].items())
            )

        if config.get('scripts'):
            matrix_columns['Scripts'][i] = '\n'.join(
                sorted(script for script in config['scripts'] if app.verbose or not script.startswith('_'))
            )

        if config.get('description'):
            matrix_columns['Description'][i] = config['description'].strip()

    standalone_columns: dict[str, dict[int, str]] = {
        'Name': {},
        'Type': {},
        'Features': {},
        'Dependencies': {},
        'Environment variables': {},
        'Scripts': {},
        'Description': {},
    }
    standalone_envs = (
        (env_name, config)
        for env_name, config in target_standalone_envs.items()
        if env_names or env_name not in matrix_envs
    )
    for i, (env_name, config) in enumerate(standalone_envs):
        if env_names and env_name not in env_names:
            continue

        environment = app.get_environment(env_name)

        standalone_columns['Name'][i] = env_name
        standalone_columns['Type'][i] = config['type']

        if environment.features:
            standalone_columns['Features'][i] = '\n'.join(environment.features)

        if environment.environment_dependencies_complex:
            standalone_columns['Dependencies'][i] = '\n'.join(
                sorted({get_normalized_dependency(d) for d in environment.environment_dependencies_complex})
            )

        env_vars = dict(environment.env_vars)
        env_vars.pop(AppEnvVars.ENV_ACTIVE)
        if env_vars:
            standalone_columns['Environment variables'][i] = '\n'.join(
                '='.join(item) for item in sorted(env_vars.items())
            )

        if environment.scripts:
            standalone_columns['Scripts'][i] = '\n'.join(
                sorted(script for script in environment.scripts if app.verbose or not script.startswith('_'))
            )

        if environment.description:
            standalone_columns['Description'][i] = environment.description.strip()

    column_options = {}
    for title in matrix_columns:
        if title != 'Description':
            column_options[title] = {'no_wrap': True}

    app.display_table(
        '' if hide_titles else 'Standalone',
        standalone_columns,
        show_lines=True,
        column_options=column_options,
        force_ascii=force_ascii,
    )
    app.display_table(
        '' if hide_titles else 'Matrices',
        matrix_columns,
        show_lines=True,
        column_options=column_options,
        force_ascii=force_ascii,
    )
