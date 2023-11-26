import click


@click.command(short_help='Create or initialize a project')
@click.argument('name', required=False)
@click.argument('location', required=False)
@click.option('--interactive', '-i', 'interactive', is_flag=True, help='Interactively choose details about the project')
@click.option('--cli', 'feature_cli', is_flag=True, help='Give the project a command line interface')
@click.option('--init', 'initialize', is_flag=True, help='Initialize an existing project')
@click.option('-so', 'setuptools_options', multiple=True, hidden=True)
@click.pass_obj
def new(app, name, location, interactive, feature_cli, initialize, setuptools_options):
    """Create or initialize a project."""
    import sys
    from copy import deepcopy
    from datetime import datetime, timezone

    from hatch.config.model import TemplateConfig
    from hatch.project.core import Project
    from hatch.template import File
    from hatch.utils.fs import Path

    if location:
        location = Path(location).resolve()

    migration_possible = False
    if initialize:
        interactive = True
        location = location or Path.cwd()
        if (location / 'setup.py').is_file() or (location / 'setup.cfg').is_file():
            migration_possible = True
            if not name:
                name = 'temporary'

    if not name:
        if not interactive:
            app.abort('Missing required argument for the project name, use the -i/--interactive flag.')

        name = app.prompt('Project name')

    normalized_name = Project.canonicalize_name(name, strict=False)
    if not location:
        location = Path(normalized_name).resolve()

    needs_config_update = False
    if location.is_file():
        app.abort(f'Path `{location}` points to a file.')
    elif location.is_dir() and any(location.iterdir()):
        if not initialize:
            app.abort(f'Directory `{location}` is not empty.')

        needs_config_update = (location / 'pyproject.toml').is_file()

    if migration_possible:
        from hatch.cli.new.migrate import migrate
        from hatch.venv.core import TempVirtualEnv

        try:
            with app.status('Migrating project metadata from setuptools'), TempVirtualEnv(
                sys.executable, app.platform
            ) as venv:
                app.platform.run_command(['python', '-m', 'pip', 'install', '-q', 'setuptools'])
                migrate(str(location), setuptools_options, venv.sys_path)
        except Exception as e:  # noqa: BLE001
            app.display_error(f'Could not automatically migrate from setuptools: {e}')
            if name == 'temporary':
                name = app.prompt('Project name')
        else:
            return

    default_config = {
        'description': '',
        'dependencies': set(),
        'package_name': normalized_name.replace('-', '_'),
        'project_name': name,
        'project_name_normalized': normalized_name,
        'args': {'cli': feature_cli},
    }

    if interactive:
        default_config['description'] = app.prompt('Description', default='')

        app.display_info()

    if needs_config_update:
        app.project.initialize(str(location / 'pyproject.toml'), default_config)
        app.display_success('Updated: pyproject.toml')
        return

    template_config = deepcopy(app.config.template.raw_data)
    if 'plugins' in template_config and not template_config['plugins']:
        del template_config['plugins']

    TemplateConfig(template_config, ('template',)).parse_fields()

    plugin_config = template_config.pop('plugins')

    # Set up default config for template files
    template_config.update(default_config)

    template_classes = app.plugins.template.collect()

    templates = []
    for template_name, template_class in sorted(template_classes.items(), key=lambda item: -item[1].PRIORITY):
        if template_name in plugin_config:
            templates.append(
                template_class(plugin_config.pop(template_name), app.cache_dir, datetime.now(timezone.utc))
            )

    if not templates:
        app.abort(f'None of the defined plugins were found: {", ".join(sorted(plugin_config))}')
    elif plugin_config:
        app.abort(f'Some of the defined plugins were not found: {", ".join(sorted(plugin_config))}')

    for template in templates:
        template.initialize_config(template_config)

    template_files = []

    for template in templates:
        for possible_template_file in template.get_files(config=deepcopy(template_config)):
            template_file = (
                possible_template_file(deepcopy(template_config), template.plugin_config)
                if possible_template_file.__class__ is not File
                else possible_template_file
            )
            if template_file.path is None or (initialize and str(template_file.path) != 'pyproject.toml'):
                continue

            template_files.append(template_file)

    for template in templates:
        template.finalize_files(config=deepcopy(template_config), files=template_files)

    for template_file in template_files:
        template_file.write(location)

    if initialize:
        app.display_success('Wrote: pyproject.toml')
        return

    from rich.markup import escape
    from rich.tree import Tree

    def recurse_directory(directory, tree):
        paths = sorted(Path(directory).iterdir(), key=lambda p: (p.is_file(), p.name))
        for path in paths:
            if path.is_dir():
                recurse_directory(
                    path, tree.add(f'[bold magenta][link={app.platform.format_file_uri(path)}]{escape(path.name)}')
                )
            else:
                tree.add(f'[green][link={app.platform.format_file_uri(path)}]{escape(path.name)}')

    root = Tree(
        f'[bold magenta][link={app.platform.format_file_uri(location)}]{escape(location.name)}',
        guide_style='bright_blue',
        hide_root=location == Path.cwd(),
    )
    recurse_directory(location, root)
    app.output(root, markup=True)
