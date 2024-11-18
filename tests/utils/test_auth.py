import pytest

import hatch.publish.auth
from hatch.publish.auth import AuthenticationCredentials
from hatch.utils.fs import Path


@pytest.fixture(autouse=True)
def mock_keyring(monkeypatch):
    class MockKeyring:
        @staticmethod
        def get_credential(*_):
            class Credential:
                username = 'gat'
                password = 'guido'

            return Credential()

    monkeypatch.setattr(hatch.publish.auth, 'keyring', MockKeyring)


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


def test_keyring_credentials():
    credentials = AuthenticationCredentials(
        app=None,
        cache_dir=Path('/none'),
        options={},
        repo='arbitrary',
        repo_config={'url': 'https://kaashandel.nl/'},
    )

    assert credentials.username == 'gat'
    assert credentials.password == 'guido'
