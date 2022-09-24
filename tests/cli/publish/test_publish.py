import os
import secrets
import tarfile
import zipfile
from collections import defaultdict

import pytest

from hatch.config.constants import PublishEnvVars

pytestmark = [pytest.mark.usefixtures('devpi')]


@pytest.fixture(autouse=True)
def local_builder(mock_backend_process, mocker):
    if mock_backend_process:
        mocker.patch('hatch.env.virtual.VirtualEnvironment.build_environment')

    yield


@pytest.fixture(autouse=True)
def keyring_store(mocker):
    mock_store = defaultdict(dict)
    mocker.patch('keyring.get_password', side_effect=lambda system, user: mock_store[system].get(user))
    mocker.patch(
        'keyring.set_password', side_effect=lambda system, user, auth: mock_store[system].__setitem__(user, auth)
    )
    yield mock_store


@pytest.fixture
def published_project_name():
    return f'c4880cdbe05de9a28415fbad{secrets.choice(range(100))}'


def remove_metadata_field(field: str, metadata_file_contents: str):
    lines = metadata_file_contents.splitlines(True)

    field_marker = f'{field}: '
    indices_to_remove = []

    for i, line in enumerate(lines):
        if line.lower().startswith(field_marker):
            indices_to_remove.append(i)

    for i, index in enumerate(indices_to_remove):
        del lines[index - i]

    return ''.join(lines)


def timestamp_to_version(timestamp):
    major, minor = str(timestamp).split('.')
    if minor.startswith('0'):
        normalized_minor = str(int(minor))
        padding = '.'.join('0' for _ in range(len(minor) - len(normalized_minor)))
        return f'{major}.{padding}.{normalized_minor}'
    else:
        return f'{major}.{minor}'


def test_timestamp_to_version():
    assert timestamp_to_version(123.4) == '123.4'
    assert timestamp_to_version(123.04) == '123.0.4'
    assert timestamp_to_version(123.004) == '123.0.0.4'


def test_explicit_options(hatch, temp_dir):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    with path.as_cwd():
        result = hatch('publish', '-o', 'foo=bar')

    assert result.exit_code == 1, result.output
    assert result.output == (
        'Use the standard CLI flags rather than passing explicit options when using the `index` plugin\n'
    )


def test_unknown_publisher(hatch, temp_dir):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    with path.as_cwd():
        result = hatch('publish', '-p', 'foo')

    assert result.exit_code == 1, result.output
    assert result.output == 'Unknown publisher: foo\n'


def test_disabled(hatch, temp_dir, config_file):
    config_file.model.publish['index']['disable'] = True
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    with path.as_cwd():
        result = hatch('publish', '-n')

    assert result.exit_code == 1, result.output
    assert result.output == 'Publisher is disabled: index\n'


def test_repo_invalid_type(hatch, temp_dir, config_file):
    config_file.model.publish['index']['repos'] = {'dev': 9000}
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    with path.as_cwd():
        result = hatch('publish', '--user', 'foo', '--auth', 'bar')

    assert result.exit_code == 1, result.output
    assert result.output == 'Hatch config field `publish.index.repos.dev` must be a string or a mapping\n'


def test_repo_missing_url(hatch, temp_dir, config_file):
    config_file.model.publish['index']['repos'] = {'dev': {}}
    config_file.save()

    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    with path.as_cwd():
        result = hatch('publish', '--user', 'foo', '--auth', 'bar')

    assert result.exit_code == 1, result.output
    assert result.output == 'Hatch config field `publish.index.repos.dev` must define a `url` key\n'


def test_missing_user(hatch, temp_dir):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    with path.as_cwd():
        result = hatch('publish', '-n')

    assert result.exit_code == 1, result.output
    assert result.output == 'Missing required option: user\n'


