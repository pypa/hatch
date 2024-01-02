from hatch.publish.auth import AuthenticationCredentials
from hatch.utils.fs import Path


def test_pypirc(fs):
    fs.create_file(
        Path.home() / '.pypirc',
        contents="""\
            [other]
            username: guido
            password: gat
            repository: https://kaashandel.nl/

            [pypi]
            username: guido
            password: sprscrt
            """,
    )

    credentials = AuthenticationCredentials(
        app=None, cache_dir=Path('/none'), options={}, repo='', repo_config={'url': ''}
    )
    assert credentials.username == 'guido'
    assert credentials.password == 'sprscrt'

    credentials = AuthenticationCredentials(
        app=None,
        cache_dir=Path('/none'),
        options={},
        repo='other',
        repo_config={'url': ''},
    )
    assert credentials.username == 'guido'
    assert credentials.password == 'gat'

    credentials = AuthenticationCredentials(
        app=None,
        cache_dir=Path('/none'),
        options={},
        repo='arbritrary',
        repo_config={'url': 'https://kaashandel.nl/'},
    )
    assert credentials.username == 'guido'
    assert credentials.password == 'gat'
