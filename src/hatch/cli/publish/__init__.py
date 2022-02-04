import click

from ...config.constants import PublishEnvVars


@click.command(short_help='Publish build artifacts')
@click.argument('artifacts', nargs=-1)
@click.option(
    '--user', '-u', envvar=PublishEnvVars.USER, help='The user with which to authenticate [env var: `HATCH_PYPI_USER`]'
)
@click.option(
    '--auth',
    '-a',
    envvar=PublishEnvVars.AUTH,
    help='The credentials to use for authentication [env var: `HATCH_PYPI_AUTH`]',
)
@click.option(
    '--repo',
    '-r',
    envvar=PublishEnvVars.REPO,
    help='The repository with which to publish artifacts [env var: `HATCH_PYPI_REPO`]',
)
@click.option('--no-prompt', '-n', is_flag=True, help='Do not prompt for missing required fields')
@click.option(
    '--publisher',
    '-p',
    'publisher_name',
    envvar=PublishEnvVars.PUBLISHER,
    default='pypi',
    help='The publisher plugin to use (default is `pypi`) [env var: `HATCH_PUBLISHER`]',
)
@click.option(
    '--option',
    '-o',
    'options',
    envvar=PublishEnvVars.OPTIONS,
    multiple=True,
    help=(
        'Options to pass to the publisher plugin. This may be selected multiple '
        'times e.g. `-o foo=bar -o baz=23` [env var: `HATCH_PUBLISHER_OPTIONS`]'
    ),
)
@click.pass_obj
def publish(app, artifacts, user, auth, repo, no_prompt, publisher_name, options):
    """Publish build artifacts."""
    option_map = {'no_prompt': no_prompt}
    if publisher_name == 'pypi':
        if options:
            app.abort('Use the standard CLI flags rather than passing explicit options when using the `pypi` plugin')

        if user:
            option_map['user'] = user
        if auth:
            option_map['auth'] = auth
        if repo:
            option_map['repo'] = repo
    else:  # no cov
        for option in options:
            key, _, value = option.partition('=')
            option_map[key] = value

    publisher_class = app.plugins.publisher.get(publisher_name)
    if publisher_class is None:
        app.abort(f'Unknown publisher: {publisher_name}')

    publisher = publisher_class(
        app.get_safe_application(),
        app.project.location,
        app.cache_dir / 'publish' / publisher_name,
        app.project.config.publish.get(publisher_name, {}),
        app.config.publish.get(publisher_name, {}),
    )
    publisher.publish(list(artifacts), option_map)