def test_missing_auth(hatch, temp_dir):
    project_name = 'My.App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    with path.as_cwd():
        result = hatch('publish', '-n', '--user', 'foo')

    assert result.exit_code == 1, result.output
    assert result.output == 'Missing required option: auth\n'


def test_flags(hatch, devpi, temp_dir_cache, helpers, published_project_name):
    with temp_dir_cache.as_cwd():
        result = hatch('new', published_project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir_cache / published_project_name

    with path.as_cwd():
        current_version = timestamp_to_version(helpers.get_current_timestamp())
        result = hatch('version', current_version)
        assert result.exit_code == 0, result.output

        result = hatch('build')
        assert result.exit_code == 0, result.output

        build_directory = path / 'dist'
        artifacts = list(build_directory.iterdir())

        result = hatch(
            'publish', '--repo', devpi.repo, '--user', devpi.user, '--auth', devpi.auth, '--ca-cert', devpi.ca_cert
        )

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        {artifacts[0].relative_to(path)} ... success
        {artifacts[1].relative_to(path)} ... success

        [{published_project_name}]
        {devpi.repo}{published_project_name}/{current_version}/
        """
    )


def test_plugin_config(hatch, devpi, temp_dir_cache, helpers, published_project_name, config_file):
    config_file.model.publish['index']['user'] = devpi.user
    config_file.model.publish['index']['auth'] = devpi.auth
    config_file.model.publish['index']['ca-cert'] = devpi.ca_cert
    config_file.model.publish['index']['repo'] = 'dev'
    config_file.model.publish['index']['repos'] = {'dev': devpi.repo}
    config_file.save()

    with temp_dir_cache.as_cwd():
        result = hatch('new', published_project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir_cache / published_project_name

    with path.as_cwd():
        del os.environ[PublishEnvVars.REPO]

        current_version = timestamp_to_version(helpers.get_current_timestamp())
        result = hatch('version', current_version)
        assert result.exit_code == 0, result.output

        result = hatch('build')
        assert result.exit_code == 0, result.output

        build_directory = path / 'dist'
        artifacts = list(build_directory.iterdir())

        result = hatch('publish')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        {artifacts[0].relative_to(path)} ... success
        {artifacts[1].relative_to(path)} ... success

        [{published_project_name}]
        {devpi.repo}{published_project_name}/{current_version}/
        """
    )


