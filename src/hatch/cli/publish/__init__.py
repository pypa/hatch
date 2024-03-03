import click

from hatch.config.constants import PublishEnvVars


@click.command(short_help='Publish build artifacts')
@click.argument('artifacts', nargs=-1)
@click.option(
    '--repo',
    '-r',
    envvar=PublishEnvVars.REPO,
    help='The repository with which to publish artifacts [env var: `HATCH_INDEX_REPO`]',
)
@click.option(
    '--user', '-u', envvar=PublishEnvVars.USER, help='The user with which to authenticate [env var: `HATCH_INDEX_USER`]'
)
@click.option(
    '--auth',
    '-a',
    envvar=PublishEnvVars.AUTH,
    help='The credentials to use for authentication [env var: `HATCH_INDEX_AUTH`]',
)
@click.option(
    '--ca-cert',
    envvar=PublishEnvVars.CA_CERT,
    help='The path to a CA bundle [env var: `HATCH_INDEX_CA_CERT`]',
)
@click.option(
    '--client-cert',
    envvar=PublishEnvVars.CLIENT_CERT,
    help='The path to a client certificate, optionally containing the private key [env var: `HATCH_INDEX_CLIENT_CERT`]',
)
@click.option(
    '--client-key',
    envvar=PublishEnvVars.CLIENT_KEY,
    help="The path to the client certificate's private key [env var: `HATCH_INDEX_CLIENT_KEY`]",
)
@click.option('--no-prompt', '-n', is_flag=True, help='Disable prompts, such as for missing required fields')
@click.option(
    '--initialize-auth', is_flag=True, help='Save first-time authentication information even if nothing was published'
)
@click.option(
    '--publisher',
    '-p',
    'publisher_name',
    envvar=PublishEnvVars.PUBLISHER,
    default='index',
    help='The publisher plugin to use (default is `index`) [env var: `HATCH_PUBLISHER`]',
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
@click.option('--yes', '-y', is_flag=True, help='Confirm without prompting when the plugin is disabled')
@click.pass_obj
def publish(
    app,
    artifacts,
    repo,
    user,
    auth,
    ca_cert,
    client_cert,
    client_key,
    no_prompt,
    initialize_auth,
    publisher_name,
    options,
    yes,
):
    """Publish build artifacts."""
    option_map = {'no_prompt': no_prompt, 'initialize_auth': initialize_auth}
    if publisher_name == 'index':
        if options:
            app.abort('Use the standard CLI flags rather than passing explicit options when using the `index` plugin')

        if repo:
            option_map['repo'] = repo
        if user:
            option_map['user'] = user
        if auth:
            option_map['auth'] = auth
        if ca_cert:
            option_map['ca_cert'] = ca_cert
        if client_cert:
            option_map['client_cert'] = client_cert
        if client_key:
            option_map['client_key'] = client_key
    else:  # no cov
        for option in options:
            key, _, value = option.partition('=')
            option_map[key] = value

    publisher_class = app.plugins.publisher.get(publisher_name)
    if publisher_class is None:
        app.abort(f'Unknown publisher: {publisher_name}')

    publisher = publisher_class(
        app,
        app.project.location,
        app.cache_dir / 'publish' / publisher_name,
        app.project.config.publish.get(publisher_name, {}),
        app.config.publish.get(publisher_name, {}),
    )
    if publisher.disable and not (yes or (not no_prompt and app.confirm(f'Confirm `{publisher_name}` publishing'))):
        app.abort(f'Publisher is disabled: {publisher_name}')

    publisher.publish(list(artifacts), option_map)
