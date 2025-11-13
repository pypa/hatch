import sys
from pathlib import Path as PathlibPath

from hatch.publish.auth import AuthenticationCredentials
from hatch.utils.fs import Path


def test_pypirc(fs):
    # Get the project root directory (tests/utils/test_auth.py -> ../../src)
    # we have to do this because of the change from sys.settrace() to sys.monitoring in 3.14
    if sys.version_info >= (3, 14):
        project_root = PathlibPath(__file__).parent.parent.parent
        fs.add_real_directory(str(project_root / "src"), read_only=True)
        fs.add_real_directory(str(project_root / "tests"), read_only=True)

    fs.create_file(
        Path.home() / ".pypirc",
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
        app=None, cache_dir=Path("/none"), options={}, repo="", repo_config={"url": ""}
    )
    assert credentials.username == "guido"
    assert credentials.password == "sprscrt"

    credentials = AuthenticationCredentials(
        app=None,
        cache_dir=Path("/none"),
        options={},
        repo="other",
        repo_config={"url": ""},
    )
    assert credentials.username == "guido"
    assert credentials.password == "gat"

    credentials = AuthenticationCredentials(
        app=None,
        cache_dir=Path("/none"),
        options={},
        repo="arbitrary",
        repo_config={"url": "https://kaashandel.nl/"},
    )
    assert credentials.username == "guido"
    assert credentials.password == "gat"