def test_plugin_config_repo_override(hatch, devpi, temp_dir_cache, helpers, published_project_name, config_file):
    config_file.model.publish['index']['user'] = 'foo'
    config_file.model.publish['index']['auth'] = 'bar'
    config_file.model.publish['index']['ca-cert'] = 'cert'
    config_file.model.publish['index']['repo'] = 'dev'
    config_file.model.publish['index']['repos'] = {
        'dev': {'url': devpi.repo, 'user': devpi.user, 'auth': devpi.auth, 'ca-cert': devpi.ca_cert},
    }
    config_file.save()

    with temp_dir_cache.as_cwd():
        result = hatch('new', published_project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir_cache / published_project_name

    with path.as_cwd():
        del os.environ[PublishEnvVars.REPO]

        current_version = timestamp_to_version(helpers.get_current_timestamp())
        result = hatch('version', current_version)
        assert result.exit_code == 0, result.output

        result = hatch('build')
        assert result.exit_code == 0, result.output

        build_directory = path / 'dist'
        artifacts = list(build_directory.iterdir())

        result = hatch('publish')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        {artifacts[0].relative_to(path)} ... success
        {artifacts[1].relative_to(path)} ... success

        [{published_project_name}]
        {devpi.repo}{published_project_name}/{current_version}/
        """
    )


def test_prompt(hatch, devpi, temp_dir_cache, helpers, published_project_name, config_file):
    config_file.model.publish['index']['ca-cert'] = devpi.ca_cert
    config_file.model.publish['index']['repo'] = 'dev'
    config_file.model.publish['index']['repos'] = {'dev': devpi.repo}
    config_file.save()

    with temp_dir_cache.as_cwd():
        result = hatch('new', published_project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir_cache / published_project_name

    with path.as_cwd():
        current_version = timestamp_to_version(helpers.get_current_timestamp())
        result = hatch('version', current_version)
        assert result.exit_code == 0, result.output

        result = hatch('build')
        assert result.exit_code == 0, result.output

        build_directory = path / 'dist'
        artifacts = list(build_directory.iterdir())

        result = hatch('publish', input=f'{devpi.user}\nfoo')

    assert result.exit_code == 1, result.output
    assert '401' in result.output
    assert 'Unauthorized' in result.output

    # Ensure nothing is saved for errors
    with path.as_cwd():
        result = hatch('publish', '-n')

    assert result.exit_code == 1, result.output
    assert result.output == 'Missing required option: user\n'

    # Trigger save
    with path.as_cwd():
        result = hatch('publish', str(artifacts[0]), input=f'{devpi.user}\n{devpi.auth}')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        Enter your username: {devpi.user}
        Enter your credentials:{' '}
        {artifacts[0].relative_to(path)} ... success

        [{published_project_name}]
        {devpi.repo}{published_project_name}/{current_version}/
        """
    )

    # Use saved results
    with path.as_cwd():
        result = hatch('publish', str(artifacts[1]))

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        {artifacts[1].relative_to(path)} ... success

        [{published_project_name}]
        {devpi.repo}{published_project_name}/{current_version}/
        """
    )


def test_initialize_auth(hatch, devpi, temp_dir_cache, helpers, published_project_name, config_file):
    config_file.model.publish['index']['ca-cert'] = devpi.ca_cert
    config_file.model.publish['index']['repo'] = 'dev'
    config_file.model.publish['index']['repos'] = {'dev': devpi.repo}
    config_file.save()

    with temp_dir_cache.as_cwd():
        result = hatch('new', published_project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir_cache / published_project_name

    # Trigger save
    with path.as_cwd():
        result = hatch('publish', '--initialize-auth', input=f'{devpi.user}\n{devpi.auth}')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        Enter your username: {devpi.user}
        Enter your credentials:{' '}
        """
    )

    with path.as_cwd():
        current_version = timestamp_to_version(helpers.get_current_timestamp())
        result = hatch('version', current_version)
        assert result.exit_code == 0, result.output

        result = hatch('build', '-t', 'wheel')
        assert result.exit_code == 0, result.output

        build_directory = path / 'dist'
        artifacts = list(build_directory.iterdir())

    # Use saved results
    with path.as_cwd():
        result = hatch('publish', str(artifacts[0]))

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        {artifacts[0].relative_to(path)} ... success

        [{published_project_name}]
        {devpi.repo}{published_project_name}/{current_version}/
        """
    )


def test_external_artifact_path(hatch, devpi, temp_dir_cache, helpers, published_project_name, config_file):
    config_file.model.publish['index']['ca-cert'] = devpi.ca_cert
    config_file.model.publish['index']['repo'] = 'dev'
    config_file.model.publish['index']['repos'] = {'dev': devpi.repo}
    config_file.save()

    with temp_dir_cache.as_cwd():
        result = hatch('new', published_project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir_cache / published_project_name
    external_build_directory = temp_dir_cache / 'dist'

    with path.as_cwd():
        current_version = timestamp_to_version(helpers.get_current_timestamp())
        result = hatch('version', current_version)
        assert result.exit_code == 0, result.output

        result = hatch('build', '-t', 'sdist', str(external_build_directory))
        assert result.exit_code == 0, result.output

        external_artifacts = list(external_build_directory.iterdir())

        result = hatch('build', '-t', 'wheel')
        assert result.exit_code == 0, result.output

        internal_build_directory = path / 'dist'
        internal_artifacts = list(internal_build_directory.iterdir())

        result = hatch('publish', '--user', devpi.user, '--auth', devpi.auth, 'dist', str(external_build_directory))

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        {internal_artifacts[0].relative_to(path)} ... success
        {external_artifacts[0]} ... success

        [{published_project_name}]
        {devpi.repo}{published_project_name}/{current_version}/
        """
    )


