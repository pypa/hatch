from hatch.publish.auth import AuthenticationCredentials
from hatch.utils.fs import Path


def test_pypirc(tmp_path, mocker):
    # Create a fake home directory
    fake_home = tmp_path / "home"
    fake_home.mkdir()

    # Create .pypirc in the fake home
    pypirc = fake_home / ".pypirc"
    pypirc.write_text("""\
[other]
username: guido
password: gat
repository: https://kaashandel.nl/

[pypi]
username: guido
password: sprscrt
""")

    mocker.patch.object(Path, "home", return_value=fake_home)
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
