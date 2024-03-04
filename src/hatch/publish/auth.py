from __future__ import annotations

from hatch.utils.fs import Path


class AuthenticationCredentials:
    def __init__(
        self,
        app,
        cache_dir: Path,
        options: dict,
        repo: str,
        repo_config: dict[str, str],
    ):
        self._app = app
        self._pwu_path = cache_dir / 'previous_working_users.json'
        self._options = options
        self._repo = repo
        self._repo_config = repo_config

        self.__username: str | None = None
        self.__password: str | None = None
        self.__username_was_read = False
        self.__password_was_read = False
        self.__pwu_data: dict[str, str] = {}

    @property
    def password(self) -> str:
        if self.__password is None:
            self.__password = self.__get_password()
        return self.__password

    @property
    def username(self) -> str:
        if self.__username is None:
            self.__username = self.__get_username()
        return self.__username

    def __get_password(self) -> str:
        # this method doesn't consider .pypirc as the __password attribute would have
        # been set when it was looked up during username retrieval

        password = self._options.get('auth') or self._repo_config.get('auth')
        if password is not None:
            return password

        import keyring

        password = keyring.get_password(self._repo, self.username)
        if password is not None:
            return password

        if self._options['no_prompt']:
            self._app.abort('Missing required option: auth')

        self.__password_was_read = True
        return self._app.prompt('Password / Token', hide_input=True)

    def __get_username(self) -> str:
        username = (
            self._options.get('user')
            or self._repo_config.get('user')
            or self._read_pypirc()
            or self._read_previous_working_user_data()
        )
        if username is not None:
            return username

        if self._options['no_prompt']:
            self._app.abort('Missing required option: user')

        self.__username_was_read = True
        return self._app.prompt(f"Username for '{self._repo_config['url']}' [__token__]") or '__token__'

    def _read_previous_working_user_data(self) -> str | None:
        if self._pwu_path.is_file():
            contents = self._pwu_path.read_text()
            if contents:
                import json

                self.__pwu_data = json.loads(contents)
        return self.__pwu_data.get(self._repo)

    def _read_pypirc(self) -> str | None:
        import configparser

        pypirc = configparser.ConfigParser()
        pypirc.read(Path.home() / '.pypirc')
        repo = self._repo or 'pypi'

        if pypirc.has_section(repo):
            self.__password = pypirc.get(section=repo, option='password', fallback=None)
            return pypirc.get(section=repo, option='username', fallback=None)

        repo_url = self._repo_config['url']
        for section in pypirc.sections():
            if pypirc.get(section=section, option='repository', fallback=None) == repo_url:
                self.__password = pypirc.get(section=section, option='password', fallback=None)
                return pypirc.get(section=section, option='username', fallback=None)

        return None

    def write_updated_data(self):
        if self.__username_was_read:
            import json

            self.__pwu_data[self._repo] = self.__username
            self._pwu_path.ensure_parent_dir_exists()
            self._pwu_path.write_text(json.dumps(self.__pwu_data))

        if self.__password_was_read:
            import keyring

            keyring.set_password(self._repo, self.__username, self.__password)
