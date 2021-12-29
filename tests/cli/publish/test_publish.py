import os
import secrets
import tarfile
import time
import zipfile
from collections import defaultdict

import httpx
import pytest

from hatch.config.constants import PublishEnvVars
from hatch.utils.ci import running_in_ci

PUBLISHER_TOKEN = os.environ.get('HATCH_CI_PUBLISHER_TOKEN')

pytestmark = [
    pytest.mark.skipif(not PUBLISHER_TOKEN, reason='Publishing tests are only executed within CI environments'),
]


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


def wait_for_artifacts(project_name, *artifacts):
    index_url = f'https://test.pypi.org/simple/{project_name}/'
    artifact_names = [artifact.name for artifact in artifacts]

    for _ in range(120):
        try:
            response = httpx.get(index_url)
            response.raise_for_status()
        except Exception:  # no cov
            pass
        else:
            for artifact_name in artifact_names:
                if artifact_name not in response.text:
                    break
            else:
                break

        time.sleep(1)
    else:  # no cov
        raise Exception(f'Could not find artifacts at {index_url}: {", ".join(artifact_names)}')


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
    project_name = 'My App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    with path.as_cwd():
        result = hatch('publish', '-o', 'foo=bar')

    assert result.exit_code == 1, result.output
    assert result.output == (
        'Use the standard CLI flags rather than passing explicit options when using the `pypi` plugin\n'
    )


def test_unknown_publisher(hatch, temp_dir):
    project_name = 'My App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    with path.as_cwd():
        result = hatch('publish', '-p', 'foo')

    assert result.exit_code == 1, result.output
    assert result.output == 'Unknown publisher: foo\n'


def test_missing_user(hatch, temp_dir):
    project_name = 'My App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    with path.as_cwd():
        result = hatch('publish', '-n')

    assert result.exit_code == 1, result.output
    assert result.output == 'Missing required option: user\n'


def test_missing_auth(hatch, temp_dir):
    project_name = 'My App'

    with temp_dir.as_cwd():
        result = hatch('new', project_name)
        assert result.exit_code == 0, result.output

    path = temp_dir / 'my-app'

    with path.as_cwd():
        result = hatch('publish', '-n', '--user', 'foo')

    assert result.exit_code == 1, result.output
    assert result.output == 'Missing required option: auth\n'


def test_flags(hatch, temp_dir_cache, helpers, published_project_name):
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
            'publish', '--user', '__token__', '--auth', PUBLISHER_TOKEN, '--repo', 'https://test.pypi.org/legacy/'
        )

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        {artifacts[0].relative_to(path)} ... success
        {artifacts[1].relative_to(path)} ... success

        [{published_project_name}]
        https://test.pypi.org/project/{published_project_name}/{current_version}/
        """
    )


def test_plugin_config(hatch, temp_dir_cache, helpers, published_project_name, config_file):
    config_file.model.publish['pypi']['user'] = '__token__'
    config_file.model.publish['pypi']['auth'] = PUBLISHER_TOKEN
    config_file.model.publish['pypi']['repo'] = 'test'
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
        https://test.pypi.org/project/{published_project_name}/{current_version}/
        """
    )


def test_prompt(hatch, temp_dir_cache, helpers, published_project_name):
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

        result = hatch('publish', input='__token__\nfoo')

    assert result.exit_code == 1, result.output
    assert '403' in result.output
    assert 'Invalid or non-existent authentication information' in result.output

    # Ensure nothing is saved for errors
    with path.as_cwd():
        result = hatch('publish', '-n')

    assert result.exit_code == 1, result.output
    assert result.output == 'Missing required option: user\n'

    # Trigger save
    with path.as_cwd():
        result = hatch('publish', str(artifacts[0]), input=f'__token__\n{PUBLISHER_TOKEN}')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        Enter your username: __token__
        Enter your credentials:{' '}
        {artifacts[0].relative_to(path)} ... success

        [{published_project_name}]
        https://test.pypi.org/project/{published_project_name}/{current_version}/
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
        https://test.pypi.org/project/{published_project_name}/{current_version}/
        """
    )


def test_external_artifact_path(hatch, temp_dir_cache, helpers, published_project_name):
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

        result = hatch(
            'publish', '--user', '__token__', '--auth', PUBLISHER_TOKEN, 'dist', str(external_build_directory)
        )

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        {internal_artifacts[0].relative_to(path)} ... success
        {external_artifacts[0]} ... success

        [{published_project_name}]
        https://test.pypi.org/project/{published_project_name}/{current_version}/
        """
    )


def test_already_exists(hatch, temp_dir_cache, helpers, published_project_name):
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

        result = hatch('publish', '--user', '__token__', '--auth', PUBLISHER_TOKEN)

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        {artifacts[0].relative_to(path)} ... success
        {artifacts[1].relative_to(path)} ... success

        [{published_project_name}]
        https://test.pypi.org/project/{published_project_name}/{current_version}/
        """
    )

    for _ in range(30 if running_in_ci() else 5):
        wait_for_artifacts(published_project_name, *artifacts)
        time.sleep(1)

    with path.as_cwd():
        result = hatch('publish', '--user', '__token__', '--auth', PUBLISHER_TOKEN)

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

        result = hatch('publish', 'dir1', 'dir2', '--user', '__token__', '--auth', 'foo')

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        No artifacts found
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
            result = hatch('publish', '--user', '__token__', '--auth', 'foo')

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
            tar_archive.add(extraction_directory)

        with path.as_cwd():
            result = hatch('publish', '--user', '__token__', '--auth', 'foo')

        assert result.exit_code == 1, result.output
        assert result.output == helpers.dedent(
            f"""
            Missing required field `{field}` in artifact: {artifact_path}
            """
        )