def test_already_exists(hatch, devpi, temp_dir_cache, helpers, published_project_name, config_file):
    config_file.model.publish['index']['ca-cert'] = devpi.ca_cert
    config_file.model.publish['index']['repo'] = 'dev'
    config_file.model.publish['index']['repos'] = {'dev': devpi.repo}
    config_file.save()

    with temp_dir_cache.as_cwd():
        result = hatch('new', published_project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir_cache / published_project_name

    with path.as_cwd():
        current_version = timestamp_to_version(helpers.get_current_timestamp())
        result = hatch('version', current_version)
        assert result.exit_code == 0, result.output

        result = hatch('build')
        assert result.exit_code == 0, result.output

        build_directory = path / 'dist'
        artifacts = list(build_directory.iterdir())

        result = hatch('publish', '--user', devpi.user, '--auth', devpi.auth)

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        {artifacts[0].relative_to(path)} ... success
        {artifacts[1].relative_to(path)} ... success

        [{published_project_name}]
        {devpi.repo}{published_project_name}/{current_version}/
        """
    )

    with path.as_cwd():
        result = hatch('publish', '--user', devpi.user, '--auth', devpi.auth)

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        {artifacts[0].relative_to(path)} ... already exists
        {artifacts[1].relative_to(path)} ... already exists
        """
    )


def test_no_artifacts(hatch, temp_dir_cache, helpers, published_project_name):
    with temp_dir_cache.as_cwd():
        result = hatch('new', published_project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir_cache / published_project_name

    with path.as_cwd():
        directory = path / 'dir2'
        directory.mkdir()
        (directory / 'test.txt').touch()

        result = hatch('publish', 'dir1', 'dir2', '--user', 'foo', '--auth', 'bar')

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        No artifacts found
        """
    )


def test_enable_with_flag(hatch, devpi, temp_dir_cache, helpers, published_project_name, config_file):
    config_file.model.publish['index']['user'] = devpi.user
    config_file.model.publish['index']['auth'] = devpi.auth
    config_file.model.publish['index']['ca-cert'] = devpi.ca_cert
    config_file.model.publish['index']['repo'] = 'dev'
    config_file.model.publish['index']['repos'] = {'dev': devpi.repo}
    config_file.model.publish['index']['disable'] = True
    config_file.save()

    with temp_dir_cache.as_cwd():
        result = hatch('new', published_project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir_cache / published_project_name

    with path.as_cwd():
        del os.environ[PublishEnvVars.REPO]

        current_version = timestamp_to_version(helpers.get_current_timestamp())
        result = hatch('version', current_version)
        assert result.exit_code == 0, result.output

        result = hatch('build')
        assert result.exit_code == 0, result.output

        build_directory = path / 'dist'
        artifacts = list(build_directory.iterdir())

        result = hatch('publish', '-y')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        {artifacts[0].relative_to(path)} ... success
        {artifacts[1].relative_to(path)} ... success

        [{published_project_name}]
        {devpi.repo}{published_project_name}/{current_version}/
        """
    )


def test_enable_with_prompt(hatch, devpi, temp_dir_cache, helpers, published_project_name, config_file):
    config_file.model.publish['index']['user'] = devpi.user
    config_file.model.publish['index']['auth'] = devpi.auth
    config_file.model.publish['index']['ca-cert'] = devpi.ca_cert
    config_file.model.publish['index']['repo'] = 'dev'
    config_file.model.publish['index']['repos'] = {'dev': devpi.repo}
    config_file.model.publish['index']['disable'] = True
    config_file.save()

    with temp_dir_cache.as_cwd():
        result = hatch('new', published_project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir_cache / published_project_name

    with path.as_cwd():
        del os.environ[PublishEnvVars.REPO]

        current_version = timestamp_to_version(helpers.get_current_timestamp())
        result = hatch('version', current_version)
        assert result.exit_code == 0, result.output

        result = hatch('build')
        assert result.exit_code == 0, result.output

        build_directory = path / 'dist'
        artifacts = list(build_directory.iterdir())

        result = hatch('publish', input='y\n')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        Confirm `index` publishing [y/N]: y
        {artifacts[0].relative_to(path)} ... success
        {artifacts[1].relative_to(path)} ... success

        [{published_project_name}]
        {devpi.repo}{published_project_name}/{current_version}/
        """
    )


class TestWheel:
    @pytest.mark.parametrize('field', ['name', 'version'])
    def test_missing_required_metadata_field(self, hatch, temp_dir_cache, helpers, published_project_name, field):
        with temp_dir_cache.as_cwd():
            result = hatch('new', published_project_name)
            assert result.exit_code == 0, result.output

        path = temp_dir_cache / published_project_name

        with path.as_cwd():
            current_version = timestamp_to_version(helpers.get_current_timestamp())
            result = hatch('version', current_version)
            assert result.exit_code == 0, result.output

            result = hatch('build', '-t', 'wheel')
            assert result.exit_code == 0, result.output

            build_directory = path / 'dist'
            artifacts = list(build_directory.iterdir())

        artifact_path = str(artifacts[0])
        metadata_file_path = f'{published_project_name}-{current_version}.dist-info/METADATA'

        with zipfile.ZipFile(artifact_path, 'r') as zip_archive:
            with zip_archive.open(metadata_file_path, 'r') as metadata_file:
                metadata_file_contents = metadata_file.read().decode('utf-8')

        with zipfile.ZipFile(artifact_path, 'w') as zip_archive:
            with zip_archive.open(metadata_file_path, 'w') as metadata_file:
                metadata_file.write(remove_metadata_field(field, metadata_file_contents).encode('utf-8'))

        with path.as_cwd():
            result = hatch('publish', '--user', 'foo', '--auth', 'bar')

        assert result.exit_code == 1, result.output
        assert result.output == helpers.dedent(
            f"""
            Missing required field `{field}` in artifact: {artifact_path}
            """
        )


class TestSourceDistribution:
    @pytest.mark.parametrize('field', ['name', 'version'])
    def test_missing_required_metadata_field(self, hatch, temp_dir_cache, helpers, published_project_name, field):
        with temp_dir_cache.as_cwd():
            result = hatch('new', published_project_name)
            assert result.exit_code == 0, result.output

        path = temp_dir_cache / published_project_name

        with path.as_cwd():
            current_version = timestamp_to_version(helpers.get_current_timestamp())
            result = hatch('version', current_version)
            assert result.exit_code == 0, result.output

            result = hatch('build', '-t', 'sdist')
            assert result.exit_code == 0, result.output

            build_directory = path / 'dist'
            artifacts = list(build_directory.iterdir())

        artifact_path = str(artifacts[0])
        extraction_directory = path / 'extraction'

        with tarfile.open(artifact_path, 'r:gz') as tar_archive:
            tar_archive.extractall(extraction_directory)

        metadata_file_path = extraction_directory / f'{published_project_name}-{current_version}' / 'PKG-INFO'
        metadata_file_path.write_text(remove_metadata_field(field, metadata_file_path.read_text()))

        with tarfile.open(artifact_path, 'w:gz') as tar_archive:
            tar_archive.add(extraction_directory, arcname='')

        with path.as_cwd():
            result = hatch('publish', '--user', 'foo', '--auth', 'bar')

        assert result.exit_code == 1, result.output
        assert result.output == helpers.dedent(
            f"""
            Missing required field `{field}` in artifact: {artifact_path}
            """
        )
